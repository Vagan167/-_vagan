from token import AWAIT

import schedule
import time
import logging
import asyncio

from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from prettytable import PrettyTable

from aiogram.types import CallbackQuery, ParseMode, WebAppInfo
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Location
import sqlite3 as sq
import os

from getpass import getpass

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from pyexpat.errors import messages
from aiogram.types import InputFile
from yookassa import Configuration, Payment

import markups as mk
from yookassa import Configuration
from flask import Flask, request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


# Укажите свои данные от ЮКассы
Configuration.account_id = ''  # Ваш идентификатор магазина
Configuration.secret_key = ''  # Ваш секретный ключ

app = Flask(__name__)

class GeneralState(StatesGroup):
    phone_reg = State()
    dz_one = State()
    dz_two = State()
    dz_three = State()
    reviews = State()
    email_reg = State()
class AdminState(StatesGroup):
    password_state = State()
    delete = State()
    course_eli_stra = State()
    eli_stra_one = State()
    eli_stra_two = State()
    eli_stra_three = State()
    eli_stra_four = State()
    man = State()

# Создаем бота и диспетчер
bot = Bot(token='')
dp = Dispatcher(bot, storage=MemoryStorage())

now = datetime.now()
new_date_half_year = now + relativedelta(months=6)
new_date_half_year_1 = now + relativedelta(years=1)
time_data_6m = new_date_half_year.strftime("%Y-%m-%d %H:%M:%S")
time_data_1y = new_date_half_year_1.strftime("%Y-%m-%d %H:%M:%S")
current_date = now.strftime("%Y-%m-%d %H:%M:%S")


# Функция для периодической отправки сообщений
async def periodic_task():
    while True:
        await asyncio.sleep(43200)  # Асинхронная задержка 1 секунда
        try:
            with sq.connect('sq_baze/users_courses/users_courses.db') as con:
                cur = con.cursor()
                cur.execute("SELECT id, course FROM users")  # Получаем id и курс всех пользователей
                users = cur.fetchall()  # Извлекаем все записи

                for user in users:
                    user_id, course = user  # Разворачиваем каждую строку
                    if course:  # Проверяем, что у пользователя есть курс
                        try:
                            # Отправка напоминания только пользователям с курсом
                            await bot.send_message(chat_id=user_id, text=f"Напоминание по курсу: {course}")
                        except Exception as e:
                            logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        except Exception as e:
            logging.error(f"Ошибка при обращении к базе данных: {e}")

# Создаем платеж в Юкассе, добавляем email для чека
async def create_payment(amount, description, phone_number, email, currency="RUB"):
    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": currency,
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://your-return-url.com",
        },
        "capture": True,
        "description": description,
        "receipt": {
            "customer": {
                "email": email,  # Добавляем email
                "phone": phone_number
            },
            "items": [
                {
                    "description": "Эликсир страсти",
                    "quantity": "1.00",
                    "amount": {
                        "value": str(amount),
                        "currency": currency
                    },
                    "vat_code": 1,
                    "payment_subject": "service",
                    "payment_mode": "full_payment"
                }
            ]
        }
    })
    return payment.confirmation.confirmation_url

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    # Создание таблицы с ограничением UNIQUE на поле id
    with sq.connect("sq_baze/users/users.db") as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,   -- Устанавливаем id как PRIMARY KEY, чтобы был уникальным
        last_name TEXT,
        first_name TEXT,
        email TEXT,
        phone_number TEXT,
        UNIQUE(id)
        )""")
    with sq.connect("sq_baze/users_courses/users_courses.db") as con:
        cur = con.cursor()

        cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER,
        last_name TEXT,
        first_name TEXT,
        phone TEXT,
        course TEXT,
        stage TEXT,
        data_ot TEXT,
        data_do TEXT
        )""")
    # Код для отправки сообщения пользователю и установки состояния
    await bot.send_message(message.chat.id, 'Пожалуйста, отправьте ваш номер телефона чтобы продолжить.', reply_markup=mk.btn_open_main)
    await GeneralState.phone_reg.set()

    # Запуск периодической задачи с использованием asyncio.create_task()
    asyncio.create_task(periodic_task())

