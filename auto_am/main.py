"""This is the main module where everything starts."""
from parser import AutoParser
from auto_am_bot import CarBot
import os


def main(url: str):
    """This function starts parsing if db file doesn't exist and then activates the car bot."""
    if not os.path.isfile('cars.db'):
        auto = AutoParser(url)
        auto.start_parsing()

    car_bot = CarBot()
    car_bot.start()


if __name__ == '__main__':
    URL = 'https://auto.am/search/passenger-cars'
    main(URL)
