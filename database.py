import sqlite3
from bcrypt import checkpw, hashpw, gensalt


agencies = {
    "hutoryandek": "Хутор Яндык",
    "tour_agency1": "ТурАгенство1"
}


class Database:
    def __init__(self):
        self.connection = sqlite3.connect("database.db")

    def create_tables(self):
        self.connection.execute("""
        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title varchar(255),
            start_time varchar(255),
            duration varchar(255),
            route varchar(255),
            tags varchar(255),
            url varchar(255),
            tour_agency varchar(255),
            photo varchar(255)
        )
        """)

        self.connection.execute("""
        CREATE TABLE IF NOT EXISTS tour_agencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title varchar(255),
            url varchar(255),
            contacts varchar(255),
            about_us varchar(1000)
        )
        """)

    def add_tour(self, title, start_time, duration, route, tags, tour_agency, photo, agency_id):
        self.connection.execute(f"""
        INSERT INTO tours (title, start_time, duration, route, tags, tour_agency, photo, agency_id)
        VALUES ({", ".join((f"'{parameter}'" for parameter in (title, start_time, duration, route, tags, tour_agency, photo, agency_id)))})
        """)
        self.connection.commit()
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM tours ORDER BY 0 - id LIMIT 1")
        result = cursor.fetchone()[0]
        return result

    def add_description(self, tour_id, description, program):
        self.connection.execute(f"""
        INSERT INTO tour_descriptions (tour_id, description, program)
        VALUES ('{tour_id}', '{description}', '{program}')
        """)

    def get_all_tours(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM tours")
        res = cursor.fetchall()[::-1]
        cursor.close()
        return res

    def get_all_tours_agency(self, agency_id):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM tours WHERE agency_id = '{agency_id}'")
        res = cursor.fetchall()[::-1]
        cursor.close()
        return res

    def get_description_tour(self, tour_id):
        cursor = self.connection.cursor()
        cursor.execute(f"""
        SELECT * FROM tour_descriptions
        WHERE tour_id = '{tour_id}'
        """)
        res_tour = cursor.fetchone()
        cursor.close()
        return res_tour

    def photos_update_agency(self, agency_id, photos):
        photos = photos[::-1]

        self.connection.execute(f"""
                UPDATE tour_agencies
                SET photo = '{', '.join(photos)}' 
                WHERE id = '{agency_id}'
                """)

        self.connection.commit()

    def photos_update(self, tour_id, photos):
        photos = photos[::-1]

        self.connection.execute(f"""
                UPDATE tours
                SET photo = '{photos[0]}'
                WHERE id = '{tour_id}'
                """)

        self.connection.execute(f"""
                UPDATE tour_descriptions
                SET photo = '{', '.join(photos)}' 
                WHERE tour_id = '{tour_id}'
                """)

        self.connection.commit()

    def edit_tour(self, tour_id, title, start_time, duration, route, tags, description):
        self.connection.execute(f"""
        UPDATE tours
        SET title = '{title}', start_time = '{start_time}',
        duration = '{duration}', route = '{route}', tags = '{tags}' 
        WHERE id = '{tour_id}'
        """)

        self.connection.execute(f"""
        UPDATE tour_descriptions
        SET description = '{description}' 
        WHERE tour_id = '{tour_id}'
        """)

        self.connection.commit()

    def get_tour_by_id(self, tour_id):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM tours WHERE id = '{tour_id}'")
        res = cursor.fetchone()
        cursor.close()
        return res

    def add_request(self, tour_id, name, phone, email):
        cursor = self.connection.cursor()
        cursor.execute(f"""
        SELECT agency_id FROM tours WHERE id = '{tour_id}'
        """)
        agency_id = cursor.fetchone()[0]
        cursor.close()

        self.connection.execute(f"""
                INSERT INTO tour_requests (tour_id, agency_id, name, mail, phone)
                VALUES ("{tour_id}", "{agency_id}", "{name}", "{email}", "{phone}")
                """)
        self.connection.commit()

    def edit_agency(self, title, url, contacts, about_us, id):
        self.connection.execute(f"""
                UPDATE tour_agencies
                SET title = '{title}', url = '{url}',
                contacts = '{contacts}', about_us = '{about_us}'
                WHERE id = {id}
                """)

        self.connection.commit()

    def get_tour_agency(self, agency_id):
        cursor = self.connection.cursor()
        cursor.execute(f"""
                SELECT * FROM tour_agencies WHERE id = '{agency_id}'
                """)
        tour_agency = cursor.fetchone()
        cursor.close()
        return tour_agency

    def login_user(self, email, password):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT tour_agency_id, hash_password FROM accounts WHERE email = '{email}'")
        res = cursor.fetchone()
        hashed_password = res[1].encode("utf-8")
        tour_agency_id = res[0]
        cursor.close()
        return tour_agency_id if (password.encode("utf-8"), hashed_password) else False

    def register_user(self, tour_agency_id, email, password):
        hash_password = hashpw(password.encode("utf-8"), gensalt(4)).decode("utf-8")
        self.connection.execute(f"""
        INSERT INTO accounts (tour_agency_id, email, hash_password) VALUES ('{tour_agency_id}', '{email}', '{hash_password}')
""")
        self.connection.commit()

    def get_agency_by_id(self, id):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT title FROM tour_agencies WHERE id = '{id}'")
        res = cursor.fetchone()[0]
        cursor.close()
        return res