async def cleanup_expired_courses():
    while True:
        # Текущая дата
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Подключаемся к базе данных
        with sq.connect('sq_baze/users_courses/users_courses.db') as con:
            cur = con.cursor()

            # Получаем записи, срок которых истёк
            cur.execute("SELECT id, course FROM users WHERE data_do <= ?", (current_date,))
            expired_courses = cur.fetchall()

            if expired_courses:
                for record in expired_courses:
                    user_id, course_name = record

                    # Удаляем запись из БД
                    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))

                    # Удаляем связанные файлы (например, видео)
                    course_videos_path = f"videos/{user_id}/{course_name}"
                    if os.path.exists(course_videos_path):
                        for file in os.listdir(course_videos_path):
                            file_path = os.path.join(course_videos_path, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        os.rmdir(course_videos_path)  # Удаляем директорию курса, если она пуста

        # Ждём 1 день до следующей проверки
        await asyncio.sleep(86400)
async def run_daily_task(target_time: str):
    """
    Запускает функцию ежедневно в определённое время.

    :param target_time: Время запуска в формате "HH:MM".
    """
    while True:
        now = datetime.now()
        # Парсим целевое время
        target_hour, target_minute = map(int, target_time.split(":"))
        # Вычисляем целевую дату и время
        target_datetime = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        # Если целевое время уже прошло, добавляем один день
        if target_datetime < now:
            target_datetime += timedelta(days=1)
        # Рассчитываем время до запуска
        time_to_sleep = (target_datetime - now).total_seconds()
        print(f"Следующий запуск через {time_to_sleep} секунд.")
        await asyncio.sleep(time_to_sleep)  # Засыпаем до целевого времени
        await cleanup_expired_courses()  # Запускаем задачу

# Функция, вызываемая при старте бота
async def on_startup(dp):
    # Запускаем периодическую задачу при старте
    asyncio.create_task(periodic_task())

# Обработчик состояния phone_reg
@dp.message_handler(state=GeneralState.phone_reg, content_types=types.ContentTypes.ANY)
async def save_send_phone_status(message: types.Message, state: FSMContext):
    if message.content_type == types.ContentType.CONTACT and message.contact.user_id == message.from_user.id:
        await message.reply("Отправьте вашу почту.")
        async with state.proxy() as data:
            data['phone_number'] = message.contact.phone_number  # Сохраняем номер телефона
        await GeneralState.email_reg.set()
    else:
        await message.reply("Пожалуйста, отправьте ваш номер телефона через кнопку «Поделиться номером».")

# Обработчик состояния email_reg для регистрации почты
@dp.message_handler(state=GeneralState.email_reg, content_types=types.ContentTypes.TEXT)
async def save_email_status(message: types.Message, state: FSMContext):
    email = message.text  # Получаем email
    async with state.proxy() as data:
        phone = data['phone_number']  # Получаем сохраненный номер телефона
        user_data = (message.from_user.id, message.from_user.last_name, message.from_user.first_name, email, phone)  # Добавляем email в user_data

    # Добавление данных в базу, запись будет уникальной благодаря PRIMARY KEY на поле id
    with sq.connect('sq_baze/users/users.db') as con:
        cur = con.cursor()
        cur.execute("""INSERT OR IGNORE INTO users (id, last_name, first_name, email, phone_number) VALUES (?, ?, ?, ?, ?);""", user_data)
        con.commit()

    await message.reply(f"Спасибо! Ваша почта ({email}) сохранена.", reply_markup=mk.btn_general_menu)
    await state.finish()  # Завершаем процесс регистрации

@dp.message_handler(lambda message: message.text == '📝Мои курсы')
async def courses(message: types.Message):
    user_id = message.from_user.id
    with sq.connect('sq_baze/users_courses/users_courses.db') as con:
        cur = con.cursor()
        cur.execute("SELECT course FROM users WHERE id = ?", (user_id,))
        course = cur.fetchone()

        if course and course[0] == 'Курс "Эликсир страсти"':
            await bot.send_message(message.chat.id, 'Открываю список курсов', reply_markup=mk.btn_courses_dop_menu)
        else:
            await bot.send_message(message.chat.id, 'У вас нет курсов')

@dp.message_handler(lambda message: message.text == '🛒Купить курсы')
async def buy_courses(message: types.Message):
    await bot.send_message(message.chat.id, 'Выберите курс который хотите купить', reply_markup=mk.btn_buy_course_main)

@dp.message_handler(lambda message: message.text == '💳Покупка курсов')
async def buy(message: types.Message):
    await bot.send_message(message.chat.id, 'Перехожу...', reply_markup=mk.btn_buy_menu)

@dp.message_handler(lambda message: message.text == '❤️Купить курс "Эликсир страсти" ПРИНЦЕССА')
async def process_payment_princess(message: types.Message):
    user_id = message.from_user.id
    amount = 1.00
    description = "Оплата курса 'Эликсир страсти' (Принцесса)"
    request_id = f"{message.from_user.id}_{int(time.time())}"
    # Получаем номер телефона и email из базы
    with sq.connect('sq_baze/users/users.db') as con:
        cur = con.cursor()
        cur.execute("SELECT phone_number, email FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()

    if result:
        phone_number = result[0]
        email = result[1]  # Получаем email из базы
    else:
        await message.answer("Ваш номер телефона и/или email не найдены. Пожалуйста, зарегистрируйтесь. /start")
        return

    try:
        # Создаем платеж, передаем email
        payment_url = await create_payment(amount, description, phone_number, email)

        # Кнопка для оплаты
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Оплатить", url=payment_url, callback_data=f'user_created_{request_id}')
        )
        await bot.send_message(message.chat.id,
                               "После покупки свяжитесь с продавцом и сообщите о покупке. Пожалуйста, перейдите в раздел 'Помощь' и 'Обратная связь', после этого с вами свяжутся!")
        await message.answer("Нажмите кнопку ниже, чтобы оплатить:", reply_markup=keyboard)
    except Exception as e:
        await message.answer(f"Ошибка при создании платежа: {e}")

@dp.message_handler(lambda message: message.text == '❤️Купить курс "Эликсир страсти" КОРОЛЕВА')
async def process_payment_princess(message: types.Message):
    user_id = message.from_user.id
    amount = 1.00
    description = "Оплата курса 'Эликсир страсти' (КОРОЛЕВА)"
    request_id = f"{message.from_user.id}_{int(time.time())}"
    # Получаем номер телефона и email из базы
    with sq.connect('sq_baze/users/users.db') as con:
        cur = con.cursor()
        cur.execute("SELECT phone_number, email FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()

    if result:
        phone_number = result[0]
        email = result[1]  # Получаем email из базы
    else:
        await message.answer("Ваш номер телефона и/или email не найдены. Пожалуйста, зарегистрируйтесь. /start")
        return

    try:
        # Создаем платеж, передаем email
        payment_url = await create_payment(amount, description, phone_number, email)

        # Кнопка для оплаты
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Оплатить", url=payment_url, callback_data=f'user_created_{request_id}')
        )
        await bot.send_message(message.chat.id,
                               "После покупки свяжитесь с продавцом и сообщите о покупке. Пожалуйста, перейдите в раздел 'Помощь' и 'Обратная связь', после этого с вами свяжутся!")
        await message.answer("Нажмите кнопку ниже, чтобы оплатить:", reply_markup=keyboard)
    except Exception as e:
        await message.answer(f"Ошибка при создании платежа: {e}")

@dp.message_handler(lambda message: message.text == '❤️Купить курс "Эликсир страсти" ВОЛШЕБНИЦА')
async def process_payment_princess(message: types.Message):
    user_id = message.from_user.id
    amount = 1.00
    description = "Оплата курса 'Эликсир страсти' (ВОЛШЕБНИЦА)"
    request_id = f"{message.from_user.id}_{int(time.time())}"

    # Получаем номер телефона и email из базы
    with sq.connect('sq_baze/users/users.db') as con:
        cur = con.cursor()
        cur.execute("SELECT phone_number, email FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()

    if result:
        phone_number = result[0]
        email = result[1]  # Получаем email из базы
    else:
        await message.answer("Ваш номер телефона и/или email не найдены. Пожалуйста, зарегистрируйтесь. /start")
        return

    try:
        # Создаем платеж, передаем email
        payment_url = await create_payment(amount, description, phone_number, email)

        # Кнопка для оплаты
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Оплатить", url=payment_url, callback_data=f'user_created_{request_id}')
        )
        await bot.send_message(message.chat.id,
                               "После покупки свяжитесь с продавцом и сообщите о покупке. Пожалуйста, перейдите в раздел 'Помощь' и 'Обратная связь', после этого с вами свяжутся!")
        await message.answer("Нажмите кнопку ниже, чтобы оплатить:", reply_markup=keyboard)
    except Exception as e:
        await message.answer(f"Ошибка при создании платежа: {e}")

@dp.message_handler(lambda message: message.text == '❤️Купить курс "Эликсир страсти" БОГИНЯ')
async def process_payment_princess(message: types.Message):
    user_id = message.from_user.id
    amount = 1.00
    description = "Оплата курса 'Эликсир страсти' (БОГИНЯ)"
    request_id = f"{message.from_user.id}_{int(time.time())}"

    # Получаем номер телефона и email из базы
    with sq.connect('sq_baze/users/users.db') as con:
        cur = con.cursor()
        cur.execute("SELECT phone_number, email FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()

    if result:
        phone_number = result[0]
        email = result[1]  # Получаем email из базы
    else:
        await message.answer("Ваш номер телефона и/или email не найдены. Пожалуйста, зарегистрируйтесь. /start")
        return

    try:
        # Создаем платеж, передаем email
        payment_url = await create_payment(amount, description, phone_number, email)
        # Кнопка для оплаты
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Оплатить", url=payment_url, callback_data=f'user_created_{request_id}')
        )
        await bot.send_message(message.chat.id,
                               "После покупки свяжитесь с продавцом и сообщите о покупке. Пожалуйста, перейдите в раздел 'Помощь' и 'Обратная связь', после этого с вами свяжутся!")
        await message.answer("Нажмите кнопку ниже, чтобы оплатить:", reply_markup=keyboard)
    except Exception as e:
        await message.answer(f"Ошибка при создании платежа: {e}")

@dp.message_handler(lambda message: message.text == '🔙Вернуться')
async def f(message: types.Message):
    await bot.send_message(message.chat.id, 'Возвращаюсь', reply_markup=mk.btn_buy_course_main)

@dp.message_handler(lambda message: message.text == '💰Цена')
async def price_buy(message: types.Message):

    price = (
        'Стоимость курса:\n\n'
        'ПРИНЦЕССА:\n'
        '1.Доступ к курсу 6 месяцев\n'
        '2.Курс в записи(полный курс упражнений, включая все материалы и шаблоны)\n'
        '3.Бонус- 1 олнайн встреча с экспертом\n'
        '4.Астрологический разбор отношений не входит в стоимость\n'
        '5.Цена: 25 000 рублей\n'
        '----------------------------------------------\n'
        'КОРОЛЕВА:\n'
        '1.Доступ к курсу 6 месяцев\n'
        '2.Курс в записи (полный курсупражнений, включая всематериалы и шаблоны)\n'
        '3.Бонус - 1 онлайн встреча с экспертом\n'
        '4.В течение курса связь сИнной по любым вопросам и разбор дз онлайн в формате голосовых сообщений\n'
        '5.Астрологический разбор отношений не входит в стоимость\n'
        'Цена: 32 000 рублей\n'
        '----------------------------------------------\n'
        'ВОЛШЕБНИЦА:\n'
        '1.Доступ к видео-урокам на 1 год\n'
        '2.Доступ в закрытый чат “Клуб любимых жен”\n'
        '3.8 тематических встреч + разбор дз и ответы на вопросы\n'
        '4.28 подборок, чек-листов и шаблонов по психолог. прокачке женщины\n'
        '5.2 месяца сопровождения наставником\n'
        '6.Конспект курса по психологии отношений на 30 страниц\n'
        '7.Бонус - Астрологический разбор отношений\n'
        'Цена: 60 000 рублей\n'
        '----------------------------------------------\n'
        'БОГИНЯ\n'
        '1.Доступ к видео-урокам навсегда\n'
        '2.Доступ в закрытый чат “Клуб любимых жен”\n'
        '3.8 личных встреч с наставником с глубокой проработкой + разбор дз и ответы на вопросы\n'
        '4.28 подборок, чек-листов и шаблонов по психолог. прокачке женщины\n'
        '5.4 месяца сопровождения наставником\n'
        '6.Конспект курса по психологии отношений на 30 страниц\n'
        '7.Мини-курс для успешных женщин “О чем писать в соцсетях”\n'
        '8.Чек-лист “Формула любви\n'
        '9.Бонус - Астрологический разбор отношений\n'
        'Цена: 200 000 рублей\n'
    )

    await bot.send_message(message.chat.id, price)

# Open course
@dp.message_handler(lambda message: message.text == '✨Курс "Эликсир страсти"')
async def courses(message: types.Message):
    user_id = message.from_user.id
    with sq.connect('sq_baze/users_courses/users_courses.db') as con:
        cur = con.cursor()
        cur.execute("SELECT course FROM users WHERE id = ?", (user_id,))
        data = cur.fetchone()
        await bot.send_message(message.chat.id, 'Ваш курс', reply_markup=mk.btn_open_course_main)

@dp.message_handler(lambda message: message.text == '📚Отправить домашнее задание')
async def courses(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    with sq.connect('sq_baze/users_courses/users_courses.db') as con:
        cur = con.cursor()

        # Получаем текущий этап курса
        cur.execute("SELECT stage_course, course FROM users WHERE id = ?", (user_id,))
        course_data = cur.fetchone()  # Получаем одну строку (кортеж)

        if course_data is None:
            await bot.send_message(message.chat.id, 'У вас нет курсов.')
            return
        else:
            stage_course, course = course_data  # Распаковываем данные из кортежа
            if int(stage_course) == 0:  # Приводим к числу, если нужно
                await bot.send_message(message.chat.id,'На этом этапе нет домашнего задания. Вы автоматически переходите на следующий этап.')
                # Обновляем этап
                stage = int(stage_course) + 1
                cur.execute("UPDATE users SET stage_course = ? WHERE id = ?", (stage, user_id))
                con.commit()  # Фиксируем изменения
                await bot.send_message(message.chat.id, f'Вы перешли на этап {stage}.')
            elif int(stage_course) == 1:  # Приводим к числу, если нужно
                await bot.send_message(message.chat.id,'Напшите ответ на домашнее задание по первому уроку')
                await GeneralState.dz_one.set()
            elif int(stage_course) == 2:  # Приводим к числу, если нужно
                await bot.send_message(message.chat.id,'Напшите ответ на домашнее задание по второму уроку')
                await GeneralState.dz_two.set()
            elif int(stage_course) == 3:  # Приводим к числу, если нужно
                await bot.send_message(message.chat.id,'Напшите ответ на домашнее задание по третьему уроку')
                await GeneralState.dz_three.set()
            else:
                await bot.send_message(message.chat.id, 'Вы прошли курс!')

@dp.message_handler(state=GeneralState.dz_one)
async def dz_one(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    with sq.connect('sq_baze/users_courses/users_courses.db') as con:
        cur = con.cursor()

        # Получаем текущий этап курса
        cur.execute("SELECT stage_course, course FROM users WHERE id = ?", (user_id,))
        course_data = cur.fetchone()  # Получаем одну строку (кортеж)
        text = message.text
        if message.text == '1':
            stage_course, course = course_data
            video = InputFile('videos/Course One/2.mp4')
            await bot.send_message(message.chat.id, 'Верно! Вы прошли на новый этап! Отправляю вам 2 урок')
            await bot.send_video(message.chat.id, video)
            stage = int(stage_course) + 1
            cur.execute("UPDATE users SET stage_course = ? WHERE id = ?", (stage, user_id))
            con.commit()  # Фиксируем изменения
            await state.finish()
        else:
            await bot.send_message(message.chat.id,'Ошибка! Попробуйте снова!')
            await state.finish()

@dp.message_handler(state=GeneralState.dz_two)
async def dz_one(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    with sq.connect('sq_baze/users_courses/users_courses.db') as con:
        cur = con.cursor()

        # Получаем текущий этап курса
        cur.execute("SELECT stage_course, course FROM users WHERE id = ?", (user_id,))
        course_data = cur.fetchone()  # Получаем одну строку (кортеж)
        text = message.text
        if message.text == '2':
            stage_course, course = course_data
            video = InputFile('videos/Course One/3.mp4')
            await bot.send_message(message.chat.id, 'Верно! Вы прошли на новый этап! Отправляю вам 3 урок')
            await bot.send_video(message.chat.id, video)
            stage = int(stage_course) + 1
            cur.execute("UPDATE users SET stage_course = ? WHERE id = ?", (stage, user_id))
            con.commit()  # Фиксируем изменения
            await state.finish()
        else:
            await bot.send_message(message.chat.id,'Ошибка! Попробуйте снова!')
            await state.finish()

@dp.message_handler(state=GeneralState.dz_three)
async def dz_one(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    with sq.connect('sq_baze/users_courses/users_courses.db') as con:
        cur = con.cursor()

        # Получаем текущий этап курса
        cur.execute("SELECT stage_course, course FROM users WHERE id = ?", (user_id,))
        course_data = cur.fetchone()  # Получаем одну строку (кортеж)
        text = message.text
        if message.text == '3':
            stage_course, course = course_data
            await bot.send_message(message.chat.id, 'Верно! Вы прошли курс! Поздравляем')
            stage = int(stage_course) + 1
            cur.execute("UPDATE users SET stage_course = ? WHERE id = ?", (stage, user_id))
            con.commit()  # Фиксируем изменения
            await state.finish()
        else:
            await bot.send_message(message.chat.id,'Ошибка! Попробуйте снова!')
            await state.finish()

@dp.message_handler(lambda message: message.text == '✍️Описание курсов')
async def opisanie(message: types.Message):

    opisanie = (
        '"Эликсир страсти" это 16 уроков и персональных практик\n\n'
        'Помогу вернуть в отношения любовь,  заботу и страсть, даже если конфликты стали нормой. Не предавая себя. Для замужних женщин, желающих снова быть любимой. От психолога и наставника 600+ женщин, которая сама прошла путь от предразводного состояния до счастливой жены с 18-летним "стажем"'
    )

    await bot.send_message(message.chat.id, opisanie)

@dp.message_handler(lambda message: message.text == '📥Получить первый урок')
async def send_one(message: types.Message):
    user_id = message.from_user.id
    with sq.connect('sq_baze/users_courses/users_courses.db') as con:
        cur = con.cursor()

        # Получаем stage_course как одно значение
        cur.execute("SELECT stage_course FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()  # Возвращает кортеж

        if result is None:
            await bot.send_message(message.chat.id, 'Пользователь не найден в базе данных.')
            return

        stage_course = result[0]  # Извлекаем значение из кортежа

        try:
            # Преобразуем stage_course в число, если это строка
            stage_course = int(stage_course)
        except ValueError:
            await bot.send_message(message.chat.id, 'Ошибка в данных курса. Попробуйте снова.')
            return

        video = InputFile('videos/Course ONE/1.mp4')
        await bot.send_message(message.chat.id, 'Высылаем вам первый урок!')
        await bot.send_video(message.chat.id, video)

        # Увеличиваем stage_course на 1
        if stage_course == 0:
            stage = stage_course + 1

            # Обновляем stage_course в базе данных
            cur.execute("UPDATE users SET stage_course = ? WHERE id = ?", (stage, user_id))
            con.commit()  # Фиксируем изменения

# Stages course
@dp.message_handler(lambda message: message.text == '🔄Этап курса')
async def courses(message: types.Message):
    user_id = message.from_user.id  # Получаем ID пользователя
    with sq.connect('sq_baze/users_courses/users_courses.db') as con:
        cur = con.cursor()

        # Проверяем, существует ли пользователь с данным ID
        cur.execute("SELECT phone FROM users WHERE id = ?", (user_id,))
        user_data = cur.fetchone()  # Получаем данные пользователя

        if user_data is None:
            await bot.send_message(message.chat.id, 'Вы не зарегистрированы. Пожалуйста, отправьте свой контакт.')
            return

        user_phone = user_data[0]  # Получаем номер телефона пользователя

        # Теперь проверяем этап курса для этого номера телефона
        cur.execute("SELECT stage_course, course FROM users WHERE phone = ?", (user_phone,))
        course_data = cur.fetchone()  # Получаем этап курса

        if course_data is None:
            await bot.send_message(message.chat.id, 'У вас нет курсов.')
        else:
            stage_course, course = course_data
            if int(stage_course) == 4:
                await bot.send_message(message.chat.id, 'Вы прошли курс!')
            else:
                stage_course = course_data[0]  # Получаем этап курса
                await bot.send_message(message.chat.id, f'Ваш этап курса: {stage_course}')

# Back
@dp.message_handler(lambda message: message.text == '🔙Назад')
async def back_reviews(message: types.Message):
    await bot.send_message(message.chat.id, 'Возвращаюсь назад', reply_markup=mk.btn_courses_dop_menu)

# Back
@dp.message_handler(lambda message: message.text == '🏠Назад в главное меню')
async def back_reviews(message: types.Message):
    await bot.send_message(message.chat.id, 'Возвращаюсь назад', reply_markup=mk.btn_general_menu)

@dp.message_handler(lambda message: message.text == '📬Обратная связь')
async def ret_svz(message: types.Message):
    gen_chat_id = '698255154'  # Замените на реальный chat_id Генерального Директора
    username = message.from_user.username

    if username:
        result_message = (
            'Клиент хочет с вами связаться!\n'
            f"Телеграмм клиента: <a href='https://t.me/{username}'>@{username}</a>\n"
        )
        # Отправляем сообщение Генеральному Директору
        await bot.send_message(gen_chat_id, result_message, parse_mode=ParseMode.HTML)
        await message.reply('Вам скоро ответят в личных сообщениях!')
    else:
        await message.reply('Чтобы сотрудник смог с вами связаться, вам необходимо ввести "Имя пользователя" в настройках Telegram.')

@dp.message_handler(lambda message: message.text == '🆘Помощь')
async def help(message: types.Message):
    await bot.send_message(message.chat.id, 'Открываю панель помощи', reply_markup=mk.btn_help_menu)

@dp.message_handler(lambda message: message.text == 'ℹ️О нас')
async def help(message: types.Message):
    await bot.send_message(message.chat.id, 'Открываю панель помощи', reply_markup=mk.btn_about_menu)

@dp.message_handler(lambda message: message.text == '🔗Вконтакт')
async def help(message: types.Message):
    url = 'https://vk.com/martynovai'
    # Send the URL first and then the message text
    await bot.send_message(message.chat.id, url, parse_mode=ParseMode.HTML)

@dp.message_handler(lambda message: message.text == '📱Телеграм')
async def help(message: types.Message):
    url = 'https://t.me/coach_innamartynova'
    # Send the URL first and then the message text
    await bot.send_message(message.chat.id, url, parse_mode=ParseMode.HTML)

@dp.message_handler(lambda message: message.text == '🌐Социальные сети')
async def help(message: types.Message):
    await bot.send_message(message.chat.id, 'Открываю панель помощи', reply_markup=mk.btn_soc_menu)

# Back
@dp.message_handler(lambda message: message.text == '🔙Назад в меню')
async def back_reviews(message: types.Message):
    await bot.send_message(message.chat.id, 'Возвращаюсь назад', reply_markup=mk.btn_about_menu)

@dp.message_handler(lambda message: message.text == '👁️Посмотреть отзывы')
async def back_reviews(message: types.Message):
    await bot.send_message(message.chat.id, 'https://t.me/otzyv_coachinnamartynova')

@dp.message_handler(lambda message: message.text == '💬Отзывы')
async def back_reviews(message: types.Message):
    await bot.send_message(message.chat.id, 'Открываю панель отзывы',reply_markup=mk.btn_reviews_menu)

@dp.message_handler(lambda message: message.text == '✍️Написать отзыв')
async def back_reviews(message: types.Message):
    await bot.send_message(message.chat.id, 'Напишите ваш отзыв')
    await GeneralState.reviews.set()

@dp.message_handler(state=GeneralState.reviews)
async def reviews_state(message: types.Message, state: FSMContext):
    text = message.text
    user_data = (message.from_user.id, message.from_user.last_name, message.from_user.first_name, text)

    with sq.connect('sq_baze/reviews/reviews.db') as con:
        cur = con.cursor()
        # Создание таблицы, если её нет
        cur.execute("""CREATE TABLE IF NOT EXISTS reviews(
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            reviews TEXT
        )""")
        cur.execute("INSERT INTO reviews (user_id, first_name, last_name, reviews) VALUES (?, ?, ?, ?)", user_data)
        con.commit()

        # Уведомляем генерального директора
        gen_chat_id = '698255154'  # Укажите реальный chat_id
        username = message.from_user.username

        if username:
            result_message = (
                f"Клиент оставил отзыв!\n\n"
                f"{text}\n"
            )
            await bot.send_message(gen_chat_id, result_message, parse_mode=ParseMode.HTML)
            await message.reply('Спасибо за отзыв!')
            await state.finish()

@dp.message_handler(lambda message: message.text in ['админ', 'Админ'])
async def admin(message: types.Message, state: FSMContext):
    user = message.from_user.id
    with sq.connect("sq_baze/admin/admin.db") as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS admins(
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            id INTEGER UNIQUE,
            last_name TEXT,
            first_name TEXT,
            admin TEXT
        )""")

        cur.execute("SELECT admin FROM admins WHERE id = ?", (user,))
        data = cur.fetchone()

        if data is None:
            # Пользователь не найден, спрашиваем пароль
            await AdminState.password_state.set()
            await bot.send_message(message.chat.id, 'Введите пароль!')
        elif data[0] == 'YES':
            # Пользователь найден и уже администратор
            await bot.send_message(message.chat.id, 'Открываю админ-панель', reply_markup=mk.btn_admin_menu)
        else:
            # Пользователь найден, но не является администратором
            await bot.send_message(message.chat.id, 'У вас нет прав администратора!')

@dp.message_handler(state=AdminState.password_state)
async def admin_password(message: types.Message, state: FSMContext):
    text = message.text
    user_id = message.from_user.id
    with sq.connect("sq_baze/admin/admin.db") as con:
        cur = con.cursor()

        if text == '':  # Если пароль правильный
            user_data = (user_id, message.from_user.last_name or '', message.from_user.first_name or '', 'YES')
            cur.execute("INSERT OR IGNORE INTO admins (id, last_name, first_name, admin) VALUES (?, ?, ?, ?)",
                        user_data)
            await bot.send_message(message.chat.id, 'Открываю админ-панель', reply_markup=mk.btn_admin_menu)
            await state.finish()
        else:
            # Если пароль неверный
            await bot.send_message(message.chat.id, 'Пароль введён неправильно!')
            await state.finish()

@dp.message_handler(lambda message: message.text == '📝Ваши отзывы')
async def reviews_Admin(message: types.Message):
    user = message.from_user.id
    with sq.connect("sq_baze/admin/admin.db") as con:
        cur = con.cursor()
        cur.execute("SELECT admin FROM admins WHERE id = ?", (user,))
        admin = cur.fetchone()
        if admin is None:
            await bot.send_message(message.chat.id, 'Вы не админ!')
        else:
            with sq.connect('sq_baze/reviews/reviews.db') as con:
                cur = con.cursor()
                # Выбираем все строки из таблицы reviews
                cur.execute("SELECT last_name, reviews FROM reviews")
                data = cur.fetchall()  # Получаем все строки результата

                if not data:
                    await bot.send_message(message.chat.id, "Отзывов пока нет.")
                    return

                # Формируем текст для отправки
                result = ""
                for row in data:
                    last_name, review = row  # Каждая строка - это кортеж
                    result += (
                        f"Имя: {last_name}\n"
                        f"Отзыв: {review}\n"
                        '---------------------------------\n'
                    )

                await bot.send_message(message.chat.id, result)

@dp.message_handler(lambda message: message.text == '🗑️Удалить отзыв')
async def delete_reviews_admin(message: types.Message):
    user = message.from_user.id
    with sq.connect("sq_baze/admin/admin.db") as con:
        cur = con.cursor()
        cur.execute("SELECT admin FROM admins WHERE id = ?", (user,))
        admin = cur.fetchone()
        if admin is None:
            await bot.send_message(message.chat.id, 'Вы не админ!')
        else:
            with sq.connect('sq_baze/reviews/reviews.db') as con:
                cur = con.cursor()
                # Выбираем все строки из таблицы reviews
                cur.execute("SELECT id, last_name, reviews FROM reviews")
                data = cur.fetchall()  # Получаем все строки результата

                if not data:
                    await bot.send_message(message.chat.id, "Отзывов пока нет.")
                    return

                # Формируем текст для отправки
                result = ""
                for row in data:
                    id, last_name, review = row  # Каждая строка - это кортеж
                    result += (
                        f'Номер отзыва: {id}\n'
                        f"Имя: {last_name}\n"
                        f"Отзыв: {review}\n"
                        '---------------------------------\n'
                    )
                await AdminState.delete.set()
                await bot.send_message(message.chat.id, result)
                await bot.send_message(message.chat.id, 'Введите номер отзыва чтобы удалить его!')

@dp.message_handler(state=AdminState.delete)
async def delete_admin(message: types.Message, state: FSMContext):
    with sq.connect('sq_baze/reviews/reviews.db') as con:
        cur = con.cursor()
        # Проверяем, есть ли номер отзыва в базе
        review_id = message.text.strip()
        cur.execute("SELECT id FROM reviews WHERE id = ?", (review_id,))
        data = cur.fetchone()

        if data is None:
            # Если отзыва с таким ID нет
            await bot.send_message(message.chat.id, "Отзыв с таким номером не найден. Проверьте и попробуйте снова.")
        else:
            # Удаляем отзыв из базы
            cur.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
            con.commit()
            await bot.send_message(message.chat.id, f"Отзыв с номером {review_id} успешно удалён.")

        # Завершаем состояние
        await state.finish()

@dp.message_handler(lambda message: message.text == '👥Пользователи')
async def users_admin(message: types.Message):
    user = message.from_user.id
    with sq.connect("sq_baze/admin/admin.db") as con:
        cur = con.cursor()
        cur.execute("SELECT admin FROM admins WHERE id = ?", (user,))
        admin = cur.fetchone()
        if admin is None:
            await bot.send_message(message.chat.id, 'Вы не админ!')
        else:
            with sq.connect("sq_baze/users/users.db") as con:
                cur = con.cursor()
                cur.execute("SELECT id, last_name, first_name, phone_number FROM users")
                data = cur.fetchall()

                if not data:
                    await bot.send_message(message.chat.id, "Пользователей пока нет.")
                    return

                result = ""
                for row in data:
                    id, last_name, first_name, phone_number = row  # Каждая строка - это кортеж
                    result += (
                        f"ID: {id}\n"
                        f"Имя: {last_name}\n"
                        f"Фамилия: {first_name}\n"
                        f"Телефон: {phone_number}\n"
                        '---------------------------------\n'
                    )

                await bot.send_message(message.chat.id, result)

@dp.message_handler(lambda message: message.text == '🤝Клиенты')
async def users_admin(message: types.Message):
    user = message.from_user.id
    with sq.connect("sq_baze/admin/admin.db") as con:
        cur = con.cursor()
        cur.execute("SELECT admin FROM admins WHERE id = ?", (user,))
        admin = cur.fetchone()
        if admin is None:
            await bot.send_message(message.chat.id, 'Вы не админ!')
        else:
            with sq.connect("sq_baze/users_courses/users_courses.db") as con:
                cur = con.cursor()
                cur.execute("SELECT id, stage_course, course, phone FROM users")
                data = cur.fetchall()

                if not data:
                    await bot.send_message(message.chat.id, "Клиентов пока нет.")
                    return

                result = ""
                for row in data:
                    id, stage_course, course, phone = row  # Каждая строка - это кортеж
                    result += (
                        f"ID: {id}\n"
                        f"Стадия курса: {stage_course}\n"
                        f"Курс: {course}\n"
                        f"Телефон: {phone}\n"
                        '---------------------------------\n'
                    )

                await bot.send_message(message.chat.id, result)

@dp.message_handler(lambda message: message.text == 'Выдать доступ к курсу')
async def back_reviews(message: types.Message, state: FSMContext):
    user = message.from_user.id
    with sq.connect("sq_baze/admin/admin.db") as con:
        cur = con.cursor()
        cur.execute("SELECT admin FROM admins WHERE id = ?", (user,))
        admin = cur.fetchone()
        if admin is None:
            await bot.send_message(message.chat.id, 'Вы не админ!')
        else:
            await bot.send_message(message.chat.id, 'Выберите курс:', reply_markup=mk.btn_course_admin_menu)

@dp.message_handler(lambda message: message.text == '❤️Курс "Эликсир страсти"')
async def back_reviews(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Выберите какую версию курса', reply_markup=mk.btn_course_dop_admin_menu)
    await AdminState.man.set()

@dp.message_handler(state=AdminState.man)
async def man_state(message: types.Message, state: FSMContext):
    text = message.text
    async with state.proxy() as data:
        data['text'] = text
        with sq.connect("sq_baze/users/users.db") as con:
            cur = con.cursor()
            cur.execute("SELECT id, last_name, first_name, phone_number FROM users")
            users_data = cur.fetchall()

            if not users_data:
                await bot.send_message(message.chat.id, "Пользователей пока нет.")
                return

            result = ""
            for row in users_data:
                id, last_name, first_name, phone_number = row
                result += (
                    f"ID: {id}\n"
                    f"Имя: {last_name}\n"
                    f"Фамилия: {first_name}\n"
                    f"Телефон: {phone_number}\n"
                    '---------------------------------\n'
                )

            await bot.send_message(message.chat.id, result)
            await bot.send_message(message.chat.id, 'Какому пользователю выдать доступ? Напишите его ID')
            await AdminState.eli_stra_one.set()


@dp.message_handler(state=AdminState.eli_stra_one)
async def eli_stra_one(message: types.Message, state: FSMContext):
    text_text = message.text
    async with state.proxy() as data:
        text = data.get('text', '').strip()  # Убираем лишние пробелы с начала и конца строки

        with sq.connect("sq_baze/users/users.db") as con:
            cur = con.cursor()
            cur.execute("SELECT phone_number FROM users WHERE id = ?", (text_text,))
            user_text = cur.fetchone()

        if user_text is None:
            await bot.send_message(message.chat.id, 'Пользователь не найден.')
            await state.finish()
            return

        # Определяем курс и соответствующее значение data_do
        data_do = None
        if text == '❤️Курс "Эликсир страсти" ПРИНЦЕССА':
            data_do = time_data_6m
        elif text == '❤️Курс "Эликсир страсти" КОРОЛЕВА':
            data_do = time_data_6m
        elif text == '❤️Курс "Эликсир страсти" ВОЛШЕБНИЦА':
            data_do = time_data_1y
        elif text == '❤️Курс "Эликсир страсти" БОГИНЯ':
            data_do = 'nav'
        else:
            await bot.send_message(message.chat.id, 'Ошибка: курс не найден.')
            await state.finish()
            return

        # Формируем кортеж пользователя
        user_data = (
        text_text, message.from_user.last_name, message.from_user.first_name, user_text[0], text, '0', current_date,
        data_do)

        # Вставляем данные в базу
        with sq.connect('sq_baze/users_courses/users_courses.db') as con:
            cur = con.cursor()
            cur.execute("INSERT INTO users (id, last_name, first_name, phone, course, stage, data_ot, data_do) VALUES(?,?,?,?,?,?,?,?)", user_data)

        await bot.send_message(message.chat.id, 'Выдали доступ!', reply_markup=mk.btn_admin_menu)
        await state.finish()


@dp.message_handler(lambda message: message.text == '🚪Выйти из админ панели')
async def back_reviews(message: types.Message):
    await bot.send_message(message.chat.id, 'Выхожу из админ-панели', reply_markup=mk.btn_general_menu)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(run_daily_task("15:23"))  # Запуск функции каждый день в 2:00
    asyncio.set_event_loop(loop)
    executor.start_polling(dp, loop=loop, skip_updates=True)
