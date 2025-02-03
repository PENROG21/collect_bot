import telebot


# вводим токен бота
asd = "5929718382:AAFZXsV2YldpqY7KCW4bbwyorLwfWHZiIo0"
bot = telebot.TeleBot(asd)


user_data = {}

# Добавление данных о пользователе
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Приветствую вас на телеграмм боте collect.')

    markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
    item1 = telebot.types.KeyboardButton("Создать таблицу")
    markup.add(item1)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


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

    bot.send_message(message.chat.id, f"Таблица создана!\nНазвание: {table_name}\nОписание: {table_description}")

    # Сбрасываем состояние
    user_data.pop(message.chat.id, None)


# Запуск бота
bot.polling(none_stop=True)