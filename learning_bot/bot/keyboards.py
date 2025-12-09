# keyboards.py
from telebot import types
import database as database

def create_student_back_button(target_callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=target_callback))
    return markup

def create_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_my_bots = types.InlineKeyboardButton("🤖 Мои боты", callback_data="my_bots")
    btn_predefined = types.InlineKeyboardButton("📚 Готовые материалы", callback_data="predefined_materials")
    markup.add(btn_my_bots, btn_predefined)
    return markup

def create_my_bots_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    bots = database.get_user_bots(user_id)
    
    for bot_id, bot_name in bots:
        markup.add(types.InlineKeyboardButton(bot_name, callback_data=f"manage_bot_{bot_id}"))
    
    markup.add(types.InlineKeyboardButton("➕ Создать нового бота", callback_data="create_bot"))
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return markup

def create_bot_management_menu(bot_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_token = types.InlineKeyboardButton("🔑 API бота", callback_data=f"edit_token_{bot_id}")
    btn_welcome = types.InlineKeyboardButton("👋 Приветствие", callback_data=f"edit_welcome_{bot_id}")
    btn_classes = types.InlineKeyboardButton("🏫 Классы", callback_data=f"manage_classes_{bot_id}")
    btn_students = types.InlineKeyboardButton("👥 Ученики", callback_data=f"manage_students_{bot_id}")
    btn_materials = types.InlineKeyboardButton("📚 Доп. материалы", callback_data=f"additional_materials_{bot_id}")
    btn_delete = types.InlineKeyboardButton("🗑️ Удалить бота", callback_data=f"delete_bot_{bot_id}")
    btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="my_bots")
    
    markup.add(btn_token, btn_welcome)
    markup.add(btn_classes, btn_students)
    markup.add(btn_materials)
    markup.add(btn_delete)
    markup.add(btn_back)
    return markup

def create_classes_menu(bot_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    classes = database.get_bot_classes(bot_id)
    
    for class_id, class_name, description in classes:
        btn_text = f"{class_name}"
        if description:
            btn_text += f" - {description}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"class_{class_id}"))
    
    markup.add(types.InlineKeyboardButton("➕ Добавить класс", callback_data=f"add_class_{bot_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"manage_bot_{bot_id}"))
    return markup

def create_class_menu(class_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📚 Предметы", callback_data=f"subjects_{class_id}"))
    markup.add(types.InlineKeyboardButton("✏️ Изменить название", callback_data=f"edit_class_{class_id}"))
    markup.add(types.InlineKeyboardButton("🗑️ Удалить класс", callback_data=f"delete_class_{class_id}"))
    
    class_info = database.get_class_info(class_id)
    if class_info:
        bot_id = class_info[1]
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"manage_classes_{bot_id}"))
    
    return markup

def create_subjects_menu(class_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    subjects = database.get_class_subjects(class_id)
    
    for subject_id, name, description in subjects:
        btn_text = f"{name}"
        if description:
            btn_text += f" - {description}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"subject_{subject_id}"))
    
    markup.add(types.InlineKeyboardButton("➕ Добавить предмет", callback_data=f"add_subject_{class_id}"))
    markup.add(types.InlineKeyboardButton("📚 Добавить готовые темы", callback_data=f"add_predefined_{class_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"class_{class_id}"))
    return markup

def create_subject_menu(subject_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📖 Темы", callback_data=f"topics_{subject_id}"))
    markup.add(types.InlineKeyboardButton("➕ Добавить тему", callback_data=f"add_topic_{subject_id}"))
    markup.add(types.InlineKeyboardButton("✏️ Изменить название", callback_data=f"edit_subject_{subject_id}"))
    markup.add(types.InlineKeyboardButton("🗑️ Удалить предмет", callback_data=f"delete_subject_{subject_id}"))
    
    subject_info = database.get_subject_info(subject_id)
    if subject_info:
        class_id = subject_info[1]
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"subjects_{class_id}"))
    
    return markup

def create_topics_menu(subject_id, page=0):
    markup = types.InlineKeyboardMarkup(row_width=1)
    topics = database.get_subject_topics(subject_id)
    
    start_idx = page * 5
    end_idx = min(start_idx + 5, len(topics))
    
    for i in range(start_idx, end_idx):
        topic = topics[i]
        topic_id, name, content, difficulty, file_path, file_type = topic
        file_icon = "📎" if file_path else ""
        markup.add(types.InlineKeyboardButton(f"{name} ({difficulty}) {file_icon}", callback_data=f"topic_{topic_id}"))

    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"prev_topics_{subject_id}_{page-1}"))
    if end_idx < len(topics):
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"next_topics_{subject_id}_{page+1}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    subject_info = database.get_subject_info(subject_id)
    if subject_info:
        class_id = subject_info[1]
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"subject_{subject_id}"))
    
    return markup

def create_topic_menu(topic_id, subject_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✏️ Изменить название", callback_data=f"edit_topic_name_{topic_id}"))
    markup.add(types.InlineKeyboardButton("📝 Изменить содержание", callback_data=f"edit_topic_content_{topic_id}"))
    markup.add(types.InlineKeyboardButton("📎 Добавить/изменить файл", callback_data=f"edit_topic_file_{topic_id}"))
    markup.add(types.InlineKeyboardButton("🗑️ Удалить тему", callback_data=f"delete_topic_{topic_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"topics_{subject_id}"))
    return markup

def create_predefined_classes_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    classes = database.get_predefined_topics()
    
    for class_info in classes:
        class_name = class_info[0]
        markup.add(types.InlineKeyboardButton(class_name, callback_data=f"predefined_class_{class_name}"))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))
    return markup

def create_predefined_subjects_menu(class_name):
    markup = types.InlineKeyboardMarkup(row_width=2)
    subjects_data = database.get_predefined_topics(class_name)
    
    # Исправляем получение предметов
    subjects = set()
    for subject_data in subjects_data:
        if subject_data and len(subject_data) > 0:
            subjects.add(subject_data[0])
    
    for subject in subjects:
        # Исправляем callback_data - добавляем class_name и subject_name правильно
        callback_data = f"predefined_subject_{class_name}_{subject.replace(' ', '_')}"
        markup.add(types.InlineKeyboardButton(subject, callback_data=callback_data))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="predefined_materials"))
    return markup

