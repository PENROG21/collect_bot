from typing import List, Union
import telebot
from telebot import types
import pandas as pd
import os

from data_base import PostgresConnection

# вводим токен бота
bot = telebot.TeleBot("7716080556:AAHJN8nkSiiEwYNnXR9DTm9JSetyi-PoKrc")

db = PostgresConnection(
    database="telebot",
    password="PENROG21"
)
db.connect()
user_data = {}


# Добавление данных о пользователе
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     f"🎉 Привет {message.from_user.first_name}! "
                     f"\n\nЭто collect - ваш помощник для организации мероприятий. \n"
                     "Больше никаких списков на бумаге! Создайте таблицу и делитесь ссылкой🤩.\n"
                     "Для записи в таблицу или получения информации просто отправьте ее ID😉.\nДля получения "
                     "инструкции нажмите /help")

    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

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
        bot.send_message(message.chat.id, print_table(owen_table), parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "Посмотреть где я записан")
def view_my_registrations_handler(message):
    owen_participants = db.get_table_info_for_user(message.from_user.id)
    if not owen_participants:
        bot.send_message(message.chat.id, "Вы пока нигде не записаны.")
    else:
        bot.send_message(message.chat.id, print_table(owen_participants), parse_mode="Markdown")


def print_table(id_tables: Union[int, List[int]]) -> str:
    """
    Формирует строку с информацией о таблице/таблицах.

    Args:
        id_tables: ID таблицы (int) или список ID таблиц (List[int]).

    Returns:
        Строка с информацией о таблице/таблицах, разделенная переносами строк.
        В случае ошибки возвращает пустую строку.
    """
    try:
        if isinstance(id_tables, int):
            id_tables = [id_tables]

        results = []
        for table_id in id_tables:
            # Из id таблиц получаем информацию об них
            info_table = db.get_info_table(table_id)

            if not info_table:
                print(f"Не удалось получить информацию о таблице с ID {table_id}")
                continue  # Переходим к следующей таблице, если не удалось получить информацию

            name, description = info_table
            results.append(f"📃 *Название Таблицы:* {name}\n"
                           f"📝 *Описание:* {description}\n"
                           f"🆔 *ID:* /{table_id}\n")

        return "\n".join(results)  # Возвращаем все строки, разделенные переносами строк

    except Exception as e:
        print(f"Ошибка в print_table: {e}")
        return ""  # Возвращаем пустую строку в случае ошибки


# Функция для отображения информации о таблице
def display_table_info(chat_id, message_id, table_id, user_id):
    """Отображает информацию о таблице и кнопки действий."""
    try:
        table_name, table_description = db.get_info_table(table_id)
        if not table_name:
            bot.send_message(chat_id, f"Таблица с ID {table_id} не найдена.")
            return

        # Определяем состояние подписки пользователя
        is_user_subscribed = db.check_user_in_table(table_id, user_id)

        # Создаем markup для кнопок
        markup = types.InlineKeyboardMarkup(row_width=1)

        # Кнопка "Записаться/Отписаться"
        subscribe_button_text = "✅ Отписаться" if is_user_subscribed else "📝 Записаться"
        subscribe_button_callback = f"unsubscribe:{table_id}" if is_user_subscribed else f"subscribe:{table_id}"
        markup.add(types.InlineKeyboardButton(subscribe_button_text, callback_data=subscribe_button_callback))

        # Кнопка "Настройки" (отображается только для владельца)
        if db.is_user_owner(table_id, user_id):
            markup.add(types.InlineKeyboardButton("⚙️ Настройки", callback_data=f"show_settings:{table_id}"))

        # Кнопка "Отправить другу"
        invite_link = f"https://t.me/{bot.get_me().username}?start=join_{table_id}"
        markup.add(types.InlineKeyboardButton("🔗 Отправить другу", url=invite_link))

        # Формируем текст сообщения
        table_info = print_table(table_id)

        # Отправляем или редактируем сообщение
        if message_id:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=table_info,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            bot.send_message(
                chat_id=chat_id,
                text=table_info,
                reply_markup=markup,
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"Ошибка при отображении информации о таблице: {e}")
        bot.send_message(chat_id, f"Произошла ошибка: {e}")


