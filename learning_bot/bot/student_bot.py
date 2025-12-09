# student_bot.py
import sqlite3
import telebot
import logging
import os

from telebot import types

from telebot import apihelper


import database as database
import keyboards as keyboards
from states import StudentState

# Глобальный словарь для хранения ID сообщений тем
student_topic_messages = {}

def run_student_bot(bot_id, bot_token, welcome_message):
    student_bot = telebot.TeleBot(bot_token)
    student_states = {}
    
    @student_bot.message_handler(commands=['start'])
    def student_start_handler(message):
        database.add_user(message.from_user.id, message.from_user.username)
        user_id = message.from_user.id
        student_states[user_id] = StudentState.MAIN_MENU
        
        # Проверяем, зарегистрирован ли ученик в боте
        username = message.from_user.username
        if not username:
            student_bot.send_message(
                message.chat.id,
                "❌ Для использования бота необходимо установить username в настройках Telegram.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        
        student_info = database.get_student_by_username(bot_id, username)
        
        if student_info:
            # Ученик зарегистрирован, показываем основное меню
            class_id, class_name = student_info
            welcome_text = f"{welcome_message}\n\n🏫 Ваш класс: {class_name}"
            
            # Сохраняем класс ученика
            database.set_student_class(user_id, bot_id, class_id)
            
            student_bot.send_message(
                message.chat.id,
                welcome_text,
                reply_markup=keyboards.create_student_main_menu()
            )
        else:
            # Ученик не зарегистрирован
            student_bot.send_message(
                message.chat.id,
                "👋 Добро пожаловать! К сожалению, вы не зарегистрированы в этом обучающем боте. Обратитесь к вашему учителю для добавления.",
                reply_markup=types.ReplyKeyboardRemove()
            )

    @student_bot.callback_query_handler(func=lambda call: call.data == "student_main_menu")
    def student_main_menu_handler(call):
        user_id = call.from_user.id
        student_states[user_id] = StudentState.MAIN_MENU
        
        # Проверяем, зарегистрирован ли ученик
        student_info = database.get_student_by_username(bot_id, call.from_user.username)
        if not student_info:
            student_bot.answer_callback_query(call.id, "Вы не зарегистрированы в этом боте")
            return
        
        student_bot.edit_message_text(
            "📚 Главное меню ученика",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.create_student_main_menu()
        )

    @student_bot.callback_query_handler(func=lambda call: call.data == "student_subjects")
    def student_subjects_handler(call):
        user_id = call.from_user.id
        
        # Получаем класс ученика
        student_class = database.get_student_class(user_id, bot_id)
        if not student_class:
            student_bot.answer_callback_query(call.id, "Класс не назначен")
            return
        
        class_id, class_name, class_description = student_class
        
        # Получаем предметы класса
        subjects = database.get_class_subjects(class_id)
        
        if not subjects:
            student_bot.edit_message_text(
                "В вашем классе пока нет предметов.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu("student_main_menu")
            )
            return
            
        student_states[user_id] = StudentState.VIEWING_SUBJECTS
        
        student_bot.edit_message_text(
            f"📚 Предметы класса {class_name}:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.create_student_subjects_menu(subjects)
        )

    @student_bot.callback_query_handler(func=lambda call: call.data.startswith("student_subject_") and not call.data.startswith("student_subject_back_"))
    def student_subject_handler(call):
        user_id = call.from_user.id
        subject_id = int(call.data.split("_")[-1])
        topics = database.get_subject_topics(subject_id)
        
        if not topics:
            student_bot.edit_message_text(
                "По этому предмету пока нет тем для изучения.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu("student_subjects")
            )
            return
            
        # Получаем прогресс ученика
        student_progress = database.get_student_progress(user_id, subject_id)
        
        student_states[user_id] = StudentState.VIEWING_TOPICS
        student_states[f"{user_id}_subject_id"] = subject_id
        
        subject_info = database.get_subject_info(subject_id)
        subject_name = subject_info[2] if subject_info else "предмет"
        
        completed_count = sum(1 for progress in student_progress if progress[2])
        total_count = len(topics)
        
        progress_text = f"📖 Темы по {subject_name}:\n\n📊 Прогресс: {completed_count}/{total_count} тем изучено"
        
        try:
            student_bot.edit_message_text(
                progress_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_student_topics_menu(topics, student_progress, subject_id)
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e):
                # Игнорируем эту ошибку, так как сообщение уже имеет нужное содержимое
                pass
            else:
                # Переотправляем сообщение при других ошибках
                student_bot.send_message(
                    call.message.chat.id,
                    progress_text,
                    reply_markup=keyboards.create_student_topics_menu(topics, student_progress, subject_id)
                )
                try:
                    student_bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass

    @student_bot.callback_query_handler(func=lambda call: call.data.startswith("student_subject_back_"))
    def student_back_from_subject_handler(call):
        user_id = call.from_user.id
        
        # Возвращаемся к списку предметов
        student_states[user_id] = StudentState.VIEWING_SUBJECTS
        
        # Получаем класс ученика
        student_class = database.get_student_class(user_id, bot_id)
        if not student_class:
            student_bot.answer_callback_query(call.id, "Класс не назначен")
            return
        
        class_id, class_name, class_description = student_class
        
        # Получаем предметы класса
        subjects = database.get_class_subjects(class_id)
        
        if not subjects:
            student_bot.edit_message_text(
                "В вашем классе пока нет предметов.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu("student_main_menu")
            )
            return
        
        try:
            student_bot.edit_message_text(
                f"📚 Предметы класса {class_name}:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_student_subjects_menu(subjects)
            )
        except Exception as e:
            # Если не удалось редактировать, отправляем новое сообщение
            student_bot.send_message(
                call.message.chat.id,
                f"📚 Предметы класса {class_name}:",
                reply_markup=keyboards.create_student_subjects_menu(subjects)
            )
            try:
                student_bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass

    @student_bot.callback_query_handler(func=lambda call: call.data.startswith("student_topic_"))
    def student_topic_handler(call):
        user_id = call.from_user.id
        topic_id = int(call.data.split("_")[-1])
        topic = database.get_topic_info(topic_id)
        
        if not topic:
            student_bot.answer_callback_query(call.id, "Тема не найдена")
            return
            
        topic_id, subject_id, name, content, difficulty, created_at, file_path, file_type = topic
        
        # Получаем прогресс ученика по этой теме
        student_progress = database.get_student_progress(user_id, subject_id)
        completed = any(progress[0] == topic_id and progress[2] for progress in student_progress)
        
        # Форматируем содержание темы
        topic_text = f"📖 <b>{name}</b>\n\n"
        topic_text += f"📊 Уровень сложности: {difficulty}\n"
        topic_text += f"✅ Статус: {'Изучено' if completed else 'Новая тема'}\n\n"
        topic_text += f"{content}\n\n"
        topic_text += "---"
        
        markup = keyboards.create_student_topic_menu(topic_id, subject_id)
        
        # Если есть файл, отправляем его и текстовое сообщение раздельно
        # Храним ID сообщений для последующего удаления
        message_ids = []

        try:
            # Сначала отправляем файл (если есть)
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    if file_type and 'image' in file_type:
                        sent_message = student_bot.send_photo(call.message.chat.id, file, caption=f"📎 Файл к теме: {name}")
                    elif file_type and 'video' in file_type:
                        sent_message = student_bot.send_video(call.message.chat.id, file, caption=f"📎 Файл к теме: {name}")
                    else:
                        sent_message = student_bot.send_document(call.message.chat.id, file, caption=f"📎 Файл к теме: {name}")
                    message_ids.append(sent_message.message_id)
            
            # Затем отправляем текст с кнопками
            text_message = student_bot.send_message(
                call.message.chat.id,
                topic_text,
                reply_markup=markup,
                parse_mode='HTML'
            )
            message_ids.append(text_message.message_id)
            
            # Сохраняем ID сообщений для этого пользователя
            if user_id not in student_topic_messages:
                student_topic_messages[user_id] = []
            student_topic_messages[user_id] = message_ids
            
            # Удаляем предыдущее сообщение (меню тем)
            try:
                student_bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
                
        except Exception as e:
            logging.error(f"Ошибка отправки темы: {e}")
            # Если ошибка, отправляем только текст
            student_bot.edit_message_text(
                topic_text + f"\n\n❌ Не удалось загрузить прикрепленный файл",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )

    @student_bot.callback_query_handler(func=lambda call: call.data.startswith("complete_topic_"))
    def complete_topic_handler(call):
        user_id = call.from_user.id
        topic_id = int(call.data.split("_")[-1])
        
        if database.mark_topic_completed(user_id, topic_id):
            student_bot.answer_callback_query(call.id, "✅ Тема отмечена как изученная!")
            
            # Обновляем сообщение
            topic = database.get_topic_info(topic_id)
            if topic:
                topic_id, subject_id, name, content, difficulty, created_at, file_path, file_type = topic
                
                topic_text = f"📖 <b>{name}</b>\n\n"
                topic_text += f"📊 Уровень сложности: {difficulty}\n"
                topic_text += f"✅ Статус: Изучено\n\n"
                topic_text += f"{content}\n\n"
                topic_text += "---\n"
                topic_text += "🎉 Поздравляем с завершением темы!"
                
                markup = keyboards.create_student_topic_menu(topic_id, subject_id)
                
                # Если текущее сообщение содержит файл (медиа), удаляем его и отправляем новое текстовое
                try:
                    student_bot.edit_message_text(
                        topic_text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
                except:
                    # Если не удалось редактировать (сообщение с медиа), отправляем новое
                    student_bot.send_message(
                        call.message.chat.id,
                        topic_text,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
                    try:
                        student_bot.delete_message(call.message.chat.id, call.message.message_id)
                    except:
                        pass
        else:
            student_bot.answer_callback_query(call.id, "❌ Ошибка при отметке темы")

    @student_bot.callback_query_handler(func=lambda call: call.data == "student_progress")
    def student_progress_handler(call):
        user_id = call.from_user.id
        
        # Получаем класс ученика
        student_class = database.get_student_class(user_id, bot_id)
        if not student_class:
            student_bot.answer_callback_query(call.id, "Класс не назначен")
            return
        
        class_id, class_name, class_description = student_class
        
        # Получаем все предметы класса
        subjects = database.get_class_subjects(class_id)
        
        progress_text = f"📊 Ваши успехи - {class_name}\n\n"
        
        total_topics = 0
        completed_topics = 0
        
        for subject_id, subject_name, subject_description in subjects:
            topics = database.get_subject_topics(subject_id)
            student_progress = database.get_student_progress(user_id, subject_id)
            
            subject_completed = sum(1 for progress in student_progress if progress[2])
            subject_total = len(topics)
            
            progress_text += f"📚 {subject_name}:\n"
            progress_text += f"   ✅ {subject_completed}/{subject_total} тем изучено\n"
            
            if subject_total > 0:
                percentage = (subject_completed / subject_total) * 100
                progress_text += f"   📈 {percentage:.1f}% завершено\n"
            
            progress_text += "\n"
            
            total_topics += subject_total
            completed_topics += subject_completed
        
        if total_topics > 0:
            overall_percentage = (completed_topics / total_topics) * 100
            progress_text += f"🎯 Общий прогресс: {completed_topics}/{total_topics} тем ({overall_percentage:.1f}%)"
            
            # Добавляем мотивационное сообщение
            if overall_percentage == 100:
                progress_text += "\n\n🎉 Поздравляем! Вы изучили все темы!"
            elif overall_percentage >= 80:
                progress_text += "\n\n🌟 Отличный результат! Продолжайте в том же духе!"
            elif overall_percentage >= 50:
                progress_text += "\n\n👍 Хорошая работа! Еще немного усилий!"
            else:
                progress_text += "\n\n💪 Начинайте изучение! Каждая тема - это новый шаг к знаниям!"
        else:
            progress_text += "В вашем классе пока нет тем для изучения."
        
        student_bot.edit_message_text(
            progress_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.create_student_progress_menu()
        )

    @student_bot.callback_query_handler(func=lambda call: call.data == "student_additional_materials")
    def student_additional_materials_handler(call):
        user_id = call.from_user.id
        
        # Получаем класс ученика
        student_class = database.get_student_class(user_id, bot_id)
        if not student_class:
            student_bot.answer_callback_query(call.id, "Класс не назначен")
            return
        
        class_id, class_name, class_description = student_class
        
        # Получаем дополнительные материалы для класса
        materials = database.get_additional_materials(bot_id, class_id)
        
        if not materials:
            student_bot.edit_message_text(
                "🌟 Дополнительные материалы\n\nПока нет дополнительных материалов для вашего класса.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_back_button_menu("student_main_menu")
            )
            return
        
        student_states[user_id] = StudentState.VIEWING_ADDITIONAL_MATERIALS
        
        student_bot.edit_message_text(
            f"🌟 Дополнительные материалы - {class_name}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.create_student_additional_materials_menu(materials)
        )

    @student_bot.callback_query_handler(func=lambda call: call.data.startswith("student_view_material_"))
    def student_view_material_handler(call):
        user_id = call.from_user.id
        material_id = int(call.data.split("_")[-1])
        material = database.get_additional_material(material_id)
        
        if not material:
            student_bot.answer_callback_query(call.id, "Материал не найден")
            return
        
        material_id, bot_id, class_id, title, description, content, file_path, file_type, created_at = material
        
        file_info = ""
        if file_path:
            file_info = f"\n\n📎 Прикрепленный файл доступен для просмотра"
        
        text = f"🌟 <b>{title}</b>\n\n"
        if description:
            text += f"📝 {description}\n\n"
        text += f"{content}{file_info}"
        
        markup = keyboards.create_student_material_menu(material_id)
        
        # Если есть файл, отправляем его отдельным сообщением
        if file_path and os.path.exists(file_path):
            try:
                # Сначала отправляем текст с кнопками
                student_bot.send_message(
                    call.message.chat.id,
                    text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                
                # Затем отправляем файл отдельным сообщением
                with open(file_path, 'rb') as file:
                    if file_type and 'image' in file_type:
                        student_bot.send_photo(call.message.chat.id, file, caption=f"📎 Файл к материалу: {title}")
                    elif file_type and 'video' in file_type:
                        student_bot.send_video(call.message.chat.id, file, caption=f"📎 Файл к материалу: {title}")
                    else:
                        student_bot.send_document(call.message.chat.id, file, caption=f"📎 Файл к материалу: {title}")
                
                # Удаляем предыдущее сообщение (меню материалов)
                try:
                    student_bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass
                    
            except Exception as e:
                logging.error(f"Ошибка отправки файла: {e}")
                # Если ошибка, отправляем только текст
                student_bot.edit_message_text(
                    text + f"\n\n❌ Не удалось загрузить прикрепленный файл",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
        else:
            # Если нет файла, просто редактируем сообщение
            student_bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )

    # Обработчик для текстовых сообщений (на случай если ученик пишет текст)
    @student_bot.message_handler(func=lambda message: True)
    def student_text_handler(message):
        user_id = message.from_user.id
        
        # Проверяем, зарегистрирован ли ученик
        username = message.from_user.username
        if not username:
            student_bot.send_message(
                message.chat.id,
                "❌ Для использования бота необходимо установить username в настройках Telegram.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        
        student_info = database.get_student_by_username(bot_id, username)
        if not student_info:
            student_bot.send_message(
                message.chat.id,
                "👋 Добро пожаловать! К сожалению, вы не зарегистрированы в этом обучающем боте. Обратитесь к вашему учителю для добавления.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        
        # Если ученик зарегистрирован, показываем главное меню
        student_states[user_id] = StudentState.MAIN_MENU
        student_bot.send_message(
            message.chat.id,
            "📚 Главное меню ученика",
            reply_markup=keyboards.create_student_main_menu()
        )

    # Обработчики кнопок "Назад"
    @student_bot.callback_query_handler(func=lambda call: call.data == "student_main_menu")
    def back_to_main_menu_handler(call):
        user_id = call.from_user.id
        student_states[user_id] = StudentState.MAIN_MENU
        
        try:
            student_bot.edit_message_text(
                "📚 Главное меню ученика",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboards.create_student_main_menu()
            )
        except:
            # Если не удалось редактировать, отправляем новое сообщение
            student_bot.send_message(
                call.message.chat.id,
                "📚 Главное меню ученика",
                reply_markup=keyboards.create_student_main_menu()
            )
            try:
                student_bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass

    @student_bot.callback_query_handler(func=lambda call: call.data.startswith("student_back_to_topics_"))
    def student_back_to_topics_handler(call):
        user_id = call.from_user.id
        subject_id = int(call.data.split("_")[-1])
        
        # Удаляем сообщения темы (файл и текст)
        if user_id in student_topic_messages:
            for msg_id in student_topic_messages[user_id]:
                try:
                    student_bot.delete_message(call.message.chat.id, msg_id)
                except:
                    pass
            del student_topic_messages[user_id]
        
        # Получаем темы предмета
        topics = database.get_subject_topics(subject_id)
        if not topics:
            student_bot.send_message(
                call.message.chat.id,
                "По этому предмету пока нет тем для изучения.",
                reply_markup=keyboards.create_student_back_button("student_subjects")
            )
            return
        
        # Получаем прогресс ученика
        student_progress = database.get_student_progress(user_id, subject_id)
        
        subject_info = database.get_subject_info(subject_id)
        subject_name = subject_info[2] if subject_info else "предмет"
        
        completed_count = sum(1 for progress in student_progress if progress[2])
        total_count = len(topics)
        
        progress_text = f"📖 Темы по {subject_name}:\n\n📊 Прогресс: {completed_count}/{total_count} тем изучено"
        
        # Отправляем меню тем
        student_bot.send_message(
            call.message.chat.id,
            progress_text,
            reply_markup=keyboards.create_student_topics_menu(topics, student_progress, subject_id)
        )
        
        # Удаляем текущее сообщение (меню темы)
        try:
            student_bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    try:
        student_bot.infinity_polling()
    except Exception as e:
        logging.error(f"Ошибка в студенческом боте {bot_id}: {e}")