def create_predefined_topics_menu(class_name, subject_name):
    markup = types.InlineKeyboardMarkup(row_width=1)
    topics = database.get_predefined_topics(class_name, subject_name)
    
    for topic_name, content in topics:
        markup.add(types.InlineKeyboardButton(topic_name, callback_data=f"view_predefined_{class_name}_{subject_name}_{topic_name}"))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"predefined_class_{class_name}"))
    return markup

def create_predefined_topic_menu(class_name, subject_name, topic_name):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📥 Добавить в мой бот", callback_data=f"add_predefined_topic_{class_name}_{subject_name}_{topic_name}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"predefined_subject_{class_name}_{subject_name}"))
    return markup

def create_back_button_menu(target_callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=target_callback))
    return markup

def create_student_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📚 Мои предметы", callback_data="student_subjects"))
    markup.add(types.InlineKeyboardButton("📊 Мои успехи", callback_data="student_progress"))
    markup.add(types.InlineKeyboardButton("🌟 Доп. материалы", callback_data="student_additional_materials"))
    return markup

def create_student_classes_menu(classes):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for class_id, class_name, description in classes:
        btn_text = class_name
        if description:
            btn_text += f" - {description}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"student_class_{class_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="student_main_menu"))
    return markup

def create_student_subjects_menu(subjects):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for subject_id, name, description in subjects:
        btn_text = name
        if description:
            btn_text += f" - {description}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"student_subject_{subject_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="student_main_menu"))
    return markup

def create_student_topics_menu(topics, student_progress, subject_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for topic in topics:
        topic_id, name, content, difficulty, file_path, file_type = topic  # Теперь распаковываем все 6 элементов
        completed = any(progress[0] == topic_id and progress[2] for progress in student_progress)
        status = "✅" if completed else "📖"
        file_icon = " 📎" if file_path else ""  # Добавляем иконку, если есть файл (опционально, но рекомендуется)
        markup.add(types.InlineKeyboardButton(f"{status} {name} ({difficulty}){file_icon}", callback_data=f"student_topic_{topic_id}"))
        
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"student_subject_back_{subject_id}"))
    
    return markup

def create_student_topic_menu(topic_id, subject_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✅ Отметить как изученное", callback_data=f"complete_topic_{topic_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад к темам", callback_data=f"student_subject_{subject_id}"))
    return markup

def create_student_progress_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="student_main_menu"))
    return markup

def create_students_management_menu(bot_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ Добавить ученика", callback_data=f"add_student_{bot_id}"))
    markup.add(types.InlineKeyboardButton("📋 Список учеников", callback_data=f"list_students_{bot_id}"))
    markup.add(types.InlineKeyboardButton("➖ Удалить ученика", callback_data=f"remove_student_{bot_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"manage_bot_{bot_id}"))
    return markup

def create_students_list_menu(students):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for student_id, username, class_name, added_at in students:
        markup.add(types.InlineKeyboardButton(f"@{username} - {class_name}", callback_data=f"view_student_{student_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="students_management"))
    return markup

def create_remove_student_menu(students, bot_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for student_id, username, class_name, added_at in students:
        markup.add(types.InlineKeyboardButton(f"@{username} - {class_name}", callback_data=f"confirm_remove_{bot_id}_{username}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"manage_students_{bot_id}"))
    return markup

def create_confirm_remove_menu(bot_id, username):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✅ Да, удалить", callback_data=f"do_remove_{bot_id}_{username}"))
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data=f"remove_student_{bot_id}"))
    return markup

def create_additional_materials_menu(bot_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ Добавить материал", callback_data=f"add_material_{bot_id}"))
    markup.add(types.InlineKeyboardButton("📋 Список материалов", callback_data=f"list_materials_{bot_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"manage_bot_{bot_id}"))
    return markup

def create_materials_list_menu(materials, bot_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for material_id, title, description, content, file_path, file_type in materials:
        file_icon = "📎" if file_path else ""
        btn_text = f"{title}{file_icon}"
        if description:
            btn_text += f" - {description[:20]}..."
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"view_material_{material_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"additional_materials_{bot_id}"))
    return markup

def create_material_menu(material_id, bot_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🗑️ Удалить материал", callback_data=f"delete_material_{material_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"list_materials_{bot_id}"))
    return markup

def create_student_additional_materials_menu(materials):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for material_id, title, description, content, file_path, file_type in materials:
        file_icon = "📎" if file_path else ""
        btn_text = f"{title}{file_icon}"
        if description:
            btn_text += f" - {description[:20]}..."
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"student_view_material_{material_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="student_main_menu"))
    return markup

def create_student_material_menu(material_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="student_additional_materials"))
    return markup

def create_class_selection_menu(classes, action, bot_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for class_id, class_name, description in classes:
        btn_text = class_name
        if description:
            btn_text += f" - {description}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"{action}_{class_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"manage_students_{bot_id}"))
    return markup