# Обработчик ввода ссылки на таблицу
@bot.message_handler(func=lambda message: message.text.startswith('/') and message.text[1:].isdigit())
def handle_table_link(message):
    """Обрабатывает ввод ссылки на таблицу (например, /12)."""
    try:
        table_id_str = message.text[1:] if message.text.startswith('/') else message.text
        table_id = int(table_id_str)
        user_id = message.from_user.id

        display_table_info(message.chat.id, None, table_id, user_id)

    except ValueError:
        bot.reply_to(message, "Неверный формат данных☹️.\nВведите целое число (например, 12 или /12).")

    except Exception as e:
        print(f"Ошибка в handle_table_link: {e}")
        bot.reply_to(message, f"Произошла ошибка: {e}")


@bot.message_handler(commands=['join'])
def join_table(message):
    """Обрабатывает команду /join tableid=XXX."""
    try:
        # Извлекаем tableid из параметров команды
        params = message.text.split(' ', 1)  # Разделяем команду и параметры
        if len(params) > 1:
            params_str = params[1] #Получаем строку tableid=123
            params_list = params_str.split('=') #Делим строку tableid=123 на массив ["tableid","123"]

            if len(params_list) > 1 and params_list[0].lower() == "tableid" :
                table_id_str = params_list[1]
            else:
                bot.reply_to(message, "Неверный формат ссылки-приглашения.")
                return
        else:
            bot.reply_to(message, "Неверный формат ссылки-приглашения.")
            return

        if not table_id_str.isdigit():
            bot.reply_to(message, "Некорректный ID таблицы.")
            return

        table_id = int(table_id_str)
        user_id = message.from_user.id  # Получаем id пользователя

        # Проверяем, существует ли таблица
        table_name, table_description = db.get_info_table(table_id)
        if not table_name:
            bot.reply_to(message, f"Таблица с ID {table_id} не найдена.")
            return

        # Если таблица существует, отображаем информацию о ней
        display_table_info(message, table_id, user_id)

    except Exception as e:
        print(f"Ошибка в join_table: {e}")
        bot.reply_to(message, f"Произошла ошибка: {e}")


def get_table_id_from_command(message):
    """Извлекает ID таблицы из команды /join."""
    try:
        text = message.text
        table_id = text.split('=')[1] #Делим строку /join tableid=123 на массив ["/join tableid","123"]
        return int(table_id)
    except (IndexError, ValueError):
        return None


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    """Обработчик нажатий на инлайн-кнопки"""
    try:
        if call.message:  # Проверяем, что сообщение существует
            data = call.data.split(":")
            action = data[0]
            table_id = int(data[1])
            user_id = call.from_user.id

            print(f"Callback data: {call.data}")  # Логирование для отладки
            print(f"Parsed data: {data}")

            if action == "show_settings":
                show_settings(call, table_id)  # Вызов обработчика настроек

            elif action == "unsubscribe":
                # Отписываем пользователя от таблицы
                if db.delete_user_from_table(table_id, user_id):
                    bot.answer_callback_query(call.id, f"Вы успешно отписались от таблицы с ID {table_id}")
                else:
                    bot.send_message(call.message.chat.id, f"Не удалось отписаться от таблицы с ID {table_id}")

                # Обновляем сообщение через display_table_info
                display_table_info(call.message.chat.id, call.message.message_id, table_id, user_id)

            elif action == "subscribe":
                # Записываем пользователя в таблицу
                if db.records_table(table_id, user_id):
                    bot.answer_callback_query(call.id, f"Вы успешно записались в таблицу с ID {table_id}")

                    # Проверяем, нужно ли уведомлять владельца о записи
                    if db.checking_for_notification(table_id):
                        notification_signed_user(id_table=table_id, id_user=user_id)
                else:
                    bot.send_message(call.message.chat.id, f"Вы уже записаны в таблицу с ID {table_id}")

                # Обновляем сообщение через display_table_info
                display_table_info(call.message.chat.id, call.message.message_id, table_id, user_id)

            elif action == "setting":
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

        id_table = db.create_table(table_name, table_description, id_owner=message.from_user.id)
        user_data[message.chat.id]["id_table"] = id_table

        # Формируем текст сообщения
        bot.send_message(message.chat.id, f"🎉 Таблица *{table_name}* успешно создана!", parse_mode="Markdown")

        message.text = f"/{id_table}"  # Создаем текстовое сообщение, как будто пользователь ввел ссылку
        handle_table_link(message)

        # После создания таблицы сбрасываем состояние
        user_data.pop(message.chat.id, None)

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
                    if not db.visibility(table_id):
                        bot.reply_to(message, "Вы не можете просмотреть таблицу.\nНедостаточно прав")

                list_participants = db.show_all_participants_table(table_id)

                if not list_participants:  # Проверка на пустоту списка упрощена
                    bot.reply_to(message, "Таблица пуста.")
                else:
                    table_name = db.name_table(id_table=table_id)
                    header = "ID | Имя | Фамилия | Логин | Платформа"
                    rows = [f"{num + 1}) {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}" for num, row in
                            enumerate(list_participants)]
                    output = f"Таблица {table_name}\nУчастники:\n{header}\n{chr(10).join(rows)}"
                    bot.reply_to(message, output)

    except Exception as error:
        print("Ошибка при работе с функцией show_participants\n", error)


