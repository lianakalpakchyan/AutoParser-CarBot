"""This is the parser module. It collects all cars' data and inserts them into the db."""
from selenium import webdriver
from bs4 import BeautifulSoup
from car_db import CarDB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AutoParser:
    def __init__(self, url: str):
        self.url = url
        self.driver = webdriver.Chrome()
        self.time = 20
        self.last_page = self._find_last_page()
        self.each_car_link = 'https://auto.am'  # this url is used to create the url for each car by adding the car ID
        self.car_db = CarDB()

    def _find_last_page(self) -> int:
        """This function finds the total number of available pages"""
        self.driver.implicitly_wait(self.time)
        self.driver.get(self.url)
        page = BeautifulSoup(self.driver.page_source, 'lxml')
        fl = page.find(class_='fl')
        return int(fl.text) if fl else 0

    @staticmethod
    def _get_car_name(card: BeautifulSoup) -> str | None:
        """This function looks for the car name if found returns it otherwise None."""
        car_name = card.find(class_='card-title')
        return car_name.text.split()[1].strip() if car_name else None

    @staticmethod
    def _get_car_type(card: BeautifulSoup) -> str | None:
        """This function looks for the car type if found returns it otherwise None."""
        car_type = card.find(class_='card-title')
        return car_type.text.split()[2].strip() if car_type else None

    @staticmethod
    def _get_car_year(card: BeautifulSoup) -> int | None:
        """This function looks for the car year if found returns it otherwise None."""
        car_year = card.find('span', class_='grey-text')
        return int(car_year.text.strip()) if car_year else None

    @staticmethod
    def _get_car_price(card: BeautifulSoup) -> str | int | None:
        """This function looks for the car price if found returns it otherwise None."""
        car_price = card.find(class_='price')
        if car_price:
            if '$' in car_price.text:
                return int(car_price.text.strip().replace(' ', '').replace('$', ''))
            return 'Պայմանագրային'

        return None

    def _get_car_url(self, card: BeautifulSoup) -> str:
        """This function creates url for each car adding its id."""
        car_url = card.find('a')
        return self.each_car_link + car_url.get('href').strip() if car_url else None

    def _get_data(self, card: BeautifulSoup) -> tuple:
        """This functions calls all data gathering functions and returns all of them together."""
        car_name = AutoParser._get_car_name(card)
        car_type = AutoParser._get_car_type(card)
        car_year = AutoParser._get_car_year(card)
        car_price = AutoParser._get_car_price(card)
        car_url = self._get_car_url(card)
        return car_name, car_type, car_year, car_price, car_url

    def _get_next_page(self: webdriver):
        """This generator returns the next page every time it's called until it reaches the total number of pages."""
        page_number = 1
        while page_number <= self.last_page:
            self.driver.get(self.url + '?q={"category":"1","page":"' + str(page_number) +
                            '","sort":"latest","layout":"list","user":{"dealer":"0","official":"0","id":""},'
                            '"year":{"gt":"1911","lt":"2024"},"usdprice":{"gt":"0","lt":"100000000"},"mileage":'
                            '{"gt":"10","lt":"1000000"}}')
            wait = WebDriverWait(self.driver, self.time)
            wait.until(EC.presence_of_element_located((By.ID, "search-result")))
            yield self.driver
            page_number += 1

    def _add_car_to_db(self, params: tuple):
        """This function receives all data of a car and inserts them into the db."""
        self.car_db.add_car(params)

    def start_parsing(self):
        """This functions creates a soup for every page parses them and adds to the db."""
        for driver in self._get_next_page():
            page = BeautifulSoup(driver.page_source, 'lxml')
            results = page.find('div', {'id': 'search-result'})
            cards = results.find_all(class_='card')
            for card in cards:
                params = self._get_data(card)
                self._add_car_to_db(params)

        self.driver.quit()
