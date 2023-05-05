"""This module starts bot activations and loads the .env file to get the bot token."""
import os
from dotenv import load_dotenv
from telebot import TeleBot, types
from car_db import CarDB
import re

load_dotenv()


class CarBot:
    def __init__(self):
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        self.bot = TeleBot(self.BOT_TOKEN)
        self.car_db = CarDB()
        self.start_count = 0
        self.amount = 10

        @self.bot.message_handler(commands=['start'])
        def show_categories(message):
            """This function greets the user and guides"""
            self.bot.send_message(message.chat.id, f"Welcome to auto bot. Type /find to search for a car."
                                                   f"\nWhen you search for some car first it will show the first "
                                                   f"{self.amount} results. To get the next {self.amount} use command "
                                                   f"/next")

        @self.bot.message_handler(commands=['find'])
        def show_categories(message):
            """This function creates the buttons for showing the options.
            Once the option is chosen it starts searching in db."""
            self.start_count = 0
            markup = types.ReplyKeyboardMarkup(row_width=2)
            btn1 = types.KeyboardButton('year')
            btn2 = types.KeyboardButton('car name')
            btn3 = types.KeyboardButton('car type')
            btn4 = types.KeyboardButton('price')
            markup.add(btn1, btn2, btn3, btn4)
            sent_msg = self.bot.send_message(message.chat.id, "Choose one category:", reply_markup=markup)
            self.bot.register_next_step_handler(sent_msg, self._search_in_db)

    def start(self):
        """This functions activates the bot it starts waiting for actions from a user."""
        self.bot.infinity_polling()

    def _ask_range(self, message, category: str):
        """If user chose an option which requires range for searching this functions is called to ask for it."""
        sent_msg = self.bot.send_message(message.chat.id, f'Specify range for {category.title()} in this format'
                                                          f'\nmin{category.title()}-max{category.title()}'
                                                          f'(for example 1111-2222)')
        self.bot.register_next_step_handler(sent_msg, self._search_by_range, category)

    def _search_in_db(self, message):
        """This function controls which type of searching should be occurred either by range or by value."""
        if message.text.lower() in ['year', 'price']:
            self._ask_range(message, message.text.lower())
        else:
            sent_msg = self.bot.send_message(message.chat.id, f'Specify the {message.text.title()}!')
            self.bot.register_next_step_handler(sent_msg, self._search_by_value, message.text)

    def _car_text(self, car):
        """This function creates the final text for every car that will be sent to a user."""
        text = f"Car: {car[1]} {car[2]}"
        if isinstance(car[4], int):
            text += f"\nPrice ${int(car[4]):,}"
        else:
            text += f"\nPrice {car[4]}"

        text += f"\nYear: {car[3]}\nURL: {car[5]}"

        return text

    def _next_cars(self, message, cars):
        f"""This generator returns {self.amount} cars every time it's called."""
        if len(cars) > self.amount:
            while self.start_count + self.amount < len(cars):
                for i in range(self.start_count, self.start_count + self.amount):
                    car = cars[i]
                    text = self._car_text(car)
                    self.bot.reply_to(message, text)

                self.start_count += self.amount
                yield self.start_count
            else:
                if self.start_count - self.amount < len(cars):
                    for i in range(self.start_count, len(cars)):
                        text = self._car_text(cars[i])
                        self.bot.reply_to(message, text)
                    raise StopIteration
        else:
            for car in cars:
                text = self._car_text(car)
                self.bot.reply_to(message, text)
            raise StopIteration

    def _next_with_exceptions(self, message, cars):
        """This function tries to get the limited amount of cars.
        First it returns itself and then waits for /next command."""
        try:
            next(self._next_cars(message, cars))
        except StopIteration:
            self.bot.reply_to(message, 'Data are over!')
            self.start_count = 0
        except RuntimeError:
            self.bot.reply_to(message, 'Data are over!')
            self.start_count = 0

    def _represent_data(self, message, cars: list):
        """This functions receives data from db and represents them to the user."""
        if cars:
            self._next_with_exceptions(message, cars)

            @self.bot.message_handler(commands=['next'])
            def show_categories(inner_message):
                self._next_with_exceptions(inner_message, cars)
        else:
            self.bot.reply_to(message, "NO DATA")

    def _search_by_value(self, message, value: str):
        """This function searches for cars in db by value."""
        category = value.strip().lower().replace(' ', '_')
        value = message.text.strip().lower()
        cars = self.car_db.search_car(category, value)
        self._represent_data(message, cars)

    def _search_by_range(self, message, category: str):
        """This function searches for cars in db by range.
        If the format of the range is not valid it informs the user."""
        value_range = message.text.strip()
        if re.match(r'\d+-\d+', message.text.strip()):
            min_limit, max_limit = value_range.split('-')
            cars = self.car_db.search_car(category, (min_limit, max_limit))
            self._represent_data(message, cars)
        else:
            self.bot.reply_to(message, 'Invalid format!')
