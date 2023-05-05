"""This module deals with the db (file name - cars.db)."""
import sqlite3 as sq


class CarDB:
    def __init__(self):
        self.cars = sq.connect('cars.db')
        self.cur = None

    def _create_table(self):
        """This function creates the table if it doesn't exist."""
        self.cur = self.cars.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS cars(
                            id INTEGER PRIMARY KEY,
                            car_name TEXT,
                            car_type TEXT,
                            year INTEGER,
                            price INTEGER,
                            url TEXT
                        )""")

    def add_car(self, params: tuple):
        """This function receives the data and inserts them into the db."""
        self._create_table()
        self.cur = self.cars.cursor()
        self.cur.execute("INSERT INTO cars VALUES (NULL, ?, ?, ?, ?, ?)", params)
        self.cars.commit()

    def search_car(self, category: str, value: str | tuple) -> list:
        """This function receives the category and the value it should look for and returns the found result.
        If it gets value as a tuple it will look for the column in a range."""
        self.cars = sq.connect('cars.db')
        self.cur = self.cars.cursor()
        if isinstance(value, str):
            cursor = self.cur.execute(f"select * from cars where LOWER({category}) like LOWER('%{value.title()}%')")
        else:
            cursor = self.cur.execute(f"select * from cars where {category} between {value[0]} and {value[1]}")

        row = cursor.fetchall()
        self.cars.close()
        return row
