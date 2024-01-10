import sqlite3
import requests
from bs4 import BeautifulSoup

def parse_car_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        brand = 'Example Brand'  
        price = 'Example Price'  
        link = url
        photo = 'https://cdn0.riastatic.com/photosnew/auto/photo/bmw_m8-gran-coupe__531681460f.webp'

        return brand, price, link, photo
    else:
        print(f"Failed to fetch the webpage: {url}")
        return None

def insert_new_car(db_path, car_details):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO cars (brand, price, auto_ria_link, photos)
            VALUES (?, ?, ?, ?)
        ''', car_details)

        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

car_page_url = 'https://auto.ria.com/uk/auto_skoda_superb_scout_35777152.html'

car_details = parse_car_page(car_page_url)

database_path = 'database.sqlite3'

if car_details:
    insert_new_car(database_path, car_details)