@bot.message_handler(commands=['excel'])
def excel_table(message):
    """
       Обработчик команды /excel для получения таблицы в формате Excel.
    """
    try:
        table_id = int(str(message.text)[6:])  # [6:] вместо [5:], т.к. /show
    except (ValueError, IndexError):
        bot.reply_to(message, "Неверный формат команды. Используйте /excel <id_таблицы>")
        return
    try:
        user_id = message.from_user.id
        if not db.exist_user(user_id):
            bot.reply_to(message, "Вас нет в базе данных")
        else:
            if not db.exists_table(table_id):
                bot.reply_to(message, "Нет такой таблицы")
            else:
                if not db.is_user_owner(table_id, user_id):
                    bot.reply_to(message, "Вы не можете получить excel таблицы.\nНедостаточно прав!")

                list_participants = db.show_all_participants_table(table_id)

                if not list_participants[0]:
                    bot.reply_to(message, "Таблица пуста.")
                else:
                    column_names = ['ID', 'Имя', 'Фамилия', 'Логин', 'Платформа']
                    df = pd.DataFrame(list_participants, columns=column_names)

                    df.insert(0, '#', range(1, len(df) + 1))

                    file_name = f'{db.name_table(table_id)}.xlsx'
                    df.to_excel(file_name, index=False)

                    # Отправляем таблицу пользователю
                    with open(file_name, 'rb') as file:
                        bot.send_document(message.chat.id, file)

                    # Удаляем файл
                    os.remove(file_name)

    except Exception as error:
        print("Ошибка при работе с функцией excel_table\n", error)


@bot.message_handler(
    func=lambda message: user_data.get(message.chat.id, {}).get("state") == "waiting_for_table_description")
def handle_table_description(message):
    """Обрабатывает описание таблицы, создает таблицу и отправляет информацию о ней."""
    try:
        if message.text == "Отмена":
            # Сбрасываем состояние и возвращаемся к началу
            user_data.pop(message.chat.id, None)
            send_welcome(message)
            return

        # Сохраняем описание таблицы
        table_description = message.text
        user_data[message.chat.id]["table_description"] = table_description

        # Выводим собранные данные
        table_name = user_data[message.chat.id]["table_name"]

        # Записываем пользователя если нет.
        if not db.exist_user(message.from_user.id):
            db.records_user(id_platform=1, user_id=message.from_user.id, username=message.from_user.username,
                            user_name=message.from_user.first_name, user_surname=message.from_user.last_name)

        # Создаём таблицу
        id_table = db.create_table(table_name, table_description, id_owner=message.from_user.id)
        user_data[message.chat.id]["id_table"] = id_table

        # Имитируем вызов handle_table_link
        message.text = f"/{id_table}"  # Создаем текстовое сообщение, как будто пользователь ввел ссылку
        handle_table_link(message)  # Вызываем функцию handle_table_link

        # После создания таблицы сбрасываем состояние
        user_data.pop(message.chat.id, None)

    except Exception as error:
        print("Ошибка при работе с функцией handle_table_description\n", error)
        bot.reply_to(message, "Произошла ошибка при создании таблицы.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_settings"))
