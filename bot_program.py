from typing import List, Union
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
        bot.send_message(message.chat.id, "У вас нет таблиц")
    else:
        bot.send_message(message.chat.id, print_table(owen_table))


@bot.message_handler(func=lambda message: message.text == "Посмотреть где я записан")
def view_my_registrations_handler(message):
    owen_participants = db.get_table_info_for_user(message.from_user.id)
    if not owen_participants:
        bot.send_message(message.chat.id, "Вы пока нигде не записаны.")
    else:
        bot.send_message(message.chat.id, print_table(owen_participants))


def print_table(id_tables: Union[int, List[int]]):
    try:
            if isinstance(id_tables, int):
                id_tables = [id_tables]
            results = []
            for table_id in id_tables:
                # Из id таблиц получаем информацию об них
                info_table = db.get_info_table(table_id)

                name = info_table[0]
                description = info_table[1]

                results.append(f'id: /{table_id}\n'
                               f'Название Таблицы {name}\nОписание '
                               f'{description}\n')
            return '\n'.join(results)  # Возвращаем все строки
    except Exception as e:
        print(e)


@bot.message_handler(func=lambda message: message.text.startswith('/') and message.text[1:].isdigit())
def handle_table_link(message):
    try:
        table_id = int(message.text[1:])
        print(table_id)
        table_name, table_description = db.get_info_table(table_id)

        if table_name:
            markup = types.InlineKeyboardMarkup()
            messeage_send = []
            print(message.from_user.id, "222")

            if db.check_user_in_table(table_id, message.from_user.id):
                item1 = types.InlineKeyboardButton("Отписаться", callback_data=f"unsubscribe:{table_id}")

                messeage_send.append('Вы записаны в таблицу. Вы можете отписаться')
            else:
                item1 = types.InlineKeyboardButton("Записаться", callback_data=f"subscribe:{table_id}")

                messeage_send.append('Вы не записаны в таблицу.')

            markup.add(item1)  # Добавляем кнопку в разметку

            messeage_send.append(print_table(table_id))

            # Отправляем сообщение с кнопками
            bot.send_message(message.chat.id, '\n'.join(messeage_send), reply_markup=markup)

        else:
            bot.reply_to(message, f"Таблица с ID {table_id} не найдена.")

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    """Обработчик нажатий на инлайн-кнопки"""
    try:
        if call.message: # Проверяем, что сообщение существует
            data = call.data.split(":")
            action = data[0]
            table_id = int(data[1])
            print(table_id)
            print(call.from_user.id)

            if action == "unsubscribe":
                # Отписываем пользователя от таблицы
                if db.delete_user_from_table(table_id, call.from_user.id):
                    bot.send_message(call.message.chat.id, f"Вы успешно отписались от таблицы с ID {table_id}")
                else:
                    bot.send_message(call.message.chat.id, f"Не удалось отписаться от таблицы с ID {table_id}")

                # Обновляем сообщение, чтобы отобразить кнопку "Записаться"
                markup = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Записаться", callback_data=f"subscribe:{table_id}")
                markup.add(item1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=markup)
                #или
                #bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
                bot.answer_callback_query(call.id, "Отписано!")

            elif action == "subscribe":
                # Записываем пользователя в таблицу
                if db.records_table(table_id, call.from_user.id):
                    bot.send_message(call.message.chat.id, f"Вы успешно записались в таблицу с ID {table_id}")
                else:
                    bot.send_message(call.message.chat.id, f"Вы уже записаны в таблицу с ID {table_id}")
                # Обновляем сообщение, чтобы отобразить кнопку "Отписаться"
                markup = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Отписаться", callback_data=f"unsubscribe:{table_id}")
                markup.add(item1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=markup)
                #или
                #bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

                bot.answer_callback_query(call.id, "Записано!")

            else:
                bot.send_message(call.message.chat.id, "Неизвестное действие.")

    except Exception as e:
        print(f"Ошибка в callback_inline: {e}")
        bot.send_message(call.message.chat.id, f"Произошла ошибка: {e}")

# Удалите функцию records_table, она больше не нужна


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
        bot.send_message(message.chat.id, f"Таблица создана! \n{print_table(int(id_table))}", reply_markup=markup)

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