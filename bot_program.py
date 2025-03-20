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
        markup.add(item1, item2)
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
        table_id = int(message.text[1:])  # Извлекаем ID таблицы
        print(table_id)
        table_name, table_description = db.get_info_table(table_id)  # Получаем информацию о таблице

        if table_name:  # Если таблица существует
            markup = types.InlineKeyboardMarkup()
            messeage_send = []

            # Проверяем, записан ли пользователь в таблицу
            if db.check_user_in_table(table_id, message.from_user.id):
                item1 = types.InlineKeyboardButton("Отписаться", callback_data=f"unsubscribe:{table_id}")
                messeage_send.append('Вы записаны в таблицу. Вы можете отписаться.')
            else:
                item1 = types.InlineKeyboardButton("Записаться", callback_data=f"subscribe:{table_id}")
                messeage_send.append('Вы не записаны в таблицу.')

            # Проверяем, является ли пользователь владельцем таблицы
            if db.is_user_owner(table_id, message.from_user.id):
                settings_button = types.InlineKeyboardButton("Настройки", callback_data=f"show_settings:{table_id}")
                markup.add(settings_button)

            markup.add(item1)  # Добавляем кнопку "Записаться" или "Отписаться"
            messeage_send.append(print_table(table_id))  # Добавляем информацию о таблице

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
        if call.message:  # Проверяем, что сообщение существует
            data = call.data.split(":")
            action = data[0]

            if action == "show_settings":
                show_settings(call)  # Вызов

            elif action == "unsubscribe":
                try:
                    table_id = int(data[1])
                except (IndexError, ValueError):
                    bot.send_message(call.message.chat.id, "Некорректный ID таблицы (отписка).")
                    return
                # Отписываем пользователя от таблицы
                if db.delete_user_from_table(table_id, call.from_user.id):
                    bot.send_message(call.message.chat.id, f"Вы успешно отписались от таблицы с ID {table_id}")
                else:
                    bot.send_message(call.message.chat.id, f"Не удалось отписаться от таблицы с ID {table_id}")

                # Обновляем сообщение, чтобы отобразить кнопку "Записаться"
                markup = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Записаться", callback_data=f"subscribe:{table_id}")
                markup.add(item1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=call.message.text, reply_markup=markup)
                bot.answer_callback_query(call.id, "Отписано!")

            elif action == "subscribe":
                try:
                    table_id = int(data[1])
                except (IndexError, ValueError):
                    bot.send_message(call.message.chat.id, "Некорректный ID таблицы (запись).")
                    return
                # Записываем пользователя в таблицу
                if db.records_table(table_id, call.from_user.id):
                    bot.send_message(call.message.chat.id, f"Вы успешно записались в таблицу с ID {table_id}")
                else:
                    bot.send_message(call.message.chat.id, f"Вы уже записаны в таблицу с ID {table_id}")
                # Обновляем сообщение, чтобы отобразить кнопку "Отписаться"
                markup = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Отписаться", callback_data=f"unsubscribe:{table_id}")
                markup.add(item1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=call.message.text, reply_markup=markup)

                bot.answer_callback_query(call.id, "Записано!")

            elif action.startswith("setting_"):
                handle_setting(call)  # Вызов обработчика настроек

            elif action == "back_to_table":
                back_to_table(call)  # Вызов обработчика кнопки "Назад"

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
            print(table_id, 'DF')
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
                if not db.is_user_owner(table_id, user_id):
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


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_settings"))
def show_settings(call):
    try:
        print("Обработчик show_settings вызван")
        chat_id = call.message.chat.id
        data = call.data.split(":")
        if len(data) > 1:
            try:
                table_id = int(data[1])  # Извлекаем ID таблицы
                print(f"Получен table_id: {table_id}")
            except ValueError:
                bot.send_message(chat_id, "Некорректный ID таблицы.")
                return
        else:
            bot.send_message(chat_id, "Не удалось получить ID таблицы.")
            return

        # Создаем кнопки настроек
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Уведомления ❌", callback_data=f"setting_1_{table_id}")
        button2 = types.InlineKeyboardButton("Visibility", callback_data=f"setting_2_{table_id}")
        button3 = types.InlineKeyboardButton("Назад", callback_data=f"back_to_table:{table_id}")
        markup.add(button1, button2)
        markup.add(button3)

        # Обновляем сообщение
        bot.edit_message_text(chat_id=chat_id,
                              message_id=call.message.message_id,
                              text="Выберите настройку\nVisibility - Участники могут смотреть содержимое таблицы.",
                              reply_markup=markup)
        print("Сообщение обновлено в show_settings")
    except Exception as error:
        print(f"Ошибка в show_settings: {error}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("setting_"))
def handle_setting(call):
    try:
        print("Обработчик handle_setting вызван")
        data = call.data.split("_")
        if len(data) < 3:
            bot.answer_callback_query(call.id, "Некорректный формат callback_data")
            return

        setting_number = int(data[1])  # Номер настройки
        table_id = data[2]  # ID таблицы

        if not table_id.isdigit():
            bot.answer_callback_query(call.id, "Некорректный ID таблицы.")
            return

        table_id = int(table_id)
        name_table = db.name_table(table_id)  # Получаем название таблицы
        print(f"Получено название таблицы: {name_table}")

        match setting_number:
            case 1:
                message = f"Вы теперь будете получать уведомления о таблице {name_table}."
            case 2:
                if db.change_show_participants(table_id):
                    visibility_status = "могут" if db.visibility(table_id) else "не могут"
                    message = f"Теперь участники таблицы {name_table} {visibility_status} смотреть содержимое."
                else:
                    message = "Ошибка при изменении видимости."
            case _:
                message = "Неизвестная настройка."

        # Обновляем текст сообщения
        updated_message = f"{message}"

        # Создаем кнопку "Назад"
        markup = types.InlineKeyboardMarkup()
        back_button = types.InlineKeyboardButton("Назад", callback_data=f"back_to_table:{table_id}")
        markup.add(back_button)

        # Обновляем сообщение
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=updated_message,
                              reply_markup=markup)
        print("Сообщение обновлено в handle_setting")

    except Exception as error:
        print(f"Ошибка в handle_setting: {error}")
        bot.answer_callback_query(call.id, "Произошла ошибка.")

