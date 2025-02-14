import psycopg2


class PostgresConnection:
    """Класс для работы с PostgreSQL."""

    def __init__(self, database, password, host="localhost", user="postgres", port=5432):
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

    def get_info_table(self, id_table):
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

    def search_owen_table(self, id_owen: int) -> list:
        """
        Метод для поиска таблиц, которыми владеет пользователь.
        :param id_owen: id пользователя
        :return: id, название и описание таблиц. (если есть)
        """
        try:
            self.cursor.execute(
                'select id, "name", discription from "table" where "table"."owner" = '
                f'(select id from users where id_user = {id_owen})'
            )
            return self.cursor.fetchall()  # Возвращаем все строки

        except Exception as error:
            print("Ошибка при работе с методом search_owen_table\n", error)

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

    def all_participants_table(self, id_table):
        """
        Метод дял проверки существования таблицы.
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
            return self.cursor.fetchone()  # Получаем первый элемент из результата (True или False)

        except psycopg2.Error as error:
            print("Ошибка при работе с методом all_participants_table в sql\n", error)

        except Exception as error:
            print("Ошибка при работе с методом all_participants_table\n", error)


if __name__ == "__main__":
    db = PostgresConnection(
        database="telebot",
        password="PENROG21"
    )
    db.connect()
    print(db.all_participants_table(1))