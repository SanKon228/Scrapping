import requests
from bs4 import BeautifulSoup
import sqlite3

def get_car_info():
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
            'abroad.not': '0',
            'damage.not': "0",
            'brand.id[0]': "79",
            'model.id[0]': "2104",
            'country.import.usa.not': '0',
            'page': page
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
                    
                    cursor.execute("SELECT COUNT(1) FROM cars WHERE auto_ria_link = ?", (link,))
                    if cursor.fetchone()[0] == 0:  
                        cursor.execute('''
                        INSERT INTO cars (brand, price, auto_ria_link, photos)
                        VALUES (?, ?, ?, ?)
                        ''', (brand, price, link, photo_url))
                        conn.commit()

        else:
            print('Failed to fetch data:', response.status_code)

        page += 1

    conn.close()