def create_main_menu_markup(table_id):
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("Записаться", callback_data=f"subscribe:{table_id}")
    item2 = types.InlineKeyboardButton("Отписаться", callback_data=f"unsubscribe:{table_id}")
    settings_button = types.InlineKeyboardButton("Настройки", callback_data=f"show_settings:{table_id}")
    markup.add(item1, item2)
    markup.add(settings_button)
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_table"))
def back_to_table(call):
    try:
        print("Обработчик back_to_table вызван")
        data = call.data.split(":")
        if len(data) > 1:
            table_id = int(data[1])  # Извлекаем ID таблицы
            print(f"Получен table_id: {table_id}")
        else:
            bot.answer_callback_query(call.id, "Некорректный ID таблицы.")
            return

        # Возвращаем пользователя к исходному сообщению с кнопками "Записаться/Отписаться"
        # Создаем новое сообщение с информацией о таблице
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=f"Таблица с ID {table_id}",
                              reply_markup=create_main_menu_markup(table_id))
        print("Сообщение обновлено в back_to_table")

    except Exception as error:
        print(f"Ошибка в back_to_table: {error}")
        bot.answer_callback_query(call.id, "Произошла ошибка.")


# Обработчик всех сообщений, начинающихся с "/" и не соответствующих известным командам.
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def unknown_command(message):
    bot.reply_to(message, "Неизвестная команда. Попробуйте /help")


# Запуск бота
bot.polling(none_stop=True)