def show_settings(call, table_id):
    """Отображает настройки таблицы с информацией о таблице."""
    try:
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        # Получаем информацию о таблице
        table_name, table_description = db.get_info_table(table_id)

        # Формируем сообщение с информацией о таблице и настройками
        output_message = (
            "⚙️ *Настройки таблицы*\n\n"
            f"🆔 *ID:* `/{table_id}`\n"
            f"📃 *Название:* {table_name}\n"
            f"📝 *Описание:* {table_description}\n\n"
            "✨ *Выберите настройку:*\n\n"
            "👁️ *Видимость:* Участники таблицы могут просматривать содержимое и сохранять таблицу в формате Excel.\n"
            "🔔 *Уведомления:* Получайте уведомления о новых участниках таблицы и их данные.\n"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)  # Чтобы кнопки были в столбик

        # Текст для кнопки уведомлений в зависимости от состояния
        item_visibility = types.InlineKeyboardButton(
            "🙈 Скрыть таблицу" if db.visibility(table_id) else "👁️ Показать таблицу",
            callback_data=f"setting:2:{table_id}"
        )

        item_notifications = types.InlineKeyboardButton(
            "🔔 Включить уведомления" if not db.checking_for_notification(table_id) else "🔕 Отключить уведомления",
            callback_data=f"setting:1:{table_id}"
        )

        item_back = types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"back_to_table:{table_id}"
        )
        # Добавляем все кнопки
        markup.add(item_visibility, item_notifications)
        markup.add(item_back)

        # Отправляем сообщение с информацией о таблице и кнопками настроек
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=output_message,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        print(f"Ошибка в show_settings: {e}")
        bot.send_message(chat_id, f"Произошла ошибка: {e}")


# Обработчик для кнопки "Назад в меню"
@bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_menu:"))
def handle_back_to_menu(call):
    """Обрабатывает нажатие кнопки 'Назад в меню'."""
    try:
        send_welcome(call.message)  # Отправляем приветственное сообщение с меню
    except Exception as e:
        print(f"Ошибка при возврате в главное меню: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при возврате в меню.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("setting:"))
def handle_setting(call):
    try:
        data = call.data.split(":")
        if len(data) < 3:
            bot.answer_callback_query(call.id, "Некорректный формат callback_data")
            return

        setting_number = int(data[1])  # Номер настройки
        table_id = int(data[2])  # ID таблицы

        name_table = db.name_table(table_id)  # Получаем название таблицы

        if setting_number == 1:
            if db.set_notification(id_table=table_id):
                # Отправляем пользователю итог операции.
                if db.checking_for_notification(table_id):
                    bot.answer_callback_query(call.id, f"Уведомления для таблицы {name_table} включены.")
                else:
                    bot.answer_callback_query(call.id, f"Уведомления для таблицы {name_table} выключены.")
            else:
                bot.answer_callback_query(call.id, "Ошибка при изменении уведомлений.")

        elif setting_number == 2:
            if db.change_show_participants(table_id):
                visibility_status = "могут" if db.visibility(table_id) else "не могут"
                bot.answer_callback_query(call.id,
                                          f"Теперь участники таблицы {name_table} {visibility_status} "
                                          f"смотреть содержимое.")
            else:
                bot.answer_callback_query(call.id, "Ошибка при изменении видимости.")
        else:
            bot.answer_callback_query(call.id, "Неизвестная настройка.")
            return

        # Вызываем show_settings напрямую, передавая table_id
        show_settings(call, table_id) # <--- Важно!

    except Exception as error:
        print(f"Ошибка в handle_setting: {error}")
        bot.answer_callback_query(call.id, "Произошла ошибка.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_table"))
