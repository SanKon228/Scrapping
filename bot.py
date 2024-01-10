from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputMediaPhoto
import aiohttp
import random
import sqlite3 
from bs4 import BeautifulSoup
import json
import asyncio
import io

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

API_TOKEN = '5302355669:AAFwboWIlaCWqG-Xhg12Q2ntCCsMk3OCvH8'  # Replace with your bot token

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

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(check_and_send_new_cars())
    executor.start_polling(dp, skip_updates=True)
