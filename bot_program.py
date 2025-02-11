import telebot

from data_base import PostgresConnection


# вводим токен бота
asd = "5929718382:AAFZXsV2YldpqY7KCW4bbwyorLwfWHZiIo0"
bot = telebot.TeleBot(asd)

db = PostgresConnection(
    database="telebot",
    password="PENROG21"
)
db.connect()
user_data = {}


# Добавление данных о пользователе
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Приветствую вас на телеграмм боте collect.')

    markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
    item1 = telebot.types.KeyboardButton("Создать таблицу")
    item2 = telebot.types.KeyboardButton("Записаться в таблицу")
    markup.add(item1)
    markup.add(item2)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_table_link(message):
    try:
        table_id = message.text[1:]
        print(table_id)
        table_name, table_description = db.get_info_table(table_id)

        if table_name:
            markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            item1 = telebot.types.KeyboardButton("Отмена")
            item2 = telebot.types.KeyboardButton("Записаться")
            markup.add(item1, item2)
            markup.add(item1)
            markup.add(item2)

            response = f"Вы перешли по ссылке на таблицу с ID: {table_id}\n"
            response += f"Название таблицы: {table_name or 'Нет названия'}\n"
            response += f"Описание таблицы: {table_description or 'Нет описания'}\n"
            bot.send_message(message.chat.id, response, reply_markup=markup)

            bot.register_next_step_handler(message, lambda message:
            records_table(message, table_id))
        else:
            bot.reply_to(message, f"Таблица с ID {table_id} не найдена.")

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")


def records_table(message, id_table):
    try:
        if message.text.strip() == "Записаться":
            if db.records_table(id_table, id_user=message.from_user.id):
                bot.send_message(message.chat.id, "Вы записались в таблицу")
            else:
                bot.send_message(message.chat.id, "Вы уже есть в таблице")
        if message.text.strip() == "Отмена":
            send_welcome(message)
    except Exception as error:
        print(error)


@bot.message_handler(func=lambda message: message.text == "Записаться в таблицу")
def handle_create_table(message):
    bot.send_message(message.chat.id, "Введите id таблицы куда хотите записаться:")
    bot.register_next_step_handler(message, lambda message: handle_table_link(message))


@bot.message_handler(func=lambda message: message.text == "Создать таблицу")
def handle_create_table(message):
    # Устанавливаем состояние "ожидание названия таблицы"
    user_data[message.chat.id] = {"state": "waiting_for_table_name"}

    markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
    item1 = telebot.types.KeyboardButton("Отмена")
    markup.add(item1)

    bot.send_message(message.chat.id, "Введите название таблицы:", reply_markup=markup)


@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("state") == "waiting_for_table_name")
def handle_table_name(message):
    if message.text == "Отмена":
        # Сбрасываем состояние и возвращаемся к началу
        user_data.pop(message.chat.id, None)
        send_welcome(message)
        return

    # Сохраняем название таблицы
    user_data[message.chat.id]["table_name"] = message.text
    user_data[message.chat.id]["state"] = "waiting_for_table_description"

    markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
    item1 = telebot.types.KeyboardButton("Отмена")
    markup.add(item1)

    bot.send_message(message.chat.id, "Введите описание таблицы:", reply_markup=markup)


@bot.message_handler(
    func=lambda message: user_data.get(message.chat.id, {}).get("state") == "waiting_for_table_description")
def handle_table_description(message):
    try:
        if message.text == "Отмена":
            # Сбрасываем состояние и возвращаемся к началу
            user_data.pop(message.chat.id, None)
            send_welcome(message)
            return

        # Сохраняем описание таблицы
        user_data[message.chat.id]["table_description"] = message.text

        # Выводим собранные данные
        table_name = user_data[message.chat.id]["table_name"]
        table_description = user_data[message.chat.id]["table_description"]

        # Записываем пользователя если нет.
        if not db.exist_user(message.from_user.id):
            db.records_user(id_platform=1, user_id=message.from_user.id, username=message.from_user.username,
                            user_name=message.from_user.first_name, user_surname=message.from_user.last_name)

        # Создаём таблицу
        id_table = db.create_table(table_name, table_description, id_owner=message.from_user.id)
        # Выводим информацию об таблице
        bot.send_message(message.chat.id, f"Таблица создана!"
                                          f"\n ID таблицы {id_table}"
                                          f"\nНазвание: {table_name}"
                                          f"\nОписание: {table_description}")

        # Сбрасываем состояние
        user_data.pop(message.chat.id, None)
    except Exception as error:
        print("Ошибка при работе с функцией handle_table_description\n", error)


# Запуск бота
bot.polling(none_stop=True)