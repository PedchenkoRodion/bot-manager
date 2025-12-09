# main.py
import telebot
import threading
import logging
import os
import sqlite3
import uuid

import database as database
import keyboards as keyboards
import student_bot
from states import UserState
from telebot import types
import config

logging.basicConfig(level=logging.ERROR)

user_states = {}
active_student_bots = {}

bot = telebot.TeleBot(config.BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_handler(message):
    database.add_user(message.from_user.id, message.from_user.username)
    user_id = message.from_user.id
    user_states[user_id] = UserState.MAIN_MENU

    welcome_text = """👋 Добро пожаловать в Teacher Bot!

Этот бот поможет учителям создавать образовательных ботов для учеников.

Возможности:
• Создание ботов для разных классов
• Добавление предметов и учебных тем
• Готовая база учебных материалов
• Управление учениками
• Дополнительные развивающие материалы

Выберите действие:"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboards.create_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data == "main_menu":
            user_states[user_id] = UserState.MAIN_MENU
            bot.edit_message_text(
                "🏠 Главное меню\n\nВыберите действие:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_main_menu()
            )
        
        elif data == "my_bots":
            bot.edit_message_text(
                "🤖 Ваши боты:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_my_bots_menu(user_id)
            )
        
        elif data == "create_bot":
            user_states[user_id] = UserState.CREATING_BOT
            bot.edit_message_text(
                "Введите название для нового бота (минимум 2 символа):\n\nОтправьте 'назад' для отмены",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu("my_bots")
            )
        
        elif data.startswith("manage_bot_"):
            bot_id = int(data.split("_")[-1])
            show_bot_management(call, bot_id)
        
        elif data.startswith("edit_token_"):
            bot_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.EDITING_TOKEN
            user_states[f"{user_id}_bot_id"] = bot_id
            
            bot_info = database.get_bot_info(bot_id)
            current_token = bot_info[3] if bot_info and bot_info[3] else "Не установлен"
            
            instruction_text = f"""🔑 Настройка API токена бота

Текущий токен: {current_token}

Для получения токена:
1. Найдите @BotFather в Telegram
2. Отправьте /newbot
3. Введите название бота
4. Введите username (должен заканчиваться на 'bot')
5. Скопируйте полученный токен

Введите новый токен (минимум 30 символов):
Отправьте 'назад' для отмены"""
            
            bot.edit_message_text(
                instruction_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu(f"manage_bot_{bot_id}"))
        
        elif data.startswith("edit_welcome_"):
            bot_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.EDITING_WELCOME
            user_states[f"{user_id}_bot_id"] = bot_id
            
            bot.edit_message_text(
                "Введите приветственное сообщение для учеников (минимум 5 символов):\n\nОтправьте 'назад' для отмены",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu(f"manage_bot_{bot_id}"))
        
        elif data.startswith("manage_classes_"):
            bot_id = int(data.split("_")[-1])
            bot.edit_message_text(
                "🏫 Управление классами:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_classes_menu(bot_id))
        
        elif data.startswith("add_class_"):
            bot_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.ADDING_CLASS
            user_states[f"{user_id}_bot_id"] = bot_id
            
            bot.edit_message_text(
                "Введите название класса (например: '1 класс'):\n\nОтправьте 'назад' для отмены",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu(f"manage_classes_{bot_id}"))
        
        elif data.startswith("class_"):
            class_id = int(data.split("_")[-1])
            bot.edit_message_text(
                "🎒 Действия с классом:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_class_menu(class_id))
        
        elif data.startswith("subjects_"):
            class_id = int(data.split("_")[-1])
            bot.edit_message_text(
                "📚 Предметы класса:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_subjects_menu(class_id))
        
        elif data.startswith("add_subject_"):
            class_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.ADDING_SUBJECT
            user_states[f"{user_id}_class_id"] = class_id
            
            bot.edit_message_text(
                "Введите название предмета (например: 'Математика'):\n\nОтправьте 'назад' для отмены",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu(f"subjects_{class_id}"))
        
        elif data.startswith("subject_"):
            subject_id = int(data.split("_")[-1])
            bot.edit_message_text(
                "📖 Действия с предметом:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_subject_menu(subject_id))
        
        elif data.startswith("topics_"):
            subject_id = int(data.split("_")[-1])
            bot.edit_message_text(
                "📝 Темы предмета:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_topics_menu(subject_id))
        
        elif data.startswith("add_topic_"):
            subject_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.ADDING_TOPIC
            user_states[f"{user_id}_subject_id"] = subject_id
            
            bot.edit_message_text(
                "Введите название темы (минимум 2 символа):\n\nОтправьте 'назад' для отмены",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu(f"topics_{subject_id}"))
        
        elif data.startswith("topic_"):
            topic_id = int(data.split("_")[-1])
            topic = database.get_topic_info(topic_id)
            if topic:
                subject_id = topic[1]
                file_info = ""
                if topic[6]:  # file_path
                    file_info = f"\n\n📎 Прикрепленный файл: {topic[7] or 'файл'}"
                bot.edit_message_text(
                    f"📖 Тема: {topic[2]}\n\nСодержание:\n{topic[3]}\n\nУровень сложности: {topic[4]}{file_info}",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_topic_menu(topic_id, subject_id))
        
        elif data.startswith("edit_topic_name_"):
            topic_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.EDITING_TOPIC_NAME
            user_states[f"{user_id}_topic_id"] = topic_id
            
            topic = database.get_topic_info(topic_id)
            if topic:
                subject_id = topic[1]
                bot.edit_message_text(
                    f"Текущее название: {topic[2]}\n\nВведите новое название темы:\n\nОтправьте 'назад' для отмены",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_back_button_menu(f"topic_{topic_id}"))
        
        elif data.startswith("edit_topic_content_"):
            topic_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.EDITING_TOPIC_CONTENT
            user_states[f"{user_id}_topic_id"] = topic_id
            
            topic = database.get_topic_info(topic_id)
            if topic:
                bot.edit_message_text(
                    f"Текущее содержание:\n{topic[3]}\n\nВведите новое содержание темы:\n\nОтправьте 'назад' для отмены",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_back_button_menu(f"topic_{topic_id}"))
        
        elif data.startswith("edit_topic_file_"):
            topic_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.EDITING_TOPIC_FILE
            user_states[f"{user_id}_topic_id"] = topic_id
            
            topic = database.get_topic_info(topic_id)
            if topic:
                current_file = f"\nТекущий файл: {topic[6] or 'нет'}" if topic[6] else ""
                bot.edit_message_text(
                    f"Отправьте файл (изображение, документ, видео) для этой темы{current_file}:\n\nОтправьте 'удалить' чтобы удалить файл\nОтправьте 'назад' для отмены",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_back_button_menu(f"topic_{topic_id}"))
        
        elif data.startswith("delete_topic_"):
            topic_id = int(data.split("_")[-1])
            topic = database.get_topic_info(topic_id)
            if topic:
                subject_id = topic[1]
                if database.delete_topic(topic_id):
                    bot.answer_callback_query(call.id, "✅ Тема удалена")
                    bot.edit_message_text(
                        "📝 Темы предмета:",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=keyboards.create_topics_menu(subject_id))
        
        elif data.startswith("edit_class_"):
            class_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.EDITING_CLASS
            user_states[f"{user_id}_class_id"] = class_id
            
            class_info = database.get_class_info(class_id)
            if class_info:
                bot.edit_message_text(
                    f"Текущее название: {class_info[2]}\nОписание: {class_info[3] or 'нет'}\n\nВведите новое название класса:\n\nОтправьте 'назад' для отмены",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_back_button_menu(f"class_{class_id}"))
        
        elif data.startswith("delete_class_"):
            class_id = int(data.split("_")[-1])
            class_info = database.get_class_info(class_id)
            if class_info:
                bot_id = class_info[1]
                if database.delete_class(class_id):
                    bot.answer_callback_query(call.id, "✅ Класс удален")
                    bot.edit_message_text(
                        "🏫 Управление классами:",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=keyboards.create_classes_menu(bot_id))
        
        elif data.startswith("edit_subject_"):
            subject_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.EDITING_SUBJECT
            user_states[f"{user_id}_subject_id"] = subject_id
            
            subject_info = database.get_subject_info(subject_id)
            if subject_info:
                bot.edit_message_text(
                    f"Текущее название: {subject_info[2]}\nОписание: {subject_info[3] or 'нет'}\n\nВведите новое название предмета:\n\nОтправьте 'назад' для отмены",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_back_button_menu(f"subject_{subject_id}"))
        
        elif data.startswith("delete_subject_"):
            subject_id = int(data.split("_")[-1])
            subject_info = database.get_subject_info(subject_id)
            if subject_info:
                class_id = subject_info[1]
                if database.delete_subject(subject_id):
                    bot.answer_callback_query(call.id, "✅ Предмет удален")
                    bot.edit_message_text(
                        "📚 Предметы класса:",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=keyboards.create_subjects_menu(class_id))
        
        elif data == "predefined_materials":
            bot.edit_message_text(
                "📚 Готовые учебные материалы:\n\nВыберите класс:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_predefined_classes_menu()
            )
        
        elif data.startswith("predefined_class_"):
            class_name = data.split("_")[2]
            bot.edit_message_text(
                f"📚 Предметы для {class_name}:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_predefined_subjects_menu(class_name)
            )
        
        elif data.startswith("predefined_subject_"):
            parts = data.split("_")
            # Исправляем парсинг - объединяем части правильно
            class_name = parts[2].replace('_', ' ')
            subject_name = parts[3].replace('_', ' ')
            
            bot.edit_message_text(
                f"📖 Темы по {subject_name} для {class_name}:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_predefined_topics_menu(class_name, subject_name)
            )
                
        elif data.startswith("view_predefined_"):
            parts = data.split("_")
            class_name = parts[2]
            subject_name = parts[3]
            topic_name = parts[4]
            
            topics = database.get_predefined_topics(class_name, subject_name)
            content = "Содержание не найдено"
            for topic in topics:
                if topic[0] == topic_name:
                    content = topic[1]
                    break
            
            bot.edit_message_text(
                f"📖 {topic_name}\n\n{content}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_predefined_topic_menu(class_name, subject_name, topic_name)
            )
        
        elif data.startswith("add_predefined_topic_"):
            parts = data.split("_")
            class_name = parts[4]
            subject_name = parts[5]
            topic_name = parts[6]
            
            # Находим bot_id из состояния пользователя
            bot_id = user_states.get(f"{user_id}_bot_id")
            if not bot_id:
                # Если bot_id не в состоянии, используем первый бот пользователя
                user_bots = database.get_user_bots(user_id)
                if user_bots:
                    bot_id = user_bots[0][0]
            
            if bot_id:
                topic_id = database.add_predefined_to_bot(bot_id, class_name, subject_name, topic_name)
                if topic_id:
                    bot.answer_callback_query(call.id, "✅ Тема добавлена в ваш бот!")
                else:
                    bot.answer_callback_query(call.id, "❌ Ошибка при добавлении темы")
            else:
                bot.answer_callback_query(call.id, "❌ Сначала создайте бот")
        
        elif data.startswith("add_predefined_"):
            class_id = int(data.split("_")[-1])
            class_info = database.get_class_info(class_id)
            if class_info:
                user_states[f"{user_id}_class_id"] = class_id
                bot.edit_message_text(
                    "📚 Готовые учебные материалы:\n\nВыберите класс:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_predefined_classes_menu()
                )
        
        elif data.startswith("delete_bot_"):
            bot_id = int(data.split("_")[-1])
            if database.delete_bot(bot_id):
                if bot_id in active_student_bots:
                    try:
                        active_student_bots[bot_id].stop_polling()
                    except:
                        pass
                    del active_student_bots[bot_id]
                bot.answer_callback_query(call.id, "✅ Бот удален")
                bot.edit_message_text(
                    "🤖 Ваши боты:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_my_bots_menu(user_id)
                )
        
        elif data.startswith("prev_topics_"):
            parts = data.split("_")
            subject_id = int(parts[2])
            page = int(parts[3])
            bot.edit_message_text(
                "📝 Темы предмета:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_topics_menu(subject_id, page)
            )
        
        elif data.startswith("next_topics_"):
            parts = data.split("_")
            subject_id = int(parts[2])
            page = int(parts[3])
            bot.edit_message_text(
                "📝 Темы предмета:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_topics_menu(subject_id, page)
            )
        
        elif data.startswith("manage_students_"):
            bot_id = int(data.split("_")[-1])
            bot.edit_message_text(
                "👥 Управление учениками:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_students_management_menu(bot_id)
            )
        
        elif data.startswith("add_student_"):
            bot_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.ADDING_STUDENT
            user_states[f"{user_id}_bot_id"] = bot_id
            
            bot.edit_message_text(
                "Введите username ученика (например: @username):\n\nОтправьте 'назад' для отмены",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu(f"manage_students_{bot_id}"))
        
        elif data.startswith("list_students_"):
            bot_id = int(data.split("_")[-1])
            students = database.get_bot_students(bot_id)
            
            if not students:
                bot.edit_message_text(
                    "В вашем боте пока нет учеников.",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_back_button_menu(f"manage_students_{bot_id}"))
                return
            
            students_text = "📋 Список ваших учеников:\n\n"
            for student_id, username, class_name, added_at in students:
                students_text += f"👤 @{username}\n🏫 Класс: {class_name}\n📅 Добавлен: {added_at[:10]}\n\n"
            
            bot.edit_message_text(
                students_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu(f"manage_students_{bot_id}"))
        
        elif data.startswith("remove_student_"):
            bot_id = int(data.split("_")[-1])
            students = database.get_bot_students(bot_id)
            
            if not students:
                bot.answer_callback_query(call.id, "Нет учеников для удаления")
                return
            
            bot.edit_message_text(
                "Выберите ученика для удаления:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_remove_student_menu(students, bot_id))
        
        elif data.startswith("confirm_remove_"):
            parts = data.split("_")
            bot_id = int(parts[2])
            username = parts[3]
            
            bot.edit_message_text(
                f"Вы уверены, что хотите удалить ученика @{username}?",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_confirm_remove_menu(bot_id, username))
        
        elif data.startswith("do_remove_"):
            parts = data.split("_")
            bot_id = int(parts[2])
            username = parts[3]
            
            if database.remove_student(bot_id, username):
                bot.answer_callback_query(call.id, "✅ Ученик удален")
                bot.edit_message_text(
                    "👥 Управление учениками:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_students_management_menu(bot_id))
            else:
                bot.answer_callback_query(call.id, "❌ Ошибка при удалении")
        
        elif data.startswith("additional_materials_"):
            bot_id = int(data.split("_")[-1])
            bot.edit_message_text(
                "📚 Дополнительные материалы:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_additional_materials_menu(bot_id))
        
        elif data.startswith("add_material_"):
            bot_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.ADDING_MATERIAL_CLASS
            user_states[f"{user_id}_bot_id"] = bot_id
            
            classes = database.get_bot_classes(bot_id)
            if not classes:
                bot.answer_callback_query(call.id, "Сначала создайте классы")
                return
            
            bot.edit_message_text(
                "Выберите класс для дополнительного материала:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_class_selection_menu(classes, "select_class_material", bot_id))
        
        elif data.startswith("select_class_material_"):
            class_id = int(data.split("_")[-1])
            user_states[user_id] = UserState.ADDING_MATERIAL_TITLE
            user_states[f"{user_id}_class_id"] = class_id
            
            bot.edit_message_text(
                "Введите название дополнительного материала:\n\nОтправьте 'назад' для отмены",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu(f"additional_materials_{user_states.get(f'{user_id}_bot_id')}"))
        
        elif data.startswith("list_materials_"):
            bot_id = int(data.split("_")[-1])
            materials = database.get_additional_materials(bot_id)
            
            if not materials:
                bot.edit_message_text(
                    "Дополнительных материалов пока нет.",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_back_button_menu(f"additional_materials_{bot_id}"))
                return
            
            bot.edit_message_text(
                "📚 Дополнительные материалы:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_materials_list_menu(materials, bot_id))
        
        elif data.startswith("view_material_"):
            material_id = int(data.split("_")[-1])
            material = database.get_additional_material(material_id)
            
            if material:
                file_info = ""
                if material[6]:  # file_path
                    file_info = f"\n\n📎 Прикрепленный файл: {material[7] or 'файл'}"
                
                class_info = database.get_class_info(material[2])
                class_name = class_info[2] if class_info else "неизвестный класс"
                
                text = f"📚 {material[3]}\n\n🏫 Класс: {class_name}\n"
                if material[4]:  # description
                    text += f"📝 Описание: {material[4]}\n"
                text += f"\n{material[5]}{file_info}"
                
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_material_menu(material_id, material[1]))
        
        elif data.startswith("delete_material_"):
            material_id = int(data.split("_")[-1])
            material = database.get_additional_material(material_id)
            
            if material and database.delete_additional_material(material_id):
                bot.answer_callback_query(call.id, "✅ Материал удален")
                bot.edit_message_text(
                    "📚 Дополнительные материалы:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_additional_materials_menu(material[1]))
        
        elif data.startswith("assign_student_class_"):
            class_id = int(data.split("_")[-1])
            bot_id = user_states.get(f"{user_id}_bot_id")
            username = user_states.get(f"{user_id}_student_username")
            
            if not bot_id or not username:
                bot.answer_callback_query(call.id, "❌ Ошибка: данные не найдены")
                return
            
            if database.add_student_by_username(bot_id, username, class_id, user_id):
                bot.answer_callback_query(call.id, f"✅ Ученик @{username} добавлен!")
                
                # Отправляем приветственное сообщение ученику через студенческий бот
                if bot_id in active_student_bots:
                    try:
                        student_bot_instance = active_student_bots[bot_id]
                        class_info = database.get_class_info(class_id)
                        class_name = class_info[2] if class_info else "класс"
                        
                        # Ищем ID ученика по username
                        conn = sqlite3.connect(database.DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("SELECT tg_id FROM users WHERE username = ?", (username,))
                        result = cursor.fetchone()
                        conn.close()
                        
                        if result:
                            student_tg_id = result[0]
                            welcome_message = f"👋 Добро пожаловать в обучающий бот!\n\nВы были добавлены в класс: {class_name}\n\nИспользуйте команду /start для начала работы!"
                            try:
                                student_bot_instance.send_message(student_tg_id, welcome_message)
                            except Exception as e:
                                logging.error(f"Ошибка отправки сообщения ученику {username}: {e}")
                        
                    except Exception as e:
                        logging.error(f"Ошибка при отправке приветствия: {e}")
                
                bot.edit_message_text(
                    f"✅ Ученик @{username} успешно добавлен в класс!",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_back_button_menu(f"manage_students_{bot_id}"))
            else:
                bot.answer_callback_query(call.id, "❌ Ошибка: ученик уже существует или произошла ошибка")
            
            user_states[user_id] = UserState.BOT_MENU
            # Очищаем временные данные
            if f"{user_id}_student_username" in user_states:
                del user_states[f"{user_id}_student_username"]
    
        elif call.data == "skip_material_file":
            user_id = call.from_user.id
            bot_id = user_states.get(f"{user_id}_bot_id")
            class_id = user_states.get(f"{user_id}_class_id")
            title = user_states.get(f"{user_id}_material_title")
            description = user_states.get(f"{user_id}_material_description")
            content = user_states.get(f"{user_id}_material_content")
            
            material_id = database.add_additional_material(bot_id, class_id, title, description, content)
            
            if material_id:
                bot.answer_callback_query(call.id, "✅ Материал добавлен!")
                bot.edit_message_text(
                    f"✅ Материал '{title}' успешно добавлен!",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=keyboards.create_additional_materials_menu(bot_id))
            else:
                bot.answer_callback_query(call.id, "❌ Ошибка при добавлении материала")
            
            user_states[user_id] = UserState.BOT_MENU
            # Очищаем временные данные
            for key in [f"{user_id}_material_title", f"{user_id}_material_description", f"{user_id}_material_content"]:
                if key in user_states:
                    del user_states[key]

    except Exception as e:
        logging.error(f"Callback error: {str(e)}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def show_bot_management(call, bot_id):
    bot_info = database.get_bot_info(bot_id)
    if not bot_info:
        bot.answer_callback_query(call.id, "Бот не найден")
        return
    
    bot_name = bot_info[2]
    bot_token = bot_info[3] if bot_info[3] else "Не установлен"
    welcome_message = bot_info[4]
    
    management_text = f"""⚙️ Управление ботом: {bot_name}

🔑 Токен API: {'✅ Установлен' if bot_token != 'Не установлен' else '❌ Не установлен'}
👋 Приветствие: {welcome_message[:50]}{'...' if len(welcome_message) > 50 else ''}

Выберите действие для настройки:"""
    
    bot.edit_message_text(
        management_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.create_bot_management_menu(bot_id)
    )

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)
    text = message.text.strip()
    
    if user_state == UserState.CREATING_BOT:
        if text.lower() == 'назад':
            user_states[user_id] = UserState.MAIN_MENU
            bot.send_message(
                message.chat.id,
                "❌ Создание бота отменено",
                reply_markup=keyboards.create_main_menu())
            return
            
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Название бота должно содержать не менее 2 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        bot_id = database.create_teacher_bot(user_id, text)
        if not bot_id:
            bot.send_message(message.chat.id, "❌ Ошибка при создании бота")
            return
            
        user_states[user_id] = UserState.BOT_MENU
        
        bot.send_message(
            message.chat.id,
            f"✅ Бот '{text}' успешно создан!\n\nТеперь настройте его:",
            reply_markup=keyboards.create_bot_management_menu(bot_id))
    
    elif user_state == UserState.EDITING_TOKEN:
        bot_id = user_states.get(f"{user_id}_bot_id")
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Изменение токена отменено",
                reply_markup=keyboards.create_bot_management_menu(bot_id))
            return
            
        if len(text) < 30:
            bot.send_message(message.chat.id, "❌ Токен должен содержать не менее 30 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        bot_username = database.update_bot_token(bot_id, text)
        user_states[user_id] = UserState.BOT_MENU
        
        if bot_username:
            bot.send_message(
                message.chat.id,
                f"✅ Токен успешно обновлен! Бот: @{bot_username}",
                reply_markup=keyboards.create_bot_management_menu(bot_id))
            
            # Запускаем студенческий бот
            if bot_id in active_student_bots:
                try:
                    active_student_bots[bot_id].stop_polling()
                except:
                    pass
            
            bot_info = database.get_bot_info(bot_id)
            welcome_message = bot_info[4] if bot_info else "Добро пожаловать в обучающий бот!"
            threading.Thread(target=student_bot.run_student_bot, args=(bot_id, text, welcome_message), daemon=True).start()
            active_student_bots[bot_id] = telebot.TeleBot(text)
        else:
            bot.send_message(
                message.chat.id,
                "❌ Неверный токен",
                reply_markup=keyboards.create_bot_management_menu(bot_id))
    
    elif user_state == UserState.EDITING_WELCOME:
        bot_id = user_states.get(f"{user_id}_bot_id")
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Изменение приветствия отменено",
                reply_markup=keyboards.create_bot_management_menu(bot_id))
            return
            
        if len(text) < 5:
            bot.send_message(message.chat.id, "❌ Приветствие должно содержать не менее 5 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        if database.update_welcome_message(bot_id, text):
            bot.send_message(
                message.chat.id,
                "✅ Приветственное сообщение обновлено!",
                reply_markup=keyboards.create_bot_management_menu(bot_id))
            user_states[user_id] = UserState.BOT_MENU
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при обновлении сообщения")
    
    elif user_state == UserState.ADDING_CLASS:
        bot_id = user_states.get(f"{user_id}_bot_id")
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Добавление класса отменено",
                reply_markup=keyboards.create_bot_management_menu(bot_id))
            return
            
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Название класса должно содержать не менее 2 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        class_id = database.create_class(bot_id, text)
        if not class_id:
            bot.send_message(message.chat.id, "❌ Ошибка при создании класса")
            return
            
        bot.send_message(
            message.chat.id,
            f"✅ Класс '{text}' создан!",
            reply_markup=keyboards.create_classes_menu(bot_id))
        user_states[user_id] = UserState.BOT_MENU
    
    elif user_state == UserState.EDITING_CLASS:
        class_id = user_states.get(f"{user_id}_class_id")
        class_info = database.get_class_info(class_id)
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Изменение класса отменено",
                reply_markup=keyboards.create_class_menu(class_id))
            return
            
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Название класса должно содержать не менее 2 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        if database.update_class_name(class_id, text):
            bot.send_message(
                message.chat.id,
                f"✅ Название класса изменено на '{text}'!",
                reply_markup=keyboards.create_class_menu(class_id))
            user_states[user_id] = UserState.BOT_MENU
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при изменении класса")
    
    elif user_state == UserState.ADDING_SUBJECT:
        class_id = user_states.get(f"{user_id}_class_id")
        class_info = database.get_class_info(class_id)
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Добавление предмета отменено",
                reply_markup=keyboards.create_subjects_menu(class_id))
            return
            
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Название предмета должно содержать не менее 2 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        subject_id = database.create_subject(class_id, text)
        if not subject_id:
            bot.send_message(message.chat.id, "❌ Ошибка при создании предмета")
            return
            
        bot.send_message(
            message.chat.id,
            f"✅ Предмет '{text}' создан!",
            reply_markup=keyboards.create_subjects_menu(class_id))
        user_states[user_id] = UserState.BOT_MENU
    
    elif user_state == UserState.EDITING_SUBJECT:
        subject_id = user_states.get(f"{user_id}_subject_id")
        subject_info = database.get_subject_info(subject_id)
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Изменение предмета отменено",
                reply_markup=keyboards.create_subject_menu(subject_id))
            return
            
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Название предмета должно содержать не менее 2 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        if database.update_subject_name(subject_id, text):
            bot.send_message(
                message.chat.id,
                f"✅ Название предмета изменено на '{text}'!",
                reply_markup=keyboards.create_subject_menu(subject_id))
            user_states[user_id] = UserState.BOT_MENU
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при изменении предмета")
    
    elif user_state == UserState.ADDING_TOPIC:
        subject_id = user_states.get(f"{user_id}_subject_id")
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Добавление темы отменено",
                reply_markup=keyboards.create_topics_menu(subject_id))
            return
            
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Название темы должно содержать не менее 2 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        user_states[f"{user_id}_topic_name"] = text
        user_states[user_id] = UserState.EDITING_TOPIC_CONTENT
        
        bot.send_message(
            message.chat.id,
            "Введите содержание темы:\n\nОтправьте 'назад' для отмены")
    
    elif user_state == UserState.EDITING_TOPIC_NAME:
        topic_id = user_states.get(f"{user_id}_topic_id")
        topic = database.get_topic_info(topic_id)
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            if topic:
                bot.send_message(
                    message.chat.id,
                    "❌ Изменение названия отменено",
                    reply_markup=keyboards.create_topic_menu(topic_id, topic[1]))
            return
            
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Название темы должно содержать не менее 2 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
            
        # Обновляем только название темы
        if database.update_topic(topic_id, name=text):
            bot.send_message(
                message.chat.id,
                f"✅ Название темы изменено на '{text}'!",
                reply_markup=keyboards.create_topic_menu(topic_id, topic[1]))
            user_states[user_id] = UserState.BOT_MENU
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при изменении темы")
    
    elif user_state == UserState.EDITING_TOPIC_CONTENT:
        if f"{user_id}_topic_id" in user_states:  # ИСПРАВЛЕНИЕ: проверяем наличие ключа
            # Редактирование существующей темы
            topic_id = user_states.get(f"{user_id}_topic_id")
            topic = database.get_topic_info(topic_id)
            
            if text.lower() == 'назад':
                user_states[user_id] = UserState.BOT_MENU
                if topic:
                    bot.send_message(
                        message.chat.id,
                        "❌ Изменение содержания отменено",
                        reply_markup=keyboards.create_topic_menu(topic_id, topic[1]))
                return
                
            if len(text) < 5:
                bot.send_message(message.chat.id, "❌ Содержание темы должно содержать не менее 5 символов. Попробуйте снова или отправьте 'назад' для отмены")
                return
                
            # Обновляем содержание темы
            if database.update_topic(topic_id, content=text):
                bot.send_message(
                    message.chat.id,
                    "✅ Содержание темы обновлено!",
                    reply_markup=keyboards.create_topic_menu(topic_id, topic[1]))
                user_states[user_id] = UserState.BOT_MENU
            else:
                bot.send_message(message.chat.id, "❌ Ошибка при обновлении темы")
        else:
            # Создание новой темы
            subject_id = user_states.get(f"{user_id}_subject_id")
            topic_name = user_states.get(f"{user_id}_topic_name")

            if not subject_id or not topic_name:
                bot.send_message(message.chat.id, "❌ Ошибка: данные темы не найдены. Попробуйте снова.")
                user_states[user_id] = UserState.BOT_MENU
                return
            
            if text.lower() == 'назад':
                user_states[user_id] = UserState.ADDING_TOPIC
                bot.send_message(
                    message.chat.id,
                    "❌ Добавление темы отменено\nВведите название темы:")
                return
                
            if len(text) < 5:
                bot.send_message(message.chat.id, "❌ Содержание темы должно содержать не менее 5 символов. Попробуйте снова или отправьте 'назад' для отмены")
                return
                
            topic_id = database.create_topic(subject_id, topic_name, text)
            if not topic_id:
                bot.send_message(message.chat.id, "❌ Ошибка при создании темы")
                return
                
            bot.send_message(
                message.chat.id,
                f"✅ Тема '{topic_name}' создана!",
                reply_markup=keyboards.create_topics_menu(subject_id))
            user_states[user_id] = UserState.BOT_MENU
            
            # Очищаем временные данные
            for key in [f"{user_id}_topic_name"]:
                if key in user_states:
                    del user_states[key]
    
    elif user_state == UserState.ADDING_STUDENT:
        bot_id = user_states.get(f"{user_id}_bot_id")
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Добавление ученика отменено",
                reply_markup=keyboards.create_students_management_menu(bot_id))
            return
        
        # Проверяем формат username
        if not text.startswith('@'):
            bot.send_message(message.chat.id, "❌ Username должен начинаться с @ (например: @username). Попробуйте снова или отправьте 'назад' для отмены")
            return
        
        username = text[1:]  # Убираем @
        user_states[f"{user_id}_student_username"] = username
        user_states[user_id] = UserState.ADDING_STUDENT_CLASS
        
        # Получаем классы для выбора
        classes = database.get_bot_classes(bot_id)
        if not classes:
            bot.send_message(message.chat.id, "❌ Сначала создайте классы")
            user_states[user_id] = UserState.BOT_MENU
            return
        
        bot.send_message(
            message.chat.id,
            f"Выберите класс для ученика @{username}:",
            reply_markup=keyboards.create_class_selection_menu(classes, "assign_student_class", bot_id))
    
    elif user_state == UserState.ADDING_MATERIAL_TITLE:
        bot_id = user_states.get(f"{user_id}_bot_id")
        class_id = user_states.get(f"{user_id}_class_id")
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.BOT_MENU
            bot.send_message(
                message.chat.id,
                "❌ Добавление материала отменено",
                reply_markup=keyboards.create_additional_materials_menu(bot_id))
            return
        
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Название материала должно содержать не менее 2 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
        
        user_states[f"{user_id}_material_title"] = text
        user_states[user_id] = UserState.ADDING_MATERIAL_DESCRIPTION
        
        bot.send_message(
            message.chat.id,
            "Введите описание материала (или '-' чтобы пропустить):\n\nОтправьте 'назад' для отмены")
    
    elif user_state == UserState.ADDING_MATERIAL_DESCRIPTION:
        bot_id = user_states.get(f"{user_id}_bot_id")
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.ADDING_MATERIAL_TITLE
            bot.send_message(
                message.chat.id,
                "❌ Ввод описания отменен\nВведите название материала:")
            return
        
        description = None if text == '-' else text
        user_states[f"{user_id}_material_description"] = description
        user_states[user_id] = UserState.ADDING_MATERIAL_CONTENT
        
        bot.send_message(
            message.chat.id,
            "Введите содержание материала:\n\nОтправьте 'назад' для отмены")
    
    elif user_state == UserState.ADDING_MATERIAL_CONTENT:
        bot_id = user_states.get(f"{user_id}_bot_id")
        class_id = user_states.get(f"{user_id}_class_id")
        
        if text.lower() == 'назад':
            user_states[user_id] = UserState.ADDING_MATERIAL_DESCRIPTION
            bot.send_message(
                message.chat.id,
                "❌ Ввод содержания отменен\nВведите описание материала:")
            return
        
        if len(text) < 5:
            bot.send_message(message.chat.id, "❌ Содержание материала должно содержать не менее 5 символов. Попробуйте снова или отправьте 'назад' для отмены")
            return
        
        user_states[f"{user_id}_material_content"] = text
        user_states[user_id] = UserState.ADDING_MATERIAL_FILE
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⏩ Пропустить добавление файла", callback_data="skip_material_file"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_material_content"))
        
        bot.send_message(
            message.chat.id,
            "Отправьте файл (изображение, документ, видео) для материала или нажмите 'Пропустить':",
            reply_markup=markup)
    
    else:
        bot.send_message(
            message.chat.id,
            "Используйте кнопки меню для навигации:",
            reply_markup=keyboards.create_main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "skip_material_file")
def skip_material_file_handler(call):
    user_id = call.from_user.id
    bot_id = user_states.get(f"{user_id}_bot_id")
    class_id = user_states.get(f"{user_id}_class_id")
    title = user_states.get(f"{user_id}_material_title")
    description = user_states.get(f"{user_id}_material_description")
    content = user_states.get(f"{user_id}_material_content")
    
    material_id = database.add_additional_material(bot_id, class_id, title, description, content)
    
    if material_id:
        bot.answer_callback_query(call.id, "✅ Материал добавлен!")
        bot.edit_message_text(
            f"✅ Материал '{title}' успешно добавлен!",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.create_back_button_menu(f"additional_materials_{bot_id}"))
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка при добавлении материала")
    
    user_states[user_id] = UserState.BOT_MENU
    # Очищаем временные данные
    for key in [f"{user_id}_material_title", f"{user_id}_material_description", f"{user_id}_material_content"]:
        if key in user_states:
            del user_states[key]

@bot.callback_query_handler(func=lambda call: call.data == "back_to_material_content")
def back_to_material_content_handler(call):
    user_id = call.from_user.id
    user_states[user_id] = UserState.ADDING_MATERIAL_CONTENT
    bot.edit_message_text(
        "Введите содержание материала:\n\nОтправьте 'назад' для отмены",
        call.message.chat.id,
        call.message.message_id)

# Обработчики файлов для тем
@bot.message_handler(content_types=['photo', 'document', 'video'], 
                    func=lambda message: user_states.get(message.from_user.id) == UserState.EDITING_TOPIC_FILE)
def handle_topic_file(message):
    user_id = message.from_user.id
    topic_id = user_states.get(f"{user_id}_topic_id")
    topic = database.get_topic_info(topic_id)
    
    if not topic:
        bot.send_message(message.chat.id, "❌ Тема не найдена")
        return
    
    # Удаляем старый файл если есть
    old_file_path = topic[6]
    if old_file_path and os.path.exists(old_file_path):
        try:
            os.remove(old_file_path)
        except Exception as e:
            logging.error(f"Ошибка при удалении старого файла: {e}")
    
    # Создаем папку для файлов если нет
    if not os.path.exists("topic_files"):
        os.makedirs("topic_files")
    
    file_info = None
    file_type = None
    
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_type = "image"
    elif message.document:
        file_info = bot.get_file(message.document.file_id)
        file_type = message.document.mime_type or "document"
    elif message.video:
        file_info = bot.get_file(message.video.file_id)
        file_type = "video"
    
    if file_info:
        downloaded_file = bot.download_file(file_info.file_path)
        file_extension = file_info.file_path.split('.')[-1] if '.' in file_info.file_path else 'file'
        file_path = f"topic_files/{uuid.uuid4().hex}.{file_extension}"
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        if database.update_topic(topic_id, file_path=file_path, file_type=file_type):
            bot.send_message(
                message.chat.id,
                f"✅ Файл успешно добавлен к теме!",
                reply_markup=keyboards.create_topic_menu(topic_id, topic[1]))
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при добавлении файла")
        
        user_states[user_id] = UserState.BOT_MENU

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == UserState.EDITING_TOPIC_FILE and message.text)
def handle_topic_file_text(message):
    user_id = message.from_user.id
    text = message.text.strip().lower()
    topic_id = user_states.get(f"{user_id}_topic_id")
    topic = database.get_topic_info(topic_id)
    
    if not topic:
        bot.send_message(message.chat.id, "❌ Тема не найдена")
        return
    
    if text == 'назад':
        user_states[user_id] = UserState.BOT_MENU
        bot.send_message(
            message.chat.id,
            "❌ Добавление файла отменено",
            reply_markup=keyboards.create_topic_menu(topic_id, topic[1]))
        return
    
    elif text == 'удалить':
        old_file_path = topic[6]
        if old_file_path and os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except Exception as e:
                logging.error(f"Ошибка при удалении файла: {e}")

        # ИСПРАВЛЕНИЕ: правильно обновляем запись в базе данных
        if database.update_topic(topic_id, file_path=None, file_type=None):
            bot.send_message(
                message.chat.id,
                "✅ Файл удален из темы!",
                reply_markup=keyboards.create_topic_menu(topic_id, topic[1]))
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при удалении файла")
        
        user_states[user_id] = UserState.BOT_MENU
    else:
        bot.send_message(message.chat.id, "❌ Некорректная команда. Отправьте файл, 'удалить' или 'назад'")
# Обработчики файлов для дополнительных материалов
@bot.message_handler(content_types=['photo', 'document', 'video'], 
                    func=lambda message: user_states.get(message.from_user.id) == UserState.ADDING_MATERIAL_FILE)
def handle_material_file(message):
    user_id = message.from_user.id
    bot_id = user_states.get(f"{user_id}_bot_id")
    class_id = user_states.get(f"{user_id}_class_id")
    title = user_states.get(f"{user_id}_material_title")
    description = user_states.get(f"{user_id}_material_description")
    content = user_states.get(f"{user_id}_material_content")
    
    # Создаем папку для файлов если нет
    if not os.path.exists("material_files"):
        os.makedirs("material_files")
    
    file_info = None
    file_type = None
    
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_type = "image"
    elif message.document:
        file_info = bot.get_file(message.document.file_id)
        file_type = message.document.mime_type or "document"
    elif message.video:
        file_info = bot.get_file(message.video.file_id)
        file_type = "video"
    
    if file_info:
        downloaded_file = bot.download_file(file_info.file_path)
        file_extension = file_info.file_path.split('.')[-1] if '.' in file_info.file_path else 'file'
        file_path = f"material_files/{uuid.uuid4().hex}.{file_extension}"
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        material_id = database.add_additional_material(bot_id, class_id, title, description, content, file_path, file_type)
        
        if material_id:
            bot.send_message(
                message.chat.id,
                f"✅ Материал '{title}' успешно добавлен с файлом!",
                reply_markup=keyboards.create_back_button_menu(f"additional_materials_{bot_id}"))
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при добавлении материала")
        
        user_states[user_id] = UserState.BOT_MENU
        # Очищаем временные данные
        for key in [f"{user_id}_material_title", f"{user_id}_material_description", f"{user_id}_material_content"]:
            if key in user_states:
                del user_states[key]

if __name__ == "__main__":
    print("Инициализация базы данных...")
    database.init_database()
    print("База данных готова!")
    
    print(f"Бот-менеджер запущен! Токен: {config.BOT_TOKEN}")
    
    # Запускаем существующие студенческие боты
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, bot_token, welcome_message FROM teacher_bots WHERE bot_token IS NOT NULL AND is_running = 1")
    bots = cursor.fetchall()
    conn.close()
    
    for bot_id, bot_token, welcome_message in bots:
        threading.Thread(target=student_bot.run_student_bot, args=(bot_id, bot_token, welcome_message), daemon=True).start()
        active_student_bots[bot_id] = telebot.TeleBot(bot_token)
        print(f"Запущен студенческий бот ID: {bot_id}")
    
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")