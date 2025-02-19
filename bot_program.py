from typing import List

import telebot
from telebot import types

from data_base import PostgresConnection


# вводим токен бота
bot = telebot.TeleBot("5929718382:AAFZXsV2YldpqY7KCW4bbwyorLwfWHZiIo0")

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
    item3 = telebot.types.KeyboardButton("Посмотреть мои таблицы")
    item4 = telebot.types.KeyboardButton("Посмотреть где я записан")

    # Проверяем есть ли пользователь в общей базе данных.
    if not db.exist_user(message.from_user.id):
        markup.add(item1)
        markup.add(item2)
    else:
        markup.add(item1, item2)
        markup.add(item3, item4)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Посмотреть мои таблицы")
def view_my_tables_handler(message):
    # Здесь будет логика отображения таблиц, созданных пользователем
    owen_table = db.search_owen_table(message.from_user.id)
    if not owen_table:
        bot.send_message(message.chat.id, "У вас не таблиц")
    else:
        bot.send_message(message.chat.id, print_table(owen_table))


@bot.message_handler(func=lambda message: message.text == "Посмотреть где я записан")
def view_my_registrations_handler(message):
    owen_participants = db.get_table_info_for_user(message.from_user.id)
    if not owen_participants:
        bot.send_message(message.chat.id, "У вас не таблиц")
    else:
        bot.send_message(message.chat.id, print_table(owen_participants))


def print_table(id_tables: list[int]):
    try:
            results = []
            for table_id in id_tables:
                # Из id таблиц получаем информацию об них
                info_table = db.get_info_table(table_id)

                name = info_table[0]
                description = info_table[1]

                results.append(f'id: /{table_id}\n'
                               f'Название {name}\n Описание '
                               f'{description}\n')
            return '\n'.join(results)  # Возвращаем все строки

    except Exception as e:
        print(e)


@bot.message_handler(func=lambda message: message.text.startswith('/') and message.text[1:].isdigit())
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
            bot.send_message(message.chat.id, print_table(table_id), reply_markup=markup)

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


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Доступные команды:\n"
                     "/start - начать работу с ботом\n"
                     "/help - показать список команд\n"
                     "/info - получить информацию")


@bot.message_handler(func=lambda message: message.text == "Записаться в таблицу")
def handle_create_table(message):
    bot.send_message(message.chat.id, "Введите id таблицы куда хотите записаться:")
    bot.register_next_step_handler(message, lambda message: handle_table_link(message))


@bot.message_handler(func=lambda message: message.text == "Создать таблицу")
def handle_create_table(message):
    try:
        # Устанавливаем состояние "ожидание названия таблицы"
        user_data[message.chat.id] = {"state": "waiting_for_table_name"}

        markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
        item1 = telebot.types.KeyboardButton("Отмена")
        markup.add(item1)

        bot.send_message(message.chat.id, "Введите название таблицы:", reply_markup=markup)
    except Exception as error:
        print("Ошибка при работе с функцией handle_table_description\n", error)


@bot.message_handler(
    func=lambda message: user_data.get(message.chat.id, {}).get("state") == "waiting_for_table_name")
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

        markup = types.InlineKeyboardMarkup()
        settings_button = types.InlineKeyboardButton("Настройки", callback_data="show_settings")
        show = types.InlineKeyboardButton("Показать содержимое", callback_data="show_settings")
        markup.add(settings_button)
        markup.add(show)

        # Создаём таблицу
        id_table = db.create_table(table_name, table_description, id_owner=message.from_user.id)
        user_data[message.chat.id]["id_table"] = id_table

        # Выводим информацию об таблице
        bot.send_message(message.chat.id, f"Таблица создана!"
                                          f"\n ID таблицы {id_table}"
                                          f"\nНазвание: {table_name}"
                                          f"\nОписание: {table_description}", reply_markup=markup)

        # Не удаляем user_data, чтобы использовать его в show_settings
        # user_data.pop(message.chat.id, None)  # Уберите эту строку
    except Exception as error:
        print("Ошибка при работе с функцией handle_table_description\n", error)