def back_to_table(call):
    """
    Функция для возращение назад.
    :param call:
    :return:
    """
    try:
        data = call.data.split(":")
        if len(data) > 1:
            table_id = int(data[1])  # Извлекаем ID таблицы
            user_id = call.from_user.id  # Получаем id пользователя

            display_table_info(call.message.chat.id, call.message.message_id, table_id, user_id)
        else:
            bot.answer_callback_query(call.id, "Некорректный ID таблицы.")
    except ValueError:
        bot.answer_callback_query(call.id, "Некорректный ID таблицы.")
    except Exception as error:
        print(f"Ошибка в back_to_table: {error}")
        bot.answer_callback_query(call.id, "Произошла ошибка.")


# Обработчик всех сообщений, начинающихся с "/" и не соответствующих известным командам.


@bot.message_handler(commands=['random'])
def random_one_user_table(message):
    """
    Обработчик команды /random для отображения случайного участника таблицы.
    """
    try:
        table_id = int(str(message.text)[8:])  # Изменено на [8:], так как команда /random
    except (ValueError, IndexError):
        bot.reply_to(message, "Неверный формат команды. Используйте /random <id_таблицы>")
        return

    try:
        user_id = message.from_user.id
        if not db.exist_user(user_id):
            bot.reply_to(message, "Вас нет в базе данных")
        else:
            if not db.exists_table(table_id):
                bot.reply_to(message, "Нет такой таблицы")
            else:
                if not db.is_user_owner(table_id, user_id):
                    bot.reply_to(message, "Вы не можете просмотреть эту таблицу.\nНедостаточно прав!")
                    return

                list_participants = db.select_rando_user(table_id)

                if list_participants is None:
                    bot.reply_to(message, "В таблице нет участников.")
                else:
                    user_id, user_name, user_surname, username, platform_name = list_participants  # Распаковка кортежа

                    # Форматирование строки с данными
                    output_string = (
                        f"Таблица: {db.name_table(id_table=table_id)}\n"
                        f"Участник:\n"
                        f"ID: {user_id}\n"
                        f"Имя: {user_name}\n"
                        f"Фамилия: {user_surname if user_surname else '-'}\n"  # Проверка на None
                        f"Логин: {username if username else '-'}\n"  # Проверка на None
                        f"Платформа: {platform_name}"
                    )
                    bot.reply_to(message, output_string)

    except Exception as error:
        print(f"Ошибка в random_one_user_table: {error}")


def notification_signed_user(id_table, id_user):
    """Отправляет уведомление владельцу таблицы о новой записи, включая информацию о пользователе."""
    try:
        owner_id = db.get_id_owen_table(id_table)  # Получаем ID владельца таблицы
        if not owner_id:
            print(f"Не удалось определить владельца таблицы с ID {id_table}")
            return  # Завершаем функцию, если не удалось получить ID владельца

        table_name = db.name_table(id_table=id_table)  # Получаем название таблицы
        data_user = db.get_info_user_id(id_user)  # Получаем данные пользователя

        if not data_user:
            print(f"Не удалось получить данные пользователя с ID {id_user}")
            notification_text = (
                f"В вашу таблицу \"{table_name}\" (ID: {id_table}) "
                f"записался новый пользователь (ID: {id_user}). "
                f"Не удалось получить дополнительную информацию о пользователе."
            )
        else:
            user_name = data_user[0]
            user_surname = data_user[1] if data_user[1] else "Не указана"  # Фамилия, если есть

            notification_text = (
                f"🎉 В вашу таблицу \"{table_name}\" (ID: {id_table}) "
                f"записался новый участник!\n\n"
                f"👤 Имя: {user_name}\n"
                f"📝 Фамилия: {user_surname}\n"
                f"🆔 ID Пользователя: {id_user}"
            )

        bot.send_message(owner_id, notification_text)  # Отправляем уведомление

    except Exception as error:
        print(f"Ошибка в notification_signed_user: {error}")


@bot.message_handler(func=lambda message: message.text.startswith('/'))
def unknown_command(message):
    bot.reply_to(message, "Неизвестная команда. Попробуйте /help")


# Запуск бота
bot.polling(none_stop=True)
