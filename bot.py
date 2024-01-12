from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputMediaPhoto
import aiohttp
import random
import sqlite3 
from bs4 import BeautifulSoup
import json
import asyncio
import requests
import io

async def get_car_info(user_id):
    page = 0
    page_empty = False

    conn = sqlite3.connect('database.sqlite3')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        price TEXT,
        auto_ria_link TEXT UNIQUE, 
        photos TEXT
    );
    ''')
    conn.commit()

    while not page_empty:
        response = requests.get(f'https://auto.ria.com/uk/search/', params={
            'indexName': 'auto,order_auto,newauto_search',
            'categories.main.id': "1",
            'price.currency': "1",
            'custom.not': "-1",
            'abroad.not': '0',
            'damage.not': "0",
            'brand.id[0]': "79",
            'model.id[0]': "2104",
            'country.import.usa.not': '0',
            'page': page,
            'size': 100
        })

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('div', class_='content-bar')
            if len(listings) == 0:
                page_empty = True
            else:
                for car_info in listings:
                    link = car_info.find('a', class_='m-link-ticket')['href']
                    photo_url = car_info.find('img')['src']
                    brand = car_info.find('span', class_='blue bold').get_text()
                    price = car_info.find('div', class_='price-ticket').get_text(strip=True)
                    
                    cursor.execute("SELECT id, price FROM cars WHERE auto_ria_link = ?", (link,))
                    car = cursor.fetchone()
                    if car is None:
                        cursor.execute('''
                        INSERT INTO cars (brand, price, auto_ria_link, photos)
                        VALUES (?, ?, ?, ?)
                        ''', (brand, price, link, photo_url))
                    else:
                        car_id, old_price = car
                        if old_price != price:
                            await bot.send_message(user_id, f"Ціна на автомобіль {brand} змінилась з {old_price} на {price}.")
                            cursor.execute('''
                            UPDATE cars SET price = ? WHERE id = ?
                            ''', (price, car_id))
                    conn.commit()
        else:
            print('Failed to fetch data:', response.status_code)

        page += 1

    conn.close()

async def parse_car_photos(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                images = soup.find_all("img", class_="outline m-auto")
                image_urls = [img['src'] for img in images if 'src' in img.attrs]
                random_photo_urls = random.sample(image_urls, min(len(image_urls), 5))
                return random_photo_urls
            else:
                return None

async def download_photo(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                return None

API_TOKEN = '5302355669:AAFwboWIlaCWqG-Xhg12Q2ntCCsMk3OCvH8'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def get_all_cars():
    conn = sqlite3.connect('database.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cars")
    cars = cursor.fetchall()
    conn.close()
    return cars

async def check_and_send_new_cars():
    while True:
        await asyncio.sleep(100)
        user_data = load_user_data()
        cars = await get_all_cars()
        num_cars_in_db = len(cars)

        for user_id, num_cars_seen in user_data.items():
            if num_cars_in_db > num_cars_seen:
                new_cars = cars[num_cars_seen:]
                for car in new_cars:
                    photo_urls = await parse_car_photos(car[3])
                    
                    if photo_urls:
                        media = [InputMediaPhoto(io.BytesIO(await download_photo(url))) for url in photo_urls]
                        await bot.send_media_group(int(user_id), media)
                    else:
                        await bot.send_message(int(user_id), "Фотографії недоступні.")
                    
                    await send_car_info(int(user_id), car)
                
                update_user_data(user_id, num_cars_in_db)

def load_user_data():
    try:
        with open('user_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_user_data(user_data):
    with open('user_data.json', 'w') as file:
        json.dump(user_data, file)

def update_user_data(user_id, num_cars_seen):
    user_data = load_user_data()
    user_data[str(user_id)] = num_cars_seen
    save_user_data(user_data)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    cars = await get_all_cars()
    update_user_data(user_id, len(cars))
    for car in cars:
        await send_car_info(user_id, car)

async def send_car_info(user_id, car):
    brand, price, link, photos_url = car[1], car[2], car[3], car[4]
    car_message = f"Brand: {brand}\nPrice: {price}\nLink: {link}\n"

    if photos_url:
        photo_bytes = await download_photo(photos_url)
        if photo_bytes:
            await bot.send_photo(user_id, photo_bytes, caption=car_message)
        else:
            await bot.send_message(user_id, car_message + "\n[Фото недоступне]")
    else:
        await bot.send_message(user_id, car_message)

def get_registered_user_ids():
    try:
        with open('user_data.json', 'r') as file:
            user_data = json.load(file)
            return list(user_data.keys())
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

async def periodic_car_info_update():
    user_ids = get_registered_user_ids()
    while True:
        for user_id in user_ids:
            await get_car_info(user_id)
        await asyncio.sleep(60)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_car_info_update())
    loop.create_task(check_and_send_new_cars())
    executor.start_polling(dp, skip_updates=True)
