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

    def get_info_table(self, id_table):
        try:
            self.cursor.execute(f'SELECT name, discription FROM "table" WHERE id = {id_table}')
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
            self.cursor.execute("INSERT INTO users(id_user, user_name, username, platform, data, user_surname)"
                                f" values ({user_id}, %s, %s, {id_platform}, now(), %s)",
                                (user_name, username, user_surname))
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
            self.cursor.execute(f"SELECT * FROM users WHERE id_user = {user_id_platform}")
            if self.cursor.fetchone():
                return True
            else:
                return False
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
            self.cursor.execute('INSERT INTO "table"(name, discription, owner, data_creat) VALUES '
                                    f"(%s, %s, (SELECT id FROM users WHERE id_user = {id_owner}), NOW()) RETURNING id",
                                (name, description))
            self.commit()

            return self.cursor.fetchone()[0]
        except Exception as error:
            print("Ошибка при работе с методом create_table\n", error)

    def close(self):
        """Закрытие подключения к PostgreSQL."""
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Соединение с PostgreSQL закрыто.")


if __name__ == "__main__":
    pass