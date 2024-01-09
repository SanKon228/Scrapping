import schedule
import time
from scrapping import get_car_info

def work():
    print("Running...")
    get_car_info()

schedule.every(10).minutes.do(work)

while True:
    schedule.run_pending()
    time.sleep(1)