@bot.message_handler(commands=['show'])
def show_participants(message):
    try:
        try:
            table_id = int(str(message.text)[6:])  # [6:] вместо [5:], т.к. /show
            print(table_id)
        except (ValueError, IndexError):
            bot.reply_to(message, "Неверный формат команды. Используйте /show <id_таблицы>")
            return

        user_id = message.from_user.id
        if not db.exist_user(user_id):
            bot.reply_to(message, "Вас нет в базе данных")
        else:
            if not db.exists_table(table_id):
                bot.reply_to(message, "Нет такой таблицы")
            else:
                if not db.check_record_exists(table_id, user_id):
                    bot.reply_to(message, "Вы не владелец.")
                else:
                    if not db.visibility(table_id):
                        bot.reply_to(message, "Вы не можете просмотреть таблицу.\nНедостаточно прав")
                    else:
                        list_participants = db.show_all_participants_table(table_id)
                        print(list_participants)
                        if not list_participants:
                            bot.reply_to(message, "Таблица пуста.")
                        else:
                            info = []
                            number = 1
                            for i in list_participants:
                                info.append(f'{number}) user_name:{i[1]}, Имя:{i[2]}, username:{i[1]}')
                                number += 1
                            bot.reply_to(message, f'Таблица {db.name_table(id_table=table_id)}\n Участники: \n'
                                                  f'{'\n'.join(info)}')

    except Exception as error:
        print("Ошибка при работе с функцией handle_table_description\n", error)


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

        markup = types.InlineKeyboardMarkup()
        settings_button = types.InlineKeyboardButton("Настройки", callback_data="show_settings")
        show = types.InlineKeyboardButton("Показать содержимое", callback_data="show_settings")
        markup.add(settings_button)
        markup.add(show)

        # Создаём таблицу
        id_table = db.create_table(table_name, table_description, id_owner=message.from_user.id)
        user_data[message.chat.id]["id_table"] = id_table

        # Выводим информацию об таблице
        bot.send_message(message.chat.id, f"Таблица создана!"
                                          f"\n ID таблицы {id_table}"
                                          f"\nНазвание: {table_name}"
                                          f"\nОписание: {table_description}", reply_markup=markup)

    except Exception as error:
        print("Ошибка при работе с функцией handle_table_description\n", error)


@bot.callback_query_handler(func=lambda call: call.data == "show_settings")
def show_settings(call):
    try:
        chat_id = call.message.chat.id

        id_table = user_data[chat_id]["id_table"]
        print(id_table)
        # Создаем 6 кнопок настроек
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Уведомления ❌", callback_data="setting_1")
        button2 = types.InlineKeyboardButton("Visibility", callback_data=f"setting_2_{id_table}")
        button3 = types.InlineKeyboardButton("Настройка 3", callback_data="setting_3")
        markup.add(button1, button2)
        markup.add(button3)

        # Изменяем сообщение, заменяя кнопку "Настройки" на 6 кнопок
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Выберите настройку\nVisibility  - Участники могу смотреть содержимое таблицы.:",
                              reply_markup=markup)
    except Exception as error:
        print(error)
        print("Ошибка при работе с функцией show_settings\n", error)


@bot.callback_query_handler(func=lambda call: call.data.startswith("setting_"))
def handle_setting(call):
    try:
        setting_number = int(call.data.split("_")[1])  # Извлекаем номер настройки
        data_for_setting_number = call.data.split("_")[2]  # Получаем данные для работы

        # Получаем название таблицы.
        name_table = db.name_table(data_for_setting_number)
        match setting_number:
            case 1:
                bot.answer_callback_query(call.id, "Вы теперь будете получать уведомление об том, что кто - то "
                                                   f"записался в таблицу {name_table}")
            case 2:
                # Меняем базу данных
                if not db.change_show_participants(data_for_setting_number):
                    bot.send_message(call.id, "Ошибка")
                else:
                    if db.visibility(id_table=data_for_setting_number):
                        bot.answer_callback_query(call.id, f"Теперь участники таблицы "
                                                           f"{name_table} "
                                                           f"могу смотреть содержимое")
                    else:
                        bot.answer_callback_query(call.id, f"Теперь участники таблицы "
                                                           f"{name_table} "
                                                           f"не смогут смотреть содержимое")
            case _:
                bot.answer_callback_query(call.id, f"Ошибка")
            # Отображаем уведомление вверху
        bot.answer_callback_query(call.id, f"Вы выбрали настройку {setting_number}")
    except Exception as error:
        print(error)
        print("Ошибка при работе с функцией show_settings\n", error)


# Обработчик всех сообщений, начинающихся с "/" и не соответствующих известным командам.
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def unknown_command(message):
    bot.reply_to(message, "Неизвестная команда. Попробуйте /help")


# Запуск бота
bot.polling(none_stop=True)