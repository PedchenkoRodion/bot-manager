# database.py
import sqlite3
import os
import logging
import threading

db_lock = threading.Lock()
DB_NAME = "db/teacher_bot.db"

def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teacher_bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        bot_name TEXT NOT NULL,
        bot_token TEXT,
        welcome_message TEXT DEFAULT 'Добро пожаловать в обучающий бот!',
        bot_username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_running INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        tg_id INTEGER UNIQUE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (bot_id) REFERENCES teacher_bots (id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (bot_id) REFERENCES teacher_bots (id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        content TEXT NOT NULL,
        difficulty_level TEXT DEFAULT 'beginner',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        file_path TEXT,
        file_type TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        completed BOOLEAN DEFAULT FALSE,
        completed_at TIMESTAMP,
        score INTEGER DEFAULT 0,
        FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE,
        UNIQUE(student_id, topic_id)  -- ДОБАВЬТЕ ЭТУ СТРОКУ
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predefined_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT NOT NULL,
        subject_name TEXT NOT NULL,
        topic_name TEXT NOT NULL,
        content TEXT NOT NULL,
        difficulty_level TEXT DEFAULT 'beginner'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        bot_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        FOREIGN KEY (bot_id) REFERENCES teacher_bots (id) ON DELETE CASCADE,
        FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        class_id INTEGER NOT NULL,
        added_by INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bot_id) REFERENCES teacher_bots (id) ON DELETE CASCADE,
        FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS additional_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        content TEXT NOT NULL,
        file_path TEXT,
        file_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bot_id) REFERENCES teacher_bots (id) ON DELETE CASCADE,
        FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE
    )
    ''')
    
    # Добавляем стандартные темы в базу
    add_predefined_topics(cursor)
    
    conn.commit()
    conn.close()

def add_predefined_topics(cursor):
    """Добавляет предопределенные темы в базу данных"""
    
    # Математика 1 класс
    math_1_topics = [
        ("Числа от 1 до 10", "Числа от 1 до 10 - это основа математики. Учимся считать: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10. Каждое число имеет свое значение и порядок. Числа используются для счета предметов, измерения и решения задач."),
        ("Сложение", "Сложение - это объединение чисел. Пример: 2 + 3 = 5. Когда мы складываем, мы объединяем две группы предметов в одну. Это одна из основных математических операций, которую мы используем каждый день."),
        ("Вычитание", "Вычитание - это удаление части. Пример: 5 - 2 = 3. Мы убираем некоторое количество предметов из группы. Вычитание помогает нам находить разницу между числами и решать задачи на уменьшение."),
        ("Геометрические фигуры", "Квадрат - четыре равные стороны и четыре прямых угла. Круг - нет углов, все точки равноудалены от центра. Треугольник - три стороны и три угла. Прямоугольник - противоположные стороны равны, все углы прямые."),
        ("Сравнение чисел", "Мы можем сравнивать числа: больше (>), меньше (<) или равно (=). Например: 5 > 3, 2 < 7, 4 = 4. Сравнение помогает нам упорядочивать числа и понимать их величину."),
    ]
    
    for topic_name, content in math_1_topics:
        cursor.execute('''
            INSERT OR IGNORE INTO predefined_topics (class_name, subject_name, topic_name, content)
            VALUES (?, ?, ?, ?)
        ''', ("1 класс", "Математика", topic_name, content))
    
    # Русский язык 1 класс
    russian_1_topics = [
        ("Алфавит", "Русский алфавит состоит из 33 букв: А, Б, В, Г, Д, Е, Ё, Ж, З, И, Й, К, Л, М, Н, О, П, Р, С, Т, У, Ф, Х, Ц, Ч, Ш, Щ, Ъ, Ы, Ь, Э, Ю, Я. Буквы бывают гласные и согласные, прописные и строчные."),
        ("Гласные и согласные", "Гласные звуки: А, Е, Ё, И, О, У, Ы, Э, Ю, Я (10 букв). Согласные звуки: все остальные буквы. Гласные можно петь, согласные - нет. Согласные бывают твердые и мягкие, звонкие и глухие."),
        ("Слоги", "Слог - это сочетание звуков, которые произносятся одним толчком воздуха. Пример: ма-ма, па-па, до-мик. В каждом слоге есть гласный звук. Слоги помогают нам правильно делить слова для переноса и чтения."),
        ("Ударение", "Ударение - это выделение одного слога в слове голосом. Например: ма́ма, па́па, кни́га. Ударный слог произносится сильнее и длиннее. Ударение помогает различать слова и правильно их произносить."),
        ("Предложение", "Предложение - это группа слов, выражающая законченную мысль. Предложение начинается с заглавной буквы и заканчивается точкой, вопросительным или восклицательным знаком."),
    ]
    
    for topic_name, content in russian_1_topics:
        cursor.execute('''
            INSERT OR IGNORE INTO predefined_topics (class_name, subject_name, topic_name, content)
            VALUES (?, ?, ?, ?)
        ''', ("1 класс", "Русский язык", topic_name, content))
    
    # Математика 2 класс
    math_2_topics = [
        ("Таблица умножения", "Умножение на 2: 2×1=2, 2×2=4, 2×3=6, 2×4=8, 2×5=10, 2×6=12, 2×7=14, 2×8=16, 2×9=18, 2×10=20. Умножение - это быстрое сложение одинаковых чисел. Например, 2×3 = 2+2+2 = 6."),
        ("Задачи на сложение и вычитание", "Пример задачи: 'У Маши 5 яблок, а у Пети 3 яблока. Сколько всего яблок?' Решение: 5 + 3 = 8. Важно понимать условие задачи и правильно выбирать действие. Задачи бывают на нахождение суммы, разности, увеличение и уменьшение."),
        ("Единицы измерения", "Длина: сантиметр (см), метр (м). Масса: килограмм (кг), грамм (г). Объем: литр (л). 1 метр = 100 сантиметров, 1 килограмм = 1000 грамм. Единицы измерения помогают нам точно измерять различные величины."),
        ("Умножение и деление", "Умножение - повторное сложение, деление - обратное действие. Пример: 3 × 4 = 12, значит 12 ÷ 4 = 3. Деление помогает распределять предметы поровну или находить, сколько раз одно число содержится в другом."),
        ("Геометрические задачи", "Решение простых геометрических задач: нахождение периметра прямоугольника (P = 2×(a+b)), площади квадрата (S = a×a). Геометрия помогает нам понимать формы и размеры окружающих предметов."),
    ]
    
    for topic_name, content in math_2_topics:
        cursor.execute('''
            INSERT OR IGNORE INTO predefined_topics (class_name, subject_name, topic_name, content)
            VALUES (?, ?, ?, ?)
        ''', ("2 класс", "Математика", topic_name, content))
    
    # Русский язык 2 класс
    russian_2_topics = [
        ("Части речи", "Имя существительное - называет предметы (стол, книга, мама). Имя прилагательное - описывает предметы (красный, большой, красивый). Глагол - обозначает действие (бежит, читает, говорит). Местоимение - заменяет имя существительное (я, ты, он, она)."),
        ("Предложение", "Предложение - это группа слов, выражающая законченную мысль. В предложении есть подлежащее (кто? что?) и сказуемое (что делает?). Пример: 'Птица летит.' Подлежащее - птица, сказуемое - летит."),
        ("Большая буква", "С большой буквы пишутся: имена людей (Мария, Александр), фамилии (Иванов, Петрова), клички животных (Шарик, Мурка), названия городов (Москва, Санкт-Петербург), стран (Россия, Франция), начало предложения."),
        ("Состав слова", "Слова состоят из частей: корень (главная часть), приставка (перед корнем), суффикс (после корнем), окончание (изменяемая часть). Пример: пере-ход-н-ый. Корень - ход, приставка - пере, суффикс - н, окончание - ый."),
        ("Правописание жи-ши, ча-ща, чу-щу", "Сочетания ЖИ-ШИ пиши с буквой И (жить, шить). ЧА-ЩА пиши с буквой А (чаша, щавель). ЧУ-ЩУ пиши с буквой У (чудеса, щука). Это правило нужно запомнить, так как эти сочетания всегда пишутся одинаково."),
    ]
    
    for topic_name, content in russian_2_topics:
        cursor.execute('''
            INSERT OR IGNORE INTO predefined_topics (class_name, subject_name, topic_name, content)
            VALUES (?, ?, ?, ?)
        ''', ("2 класс", "Русский язык", topic_name, content))

    # Окружающий мир 1 класс
    world_1_topics = [
        ("Времена года", "Зима - холодно, снег, короткие дни. Весна - тает снег, появляются цветы, прилетают птицы. Лето - тепло, каникулы, длинные дни. Осень - листья желтеют, птицы улетают, сбор урожая. Каждое время года длится 3 месяца."),
        ("Домашние животные", "Кошка, собака, корова, лошадь, коза, овца, свинья, курица. Животные, которые живут с человеком и приносят ему пользу. Человек заботится о них: кормит, поит, лечит, дает жилье."),
        ("Дикие животные", "Медведь, волк, лиса, заяц, белка, еж, лось. Животные, которые живут в лесу, сами добывают пищу и строят жилища. Они приспособлены к жизни в природных условиях."),
        ("Растения", "Деревья (береза, дуб, ель), кустарники (сирень, малина), травы (подорожник, одуванчик). Растения дают нам кислород, пищу, лекарства. Они являются домом для многих животных."),
        ("Правила дорожного движения", "Переходить дорогу только на зеленый свет светофора, по пешеходному переходу. Смотреть сначала налево, потом направо. Не играть на проезжей части. Носить светоотражающие элементы в темное время суток."),
    ]
    
    for topic_name, content in world_1_topics:
        cursor.execute('''
            INSERT OR IGNORE INTO predefined_topics (class_name, subject_name, topic_name, content)
            VALUES (?, ?, ?, ?)
        ''', ("1 класс", "Окружающий мир", topic_name, content))

    # Окружающий мир 2 класс
    world_2_topics = [
        ("Природные зоны России", "Арктика - холодно, льды, белые медведи. Тундра - мхи, лишайники, северные олени. Лес - деревья, много животных. Степь - травы, мало деревьев. Пустыня - жарко, кактусы, верблюды."),
        ("Водоемы", "Река - течет в одном направлении. Озеро - окружено сушей. Море - часть океана. Океан - самый большой водоем. Водоемы являются домом для многих растений и животных, дают нам воду и пищу."),
        ("Полезные ископаемые", "Уголь, нефть, газ - топливо. Железная руда - металл. Песок, глина - строительные материалы. Соль - пищевой продукт. Полезные ископаемые добывают из земли и используют в хозяйстве."),
        ("Экология", "Экология - наука о взаимоотношениях живых организмов с окружающей средой. Важно беречь природу: не мусорить, экономить воду и электричество, сажать деревья, защищать животных."),
        ("Страны и народы", "Россия - самая большая страна в мире. В мире много разных стран: Китай, Индия, США, Бразилия и др. У каждого народа свои традиции, язык, культура, национальная кухня и праздники."),
    ]
    
    for topic_name, content in world_2_topics:
        cursor.execute('''
            INSERT OR IGNORE INTO predefined_topics (class_name, subject_name, topic_name, content)
            VALUES (?, ?, ?, ?)
        ''', ("2 класс", "Окружающий мир", topic_name, content))

    # Литература 1 класс
    literature_1_topics = [
        ("Русские народные сказки", "'Колобок', 'Репка', 'Теремок', 'Курочка Ряба'. Сказки учат добру, дружбе, взаимопомощи. В них добро всегда побеждает зло. Сказки передаются из поколения в поколение."),
        ("Стихи для детей", "Стихи А. Барто, С. Маршака, К. Чуковского. Стихи развивают память, чувство ритма, обогащают словарный запас. Они веселые, легко запоминаются и нравятся детям."),
        ("Рассказы о животных", "Рассказы В. Бианки, М. Пришвина, Е. Чарушина. Писатели описывают повадки животных, их жизнь в природе. Эти рассказы учат любить и понимать природу, бережно относиться к животным."),
        ("Басни", "Басни И. Крылова: 'Ворона и Лисица', 'Стрекоза и Муравей', 'Мартышка и Очки'. Басни - это короткие поучительные истории, в которых животные ведут себя как люди. Каждая басня содержит мораль - главную мысль."),
        ("Детские писатели", "Корней Чуковский ('Айболит', 'Мойдодыр'), Самуил Маршак ('Кошкин дом', 'Вот какой рассеянный'), Агния Барто ('Игрушки'). Эти писатели создали замечательные произведения, которые любят все дети."),
    ]
    
    for topic_name, content in literature_1_topics:
        cursor.execute('''
            INSERT OR IGNORE INTO predefined_topics (class_name, subject_name, topic_name, content)
            VALUES (?, ?, ?, ?)
        ''', ("1 класс", "Литература", topic_name, content))

    # Литература 2 класс
    literature_2_topics = [
        ("Русские былины", "Былины о богатырях: Илье Муромце, Добрыне Никитиче, Алеше Поповиче. Былины - это народные эпические песни о подвигах богатырей. Они воспевают мужество, силу, любовь к Родине."),
        ("Сказки народов мира", "Сказки разных стран: 'Золушка' (Франция), 'Бременские музыканты' (Германия), 'Аладдин' (Арабские страны). Сказки разных народов похожи, но имеют национальные особенности."),
        ("Рассказы о детях", "Рассказы Н. Носова ('Живая шляпа', 'Фантазеры'), В. Драгунского ('Денискины рассказы'). Эти рассказы веселые, понятные детям, учат дружбе, честности, взаимовыручке."),
        ("Поэзия о природе", "Стихи Ф. Тютчева, А. Фета, С. Есенина о природе. Поэты тонко чувствуют красоту природы и умеют передать ее в словах. Их стихи развивают воображение и любовь к родной природе."),
        ("Детские журналы", "'Мурзилка', 'Веселые картинки' - популярные детские журналы. В них публикуются рассказы, стихи, загадки, кроссворды, комиксы. Журналы развивают интерес к чтению и познанию нового."),
    ]
    
    for topic_name, content in literature_2_topics:
        cursor.execute('''
            INSERT OR IGNORE INTO predefined_topics (class_name, subject_name, topic_name, content)
            VALUES (?, ?, ?, ?)
        ''', ("2 класс", "Литература", topic_name, content))

def create_teacher_bot(user_id, bot_name):
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    if not bot_name or not isinstance(bot_name, str) or len(bot_name) < 2:
        return None
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO teacher_bots (user_id, bot_name) VALUES (?, ?)", (user_id, bot_name))
    bot_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return bot_id

def get_user_bots(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, bot_name FROM teacher_bots WHERE user_id = ?
    UNION
    SELECT tb.id, tb.bot_name FROM teacher_bots tb
    JOIN bot_admins ba ON tb.id = ba.bot_id
    WHERE ba.user_id = ?
    """, (user_id, user_id))
    bots = cursor.fetchall()
    conn.close()
    return bots

def get_bot_info(bot_id):
    if not isinstance(bot_id, int) or bot_id <= 0:
        return None
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teacher_bots WHERE id = ?", (bot_id,))
    bot = cursor.fetchone()
    conn.close()
    return bot

def update_bot_token(bot_id, token):
    if not isinstance(bot_id, int) or bot_id <= 0:
        return
    if not token or not isinstance(token, str) or len(token) < 30:
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    bot_username = None
    try:
        import telebot
        temp_bot = telebot.TeleBot(token)
        bot_info = temp_bot.get_me()
        bot_username = bot_info.username
        cursor.execute("UPDATE teacher_bots SET bot_token = ?, bot_username = ?, is_running = 1 WHERE id = ?", (token, bot_username, bot_id))
        conn.commit()
        logging.info(f"Токен для бота {bot_id} обновлён, username: @{bot_username}")
    except Exception as e:
        logging.error(f"Ошибка при проверке токена: {e}")
        cursor.execute("UPDATE teacher_bots SET bot_token = ?, bot_username = NULL, is_running = 0 WHERE id = ?", (token, bot_id))
        conn.commit()
    conn.close()
    return bot_username

def update_welcome_message(bot_id, message):
    if not isinstance(bot_id, int) or bot_id <= 0:
        return False
    if not message or not isinstance(message, str) or len(message) < 5:
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE teacher_bots SET welcome_message = ? WHERE id = ?", (message, bot_id))
    conn.commit()
    conn.close()
    return True

def get_bot_classes(bot_id):
    if not isinstance(bot_id, int) or bot_id <= 0:
        return []
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM classes WHERE bot_id = ?", (bot_id,))
    classes = cursor.fetchall()
    conn.close()
    return classes

def create_class(bot_id, name, description=None):
    if not isinstance(bot_id, int) or bot_id <= 0:
        return None
    if not name or not isinstance(name, str) or len(name) < 2:
        return None
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO classes (bot_id, name, description) VALUES (?, ?, ?)", (bot_id, name, description))
    class_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return class_id

def get_class_info(class_id):
    if not isinstance(class_id, int) or class_id <= 0:
        return None
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
    class_info = cursor.fetchone()
    conn.close()
    return class_info

def update_class_name(class_id, new_name, new_description=None):
    if not isinstance(class_id, int) or class_id <= 0:
        return False
    if not new_name or not isinstance(new_name, str) or len(new_name) < 2:
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if new_description:
        cursor.execute("UPDATE classes SET name = ?, description = ? WHERE id = ?", (new_name, new_description, class_id))
    else:
        cursor.execute("UPDATE classes SET name = ? WHERE id = ?", (new_name, class_id))
    conn.commit()
    conn.close()
    return True

def delete_class(class_id):
    if not isinstance(class_id, int) or class_id <= 0:
        return False
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Получаем bot_id для удаления записей учеников
        cursor.execute("SELECT bot_id FROM classes WHERE id = ?", (class_id,))
        class_info = cursor.fetchone()
        if not class_info:
            return False
            
        bot_id = class_info[0]
        
        # Удаляем записи учеников этого класса
        cursor.execute("DELETE FROM student_classes WHERE class_id = ? AND bot_id = ?", (class_id, bot_id))
        cursor.execute("DELETE FROM bot_students WHERE class_id = ?", (class_id,))
        
        # Удаляем темы, предметы и класс
        cursor.execute("DELETE FROM topics WHERE subject_id IN (SELECT id FROM subjects WHERE class_id = ?)", (class_id,))
        cursor.execute("DELETE FROM subjects WHERE class_id = ?", (class_id,))
        cursor.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Ошибка при удалении класса: {e}")
        return False
    finally:
        conn.close()

def get_class_subjects(class_id):
    if not isinstance(class_id, int) or class_id <= 0:
        return []
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM subjects WHERE class_id = ?", (class_id,))
    subjects = cursor.fetchall()
    conn.close()
    return subjects

def create_subject(class_id, name, description=None):
    if not isinstance(class_id, int) or class_id <= 0:
        return None
    if not name or not isinstance(name, str) or len(name) < 2:
        return None
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subjects (class_id, name, description) VALUES (?, ?, ?)", (class_id, name, description))
    subject_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return subject_id

def get_subject_info(subject_id):
    if not isinstance(subject_id, int) or subject_id <= 0:
        return None
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()
    conn.close()
    return subject

def update_subject_name(subject_id, new_name, new_description=None):
    if not isinstance(subject_id, int) or subject_id <= 0:
        return False
    if not new_name or not isinstance(new_name, str) or len(new_name) < 2:
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if new_description:
        cursor.execute("UPDATE subjects SET name = ?, description = ? WHERE id = ?", (new_name, new_description, subject_id))
    else:
        cursor.execute("UPDATE subjects SET name = ? WHERE id = ?", (new_name, subject_id))
    conn.commit()
    conn.close()
    return True

def delete_subject(subject_id):
    if not isinstance(subject_id, int) or subject_id <= 0:
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()
    return True

def get_subject_topics(subject_id):
    if not isinstance(subject_id, int) or subject_id <= 0:
        return []
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, content, difficulty_level, file_path, file_type FROM topics WHERE subject_id = ? ORDER BY created_at", (subject_id,))
    topics = cursor.fetchall()
    conn.close()
    return topics

def create_topic(subject_id, name, content, difficulty_level='beginner', file_path=None, file_type=None):
    if not isinstance(subject_id, int) or subject_id <= 0:
        return None
    if not name or not isinstance(name, str) or len(name) < 2:
        return None
    if not content or not isinstance(content, str) or len(content) < 5:
        return None
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO topics (subject_id, name, content, difficulty_level, file_path, file_type) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (subject_id, name, content, difficulty_level, file_path, file_type))
        
        topic_id = cursor.lastrowid
        conn.commit()
        logging.info(f"Тема создана: ID={topic_id}, name={name}, subject_id={subject_id}")
        
    except Exception as e:
        logging.error(f"Ошибка при создании темы: {e}")
        topic_id = None
        conn.rollback()
    
    conn.close()
    return topic_id

def get_topic_info(topic_id):
    if not isinstance(topic_id, int) or topic_id <= 0:
        return None
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
    topic = cursor.fetchone()
    conn.close()
    return topic

def update_topic(topic_id, name=None, content=None, difficulty_level=None, file_path=None, file_type=None):
    if not isinstance(topic_id, int) or topic_id <= 0:
        return False
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if difficulty_level is not None:
        updates.append("difficulty_level = ?")
        params.append(difficulty_level)
    if file_path is not None:
        updates.append("file_path = ?")
        params.append(file_path)
    if file_type is not None:
        updates.append("file_type = ?")
        params.append(file_type)
    
    if updates:
        query = "UPDATE topics SET " + ", ".join(updates) + " WHERE id = ?"
        params.append(topic_id)
        cursor.execute(query, tuple(params))
        conn.commit()
    
    conn.close()
    return True

def delete_topic(topic_id):
    if not isinstance(topic_id, int) or topic_id <= 0:
        return False
    
    # Получаем информацию о файле перед удалением
    topic = get_topic_info(topic_id)
    if topic and topic[6]:  # file_path
        file_path = topic[6]
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logging.error(f"Ошибка при удалении файла: {e}")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    conn.commit()
    conn.close()
    return True

def get_predefined_topics(class_name=None, subject_name=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if class_name and subject_name:
        cursor.execute("SELECT topic_name, content FROM predefined_topics WHERE class_name = ? AND subject_name = ?", 
                      (class_name, subject_name))
    elif class_name:
        cursor.execute("SELECT DISTINCT subject_name FROM predefined_topics WHERE class_name = ?", 
                      (class_name,))
    else:
        cursor.execute("SELECT DISTINCT class_name FROM predefined_topics")
    
    results = cursor.fetchall()
    conn.close()
    return results

def add_predefined_to_bot(bot_id, class_name, subject_name, topic_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Получаем класс или создаем его
        cursor.execute("SELECT id FROM classes WHERE bot_id = ? AND name = ?", (bot_id, class_name))
        class_result = cursor.fetchone()
        if not class_result:
            cursor.execute("INSERT INTO classes (bot_id, name) VALUES (?, ?)", (bot_id, class_name))
            class_id = cursor.lastrowid
        else:
            class_id = class_result[0]
        
        # Получаем предмет или создаем его
        cursor.execute("SELECT id FROM subjects WHERE class_id = ? AND name = ?", (class_id, subject_name))
        subject_result = cursor.fetchone()
        if not subject_result:
            cursor.execute("INSERT INTO subjects (class_id, name) VALUES (?, ?)", (class_id, subject_name))
            subject_id = cursor.lastrowid
        else:
            subject_id = subject_result[0]
        
        # Получаем содержание темы
        cursor.execute("SELECT content FROM predefined_topics WHERE class_name = ? AND subject_name = ? AND topic_name = ?", 
                      (class_name, subject_name, topic_name))
        topic_content_result = cursor.fetchone()
        
        if topic_content_result:
            topic_content = topic_content_result[0]
            # Проверяем, нет ли уже такой темы
            cursor.execute("SELECT id FROM topics WHERE subject_id = ? AND name = ?", (subject_id, topic_name))
            existing_topic = cursor.fetchone()
            
            if not existing_topic:
                # Добавляем тему
                cursor.execute("INSERT INTO topics (subject_id, name, content) VALUES (?, ?, ?)", 
                              (subject_id, topic_name, topic_content))
                topic_id = cursor.lastrowid
            else:
                topic_id = existing_topic[0]  # Тема уже существует
        else:
            topic_id = None
        
        conn.commit()
        return topic_id
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Ошибка при добавлении готовой темы: {e}")
        return None
    finally:
        conn.close()

def add_user(tg_id, username=None):
    if not isinstance(tg_id, int) or tg_id <= 0:
        return
    if username is not None and not isinstance(username, str):
        return
    
    with db_lock:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE tg_id = ?", (tg_id,))
        exists = cursor.fetchone() is not None
        
        if not exists:
            cursor.execute("INSERT INTO users (tg_id, username) VALUES (?, ?)", (tg_id, username))
        elif username:
            cursor.execute("UPDATE users SET username = ? WHERE tg_id = ?", (username, tg_id))
        conn.commit()
        conn.close()

def set_student_class(student_id, bot_id, class_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Удаляем старый класс если есть
    cursor.execute("DELETE FROM student_classes WHERE student_id = ? AND bot_id = ?", (student_id, bot_id))
    
    # Добавляем новый класс
    cursor.execute("INSERT INTO student_classes (student_id, bot_id, class_id) VALUES (?, ?, ?)", 
                  (student_id, bot_id, class_id))
    
    conn.commit()
    conn.close()
    return True

def get_student_class(student_id, bot_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, c.description 
        FROM student_classes sc 
        JOIN classes c ON sc.class_id = c.id 
        WHERE sc.student_id = ? AND sc.bot_id = ?
    """, (student_id, bot_id))
    result = cursor.fetchone()
    conn.close()
    return result

def mark_topic_completed(student_id, topic_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем, существует ли уже запись
    cursor.execute("SELECT id FROM student_progress WHERE student_id = ? AND topic_id = ?", 
                  (student_id, topic_id))
    existing = cursor.fetchone()
    
    if existing:
        # Обновляем существующую запись
        cursor.execute("""
            UPDATE student_progress 
            SET completed = TRUE, completed_at = CURRENT_TIMESTAMP, score = 100 
            WHERE student_id = ? AND topic_id = ?
        """, (student_id, topic_id))
    else:
        # Создаем новую запись
        cursor.execute("""
            INSERT INTO student_progress (student_id, topic_id, completed, completed_at, score)
            VALUES (?, ?, TRUE, CURRENT_TIMESTAMP, 100)
        """, (student_id, topic_id))
    
    conn.commit()
    conn.close()
    return True

def get_student_progress(student_id, subject_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        if subject_id:
            # Получаем прогресс по конкретному предмету
            cursor.execute("""
                SELECT t.id, t.name, 
                    CASE WHEN sp.completed = 1 THEN 1 ELSE 0 END as completed 
                FROM topics t 
                LEFT JOIN student_progress sp ON t.id = sp.topic_id AND sp.student_id = ?
                WHERE t.subject_id = ?
                GROUP BY t.id  -- ДОБАВЬТЕ ЭТУ СТРОКУ
                ORDER BY t.id
            """, (student_id, subject_id))
        else:
            # Получаем весь прогресс ученика
            cursor.execute("""
                SELECT t.id, t.name, 
                    CASE WHEN sp.completed = 1 THEN 1 ELSE 0 END as completed 
                FROM topics t 
                LEFT JOIN student_progress sp ON t.id = sp.topic_id AND sp.student_id = ?
                GROUP BY t.id  -- ДОБАВЬТЕ ЭТУ СТРОКУ
                ORDER BY t.id
            """, (student_id,))
        
        progress = cursor.fetchall()
        return progress
        
    except Exception as e:
        logging.error(f"Ошибка при получении прогресса: {e}")
        return []
    finally:
        conn.close()

def delete_bot(bot_id):
    if not isinstance(bot_id, int) or bot_id <= 0:
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM teacher_bots WHERE id = ?", (bot_id,))
    conn.commit()
    conn.close()
    return True

def add_student_by_username(bot_id, username, class_id, added_by):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем, существует ли уже такой ученик
    cursor.execute("SELECT id FROM bot_students WHERE bot_id = ? AND username = ?", (bot_id, username))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return False
    
    # Добавляем ученика
    cursor.execute("INSERT INTO bot_students (bot_id, username, class_id, added_by) VALUES (?, ?, ?, ?)", 
                  (bot_id, username, class_id, added_by))
    
    conn.commit()
    conn.close()
    return True

def get_bot_students(bot_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT bs.id, bs.username, c.name, bs.added_at 
        FROM bot_students bs 
        JOIN classes c ON bs.class_id = c.id 
        WHERE bs.bot_id = ?
        ORDER BY bs.added_at DESC
    """, (bot_id,))
    students = cursor.fetchall()
    conn.close()
    return students

def remove_student(bot_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bot_students WHERE bot_id = ? AND username = ?", (bot_id, username))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_student_by_username(bot_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT bs.class_id, c.name 
        FROM bot_students bs 
        JOIN classes c ON bs.class_id = c.id 
        WHERE bs.bot_id = ? AND bs.username = ?
    """, (bot_id, username))
    result = cursor.fetchone()
    conn.close()
    return result

def add_additional_material(bot_id, class_id, title, description, content, file_path=None, file_type=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO additional_materials (bot_id, class_id, title, description, content, file_path, file_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (bot_id, class_id, title, description, content, file_path, file_type))
    material_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return material_id

def get_additional_materials(bot_id, class_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if class_id:
        cursor.execute("""
            SELECT id, title, description, content, file_path, file_type 
            FROM additional_materials 
            WHERE bot_id = ? AND class_id = ?
            ORDER BY created_at DESC
        """, (bot_id, class_id))
    else:
        cursor.execute("""
            SELECT id, title, description, content, file_path, file_type 
            FROM additional_materials 
            WHERE bot_id = ?
            ORDER BY created_at DESC
        """, (bot_id,))
    
    materials = cursor.fetchall()
    conn.close()
    return materials

def get_additional_material(material_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM additional_materials WHERE id = ?", (material_id,))
    material = cursor.fetchone()
    conn.close()
    return material

def delete_additional_material(material_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Получаем информацию о файле перед удалением
    material = get_additional_material(material_id)
    if material and material[6]:  # file_path
        file_path = material[6]
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logging.error(f"Ошибка при удалении файла: {e}")
    
    cursor.execute("DELETE FROM additional_materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()
    return True# database.py