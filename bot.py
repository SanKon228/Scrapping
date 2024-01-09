from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from aiogram.types import InputFile
import aiohttp

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

MAX_MESSAGE_LENGTH = 4096

async def create_cars_messages(cars):
    messages = []
    current_message = ""
    for car in cars:
        brand, price, link, photos = car[1], car[2], car[3], car[4]
        car_message = f"Brand: {brand}\nPrice: {price}\nLink: {link}\nPhotos: {photos}\n\n"
        
        if len(current_message) + len(car_message) > MAX_MESSAGE_LENGTH:
            messages.append(current_message)
            current_message = car_message
        else:
            current_message += car_message
            
    if current_message:
        messages.append(current_message)
        
    return messages

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    cars = await get_all_cars()
    
    for car in cars:
        brand, price, link, photos_url = car[1], car[2], car[3], car[4]
        car_message = f"Brand: {brand}\nPrice: {price}\nLink: {link}\n"
        
        if photos_url:
            photo_bytes = await download_photo(photos_url)
            if photo_bytes:
                await bot.send_photo(message.from_user.id, photo_bytes, caption=car_message)
            else:
                await bot.send_message(message.from_user.id, "Неможливо завантажити фото.")
        else:
            await bot.send_message(message.from_user.id, car_message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


