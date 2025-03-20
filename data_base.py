from typing import List, Optional, Union
import inspect

import psycopg2


class PostgresConnection:
    """Класс для работы с PostgreSQL."""

    def __init__(self, database, password, host="localhost", user="postgres", port=5432 ):
        """Инициализация подключения к PostgreSQL."""
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None

    def __str__(self):
        # Mask the password for security
        return (f"PostgreSQLConnection(\n"
                f"host='{self.host}', "
                f"\ndatabase='{self.database}', "
                f"\nuser='{self.user}', "
                f"\nport={self.port})")

    def __repr__(self):
        """Возвращает формальное строковое представление объекта."""
        return (
            f"PostgresConnection(host={self.host!r}, "
            f"database={self.database!r}, user={self.user!r}, "
            f"port={self.port!r})"
        )

    def __del__(self):
        """Закрывает соединение при удалении объекта."""
        if self.connection:
            self.close()

    def __getattr__(self, name):
        """Обрабатывает попытку доступа к несуществующему атрибуту."""
        raise AttributeError(f"Атрибут '{name}' не найден")

    def __setattr__(self, name, value):
        """Обрабатывает попытку установки атрибута."""
        super().__setattr__(name, value)

    def commit(self):
        """Сохранение изменений в базе данных."""
        try:
            self.connection.commit()
            print("Изменения сохранены.")
        except psycopg2.Error as e:
            print(f"Ошибка сохранения изменений: {e}")

    def connect(self):
        """Создание подключения к PostgreSQL."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.cursor = self.connection.cursor()

            print("Соединение с PostgreSQL установлено успешно.")
        except psycopg2.Error as e:
            print(f"Ошибка подключения: {e}")

    def close(self):
        """Закрытие подключения к PostgreSQL."""
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Соединение с PostgreSQL закрыто.")

    def get_info_table(self, id_table: int):
        try:
            self.cursor.execute(
                f'SELECT name, discription FROM "table" WHERE id = {id_table}'
            )
            table_info = self.cursor.fetchone()

            if table_info:
                return table_info[0], table_info[1]
            else:
                return None, None

        except Exception as error:
            print("Ошибка при работе с методом get_info_table", error)
            return None, None

    def name_table(self, id_table) -> str:
        """
        Метод, который возвращает название таблицы
        :param id_table: Id таблицы
        :return: Название таблицы. (str)
        """
        try:
            self.cursor.execute(
                f'select name from "table" where id = {id_table}'
            )
            return str(self.cursor.fetchone())

        except psycopg2.Error as e:
            print(f"Ошибка в name_table (SQL): {e}")
            return 'None'

        except Exception as e:
            print(f"Ошибка в name_table: {e}")
            return 'None'

    def records_user(self, user_id, user_name: str, user_surname: str, username: str, id_platform: int):
        """
        Метод для, добавление пользователя в базу данных.
        :param user_id: id пользователя из платформа
        :param user_name:
        :param user_surname:
        :param username:
        :param id_platform: Платформа
        """
        try:
            self.cursor.execute(
                "INSERT INTO users(id_user, user_name, username, platform, data, user_surname)"
                                f" values ({user_id}, %s, %s, {id_platform}, now(), %s)",
                                (user_name, username, user_surname)
            )
            self.commit()
        except Exception as error:
            print("Ошибка при работе с методом records_user\n", error)

    def exist_user(self, user_id_platform: str) -> bool:
        """
        Метод, для проверки наличия пользователя в базе данных
        :param user_id_platform: id пользователя из платформы
        :return: True если есть
        """
        try:
            self.cursor.execute(
                f"SELECT * FROM users WHERE id_user = {user_id_platform}"
            )
            return bool(self.cursor.fetchone())

        except Exception as error:
            print("Ошибка при работе с методом exist_user\n", error)

    def create_table(self, name: str, description: str, id_owner: int) -> str:
        """
        Метод для, создание таблицы
        :param name: Название таблицы
        :param description: Описание таблицы
        :param id_owner: Id создателя и владельца
        :return:
        """
        try:
            self.cursor.execute(
                'INSERT INTO "table"(name, discription, owner, data_creat) VALUES '
                f"(%s, %s, (SELECT id FROM users WHERE id_user = {id_owner}), NOW()) RETURNING id",
                                (name, description)
            )
            self.commit()

            return self.cursor.fetchone()[0]
        except Exception as error:
            print("Ошибка при работе с методом create_table\n", error)

    def records_table(self, id_table: int, id_user: int) -> bool:
        """
        Пытается добавить запись в таблицу 'records'.  Возвращает True при успешном добавлении,
        False, если запись уже существует (нарушение уникальности), и печатает сообщение об ошибке
        в случае других исключений.
        """
        try:
            self.cursor.execute(
                f'insert into records(id_table, id_name, "data") '
                f'values ({id_table}, (select id from users where id_user = {id_user} ), now())'
            )
            self.connection.commit()  # Важно: нужно зафиксировать изменения в базе данных
            return True  # Успешно добавлено
        except psycopg2.errors.UniqueViolation as e:
            self.connection.rollback()  # Откатываем транзакцию при ошибке уникальности
            return False  # Запись уже существует
        except Exception as error:
            self.connection.rollback()  # Откатываем транзакцию при любой другой ошибке
            print("Ошибка при добавлении записи в таблицу 'records':\n", error)
            return False  # Произошла другая ошибка

    def search_owen_table(self, owner_id: int) -> List[int]:
        """
        Получает список ID таблиц, принадлежащих пользователю.

        Args:
            owner_id: ID пользователя-владельца.

        Returns:
            Список ID таблиц, принадлежащих пользователю.
            Возвращает пустой список, если пользователь не владеет ни одной таблицей
            или если произошла ошибка.
        """
        sql_query = """
            SELECT 
                id
            FROM 
                "table"
            WHERE 
                "owner" = (SELECT id FROM users WHERE id_user = %s)
        """
        try:
            self.cursor.execute(sql_query, (owner_id,))  # Параметризованный запрос
            table_ids = [row[0] for row in self.cursor.fetchall()]  # Преобразуем результат в список ID
            return table_ids
        except psycopg2.Error as pg_error:
            print(f"Ошибка PostgreSQL в {inspect.currentframe().f_code.co_name}: {pg_error}")
            return []  # Возвращаем пустой список в случае ошибки
        except Exception as generic_error:
            print(f"Общая ошибка в {inspect.currentframe().f_code.co_name}: {generic_error}")
            return []

    def exists_table(self, id_table) -> bool:
        """
        Метод дял проверки существования таблицы.
        :param id_table: Id таблицы которое надо проверить
        :return: True если есть и наоборот.
        """
        try:
            # Используем параметризованный запрос для защиты от SQL-инъекций
            self.cursor.execute(
                f"SELECT EXISTS (SELECT 1 FROM records "
                f"WHERE id_table = {id_table}) AS exists;"
            )
            result = self.cursor.fetchone()[0]  # Получаем первый элемент из результата (True или False)

            return bool(result)  # Явно преобразуем в bool

        except psycopg2.Error as error:
            print("Ошибка при работе с методом exists_table в sql\n", error)

        except Exception as error:
            print("Ошибка при работе с методом exists_table\n", error)

    def show_all_participants_table(self, id_table) -> list :
        """
        Метод, который возврощаяет участников таблиц
        Метод, которая возвращаяет участников таблицы
        :id_table id_table: Id таблицы которое надо проверить
        :return: True если есть и наоборот.
        """
        try:
            # Используем параметризованный запрос для защиты от SQL-инъекций
            self.cursor.execute(
                "select users.user_name, users.user_surname, users.username from users "
                "inner join records "
                f"on records.id_table = {id_table}"
            )
            return [self.cursor.fetchone()]  # Получаем первый элемент из результата (True или False)

        except psycopg2.Error as error:
            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name} в sql\n", error)

        except Exception as error:
            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name}\n", error)

    def check_user_in_table(self, id_table: int, id_user: int) -> bool:
        """
        Проверяет, записан ли пользователь с указанным ID в таблицу с указанным ID.

        Args:
            table_id: ID таблицы.
            user_id: ID пользователя.

        Returns:
            True, если пользователь записан в таблицу, иначе False.  Возвращает False при любой ошибке.
        """
        try:
            # Используем параметризованный запрос для защиты от SQL-инъекций
            self.cursor.execute("select id from records r where id_table = %s and id_name "
                                "= get_id_user(%s)", (id_table, id_user)
            )
            # Получаем первый элемент из результата (True или False)
            result = self.cursor.fetchone()
            # Если результат None, возвращаем False
            if result is None:
                return False
            # Преобразуем первый элемент результата в bool
            return bool(result[0])

        except psycopg2.Error as error:
            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name} в sql\n", error)
            return False

        except Exception as error:
            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name}\n", error)
            return False

    def is_user_owner(self, table_id, owner_id):
        """
        Быстро проверяет что пользователь, владелrец таблицы
        Возвращает True, если запись существует, иначе False.
        """
        try:
            self.cursor.execute(
                'SELECT 1 FROM "table" WHERE id = %s AND owner = '
                '(select id from users where "id_user" = %s) LIMIT 1',
                (table_id, owner_id)
            )
            return bool(self.cursor.fetchone())  # True, если запись найдена, иначе False

        except psycopg2.Error as e:
            print(f"Ошибка в check_record_exists (SQL): {e}")
            return False  # Возвращаем False в случае ошибки

        except Exception as e:
            print(f"Ошибка в check_record_exists: {e}")
            return False  # Возвращаем False в случае другой ошибки

    def change_show_participants(self, id_table: int) -> bool:
        """
        Метод, который позволяет участникам таблицы просматривать запись в таблице.
        :param id_table: ID таблицы
        :return: True если все успешно прошло и наоборт.
        """
        try:
            self.cursor.execute(f'''
            UPDATE "table" SET show_participants = NOT show_participants where "id" = {id_table};
            '''
            )
            self.commit()
            return True

        except psycopg2.Error as error:

            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name} в sql\n", error)
        except Exception as error:

            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name}\n", error)

    def get_table_info_for_user(self, id_table: int) -> Optional[List[int]]:
        """
        Метод, который возвращает id таблиц где пользователь принимает участие.
        :param id_table:
        :return:
        """
        try:
            self.cursor.execute('select "table".id from "table" inner join records ON '
                                '"table".id = records.id_table inner join users on users.id = records.id_name ' 
                                f'where users.id = (select id from users u2 where id_user = {id_table})'
                                )
            rows = self.cursor.fetchall()

            return [row[0] for row in rows] if rows else []

        except psycopg2.Error as error:

            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name} в sql\n", error)
        except Exception as error:

            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name}\n", error)

    def visibility(self, id_table) -> type[bool, str]:
        """
        Метод, который проверяет, могут - ли участник просматривать таблицу
        :param id_table: id таблицы
        :return: True если могут и наоборот.
        """
        try:
            # Используем параметризованный запрос для защиты от SQL-инъекций
            self.cursor.execute(
                f'select show_participants from "table" where id = {id_table}'
            )
            show_participants = self.cursor.fetchone()[0]
            return bool(show_participants)  # Получаем первый элемент из результата (True или False)

        except psycopg2.Error as error:
            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name} в sql\n", error)

        except Exception as error:
            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name}\n", error)

    def delete_user_from_table(self, id_table, id_users) -> bool:
        try:
            # Используем параметризованный запрос для защиты от SQL-инъекций
            self.cursor.execute(
                'delete from records where id_name = get_id_user(%s) and id_table = %s',
                (id_users, id_table)
            )
            self.connection.commit()
            return True  # Получаем первый элемент из результата (True или False)

        except psycopg2.Error as error:
            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name} в sql\n", error)
            return False

        except Exception as error:
            print(f"Ошибка при работе с методом {inspect.currentframe().f_code.co_name}\n", error)
            return False


if __name__ == "__main__":
    db = PostgresConnection(
            database="telebot",
            password="PENROG21"
    )
    db.connect()
    db.exist_user('3')
    print(db.visibility(1))
