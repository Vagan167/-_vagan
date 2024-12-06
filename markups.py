from idlelib.pyparse import trans

from Tools.demo.life import keyloop
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from invoke import Result

from pythonProject.main import buy_courses

btn_general_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_courses_dop_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_open_main = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_open_course_main = ReplyKeyboardMarkup(resize_keyboard=True)
btn_buy_course_main = ReplyKeyboardMarkup(resize_keyboard=True)
btn_help_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_about_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_soc_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_reviews_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_admin_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_buy_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_course_admin_menu = ReplyKeyboardMarkup(resize_keyboard=True)
btn_course_dop_admin_menu = ReplyKeyboardMarkup(resize_keyboard=True)

btn_send_menu = InlineKeyboardMarkup()


btn_send_pok = InlineKeyboardButton("Вы потверждаете покупку?", url="https://algoritm23.net/")

btn_courses = KeyboardButton('📝Мои курсы')
btn_courses_dop = KeyboardButton('📚Отправить домашнее задание')

btn_courses_dop_stage = KeyboardButton('🔄Этап курса')

btn_back_course = KeyboardButton('🏠Назад в главное меню')
btn_back_course_next = KeyboardButton('🔙Назад')
btn_back_soc = KeyboardButton('🔙Назад в меню')
btn_back_admin = KeyboardButton('🚪Выйти из админ панели')
btn_back_buy = KeyboardButton('🔙Вернуться')

btn_buy_courses = KeyboardButton('🛒Купить курсы')

btn_buy_price = KeyboardButton('💰Цена')

btn_buy = KeyboardButton('💳Покупка курсов')

btn_buy_information = KeyboardButton('✍️Описание курсов')

btn_course_otn_1 = KeyboardButton('❤️Купить курс "Эликсир страсти" ПРИНЦЕССА')
btn_course_otn_2 = KeyboardButton('❤️Купить курс "Эликсир страсти" КОРОЛЕВА')
btn_course_otn_3 = KeyboardButton('❤️Купить курс "Эликсир страсти" ВОЛШЕБНИЦА')
btn_course_otn_4 = KeyboardButton('❤️Купить курс "Эликсир страсти" БОГИНЯ')

btn_course_one = KeyboardButton('✨Курс "Эликсир страсти"')

btn_one_course = KeyboardButton('📥Получить первый урок')

btn_send = KeyboardButton('Отправить номер телефона', request_contact=True)

obr_svz = KeyboardButton('📬Обратная связь')

btn_help = KeyboardButton('🆘Помощь')

btn_about = KeyboardButton('ℹ️О нас')
btn_soc = KeyboardButton('🌐Социальные сети')

btn_vk = KeyboardButton('🔗Вконтакт')
btn_telegram = KeyboardButton('📱Телеграм')

btn_reviews = KeyboardButton('💬Отзывы')

btn_show_reviews = KeyboardButton('👁️Посмотреть отзывы')

btn_write_reviews = KeyboardButton('✍️Написать отзыв')

btn_admin_show_reviews = KeyboardButton('📝Ваши отзывы')
btn_Admin_delete_reviews = KeyboardButton('🗑️Удалить отзыв')
btn_Admin_show_users = KeyboardButton('👥Пользователи')
btn_Admin_show_client = KeyboardButton('🤝Клиенты')
btn_dobav_admin = KeyboardButton('Выдать доступ к курсу')

btn_admin_course = KeyboardButton('❤️Курс "Эликсир страсти"')

btn_course_otn_1_admin = KeyboardButton('❤️Курс "Эликсир страсти" ПРИНЦЕССА')
btn_course_otn_2_admin = KeyboardButton('❤️Курс "Эликсир страсти" КОРОЛЕВА')
btn_course_otn_3_admin = KeyboardButton('❤️Курс "Эликсир страсти" ВОЛШЕБНИЦА')
btn_course_otn_4_admin = KeyboardButton('❤️Курс "Эликсир страсти" БОГИНЯ')

btn_buy_menu.row(btn_course_otn_1, btn_course_otn_2, btn_course_otn_3, btn_course_otn_4)
btn_buy_menu.row(btn_back_buy)

btn_open_course_main.row(btn_courses_dop, btn_courses_dop_stage, btn_one_course)
btn_open_course_main.row(btn_back_course_next)

btn_open_main.row(btn_send)

btn_general_menu.row(btn_buy_courses, btn_about)
btn_general_menu.row(btn_courses, btn_help)

btn_courses_dop_menu.row(btn_course_one)
btn_courses_dop_menu.row(btn_back_course)

btn_buy_course_main.row( btn_buy_price, btn_buy_information)
btn_buy_course_main.row(btn_buy)
btn_buy_course_main.row(btn_back_course)

btn_help_menu.row(obr_svz)
btn_help_menu.row(btn_back_course)

btn_about_menu.row(btn_soc,btn_reviews)
btn_about_menu.row(btn_back_course)

btn_soc_menu.row(btn_vk,btn_telegram)
btn_soc_menu.row(btn_back_soc)

btn_reviews_menu.row(btn_show_reviews, btn_write_reviews)
btn_reviews_menu.row(btn_back_soc)

btn_admin_menu.row(btn_admin_show_reviews, btn_Admin_delete_reviews)
btn_admin_menu.row(btn_Admin_show_users, btn_Admin_show_client)
btn_admin_menu.row(btn_dobav_admin)
btn_admin_menu.row(btn_back_admin)

btn_course_admin_menu.row(btn_admin_course)

btn_course_dop_admin_menu.row(btn_course_otn_1_admin, btn_course_otn_2_admin)
btn_course_dop_admin_menu.row(btn_course_otn_3_admin, btn_course_otn_4_admin)

btn_send_menu.row(btn_send_pok)