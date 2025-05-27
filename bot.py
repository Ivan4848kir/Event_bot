import telebot
from telebot import types
import config
import os
from datetime import datetime
import threading
import time

bot = telebot.TeleBot(config.BOT_TOKEN)

# Инициализация файлов
def init_files():
    if not os.path.exists('schedule.txt'):
        with open('schedule.txt', 'w', encoding='utf-8') as f:
            f.write("""1. "Ромео и Джульетта" - 15 июня, 19:00 - https://example.com/tickets/1
2. "Гамлет" - 16 июня, 18:30 - https://example.com/tickets/2
3. "Щелкунчик" - 17 июня, 20:00 - https://example.com/tickets/3""")

    if not os.path.exists('news.txt'):
        with open('news.txt', 'w', encoding='utf-8') as f:
            f.write("""1. Новая постановка "Ромео и Джульетта" - премьера 15 июня!
2. Скидки на билеты для студентов - 20% при предъявлении студенческого.
3. Наш театр получил премию "Золотая маска"!""")

    if not os.path.exists('subscribers.txt'):
        with open('subscribers.txt', 'w') as f:
            f.write("")

# Чтение/запись данных
def get_schedule():
    with open('schedule.txt', 'r', encoding='utf-8') as f:
        return f.read()

def get_news():
    with open('news.txt', 'r', encoding='utf-8') as f:
        return f.read()

def get_subscribers():
    with open('subscribers.txt', 'r') as f:
        return [int(line.strip()) for line in f if line.strip()]

def add_subscriber(user_id):
    subscribers = get_subscribers()
    if user_id not in subscribers:
        with open('subscribers.txt', 'a') as f:
            f.write(f"{user_id}\n")

def remove_subscriber(user_id):
    subscribers = get_subscribers()
    if user_id in subscribers:
        subscribers.remove(user_id)
        with open('subscribers.txt', 'w') as f:
            for sub in subscribers:
                f.write(f"{sub}\n")

# Рассылка уведомлений
def send_notification(message_text):
    subscribers = get_subscribers()
    for user_id in subscribers:
        try:
            bot.send_message(user_id, "🔔 Новое уведомление:\n\n" + message_text)
        except Exception as e:
            print(f"Ошибка при отправке уведомления {user_id}: {e}")

# Логирование
def log_action(user_id, action):
    with open('admin_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now()}: User {user_id} {action}\n")

# Команды бота
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📅 Расписание спектаклей")
    btn2 = types.KeyboardButton("📰 Новости театра")
    btn3 = types.KeyboardButton("🎭 О театре")
    btn4 = types.KeyboardButton("🔔 Подписаться на уведомления")
    btn5 = types.KeyboardButton("🔕 Отписаться от уведомлений")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    welcome_text = """Добро пожаловать в театральный бот! Здесь вы можете:
- Узнать расписание спектаклей
- Читать новости театра
- Получать уведомления о новых событиях

Выберите опцию:"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# Обработчик кнопок
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "📅 Расписание спектаклей":
        schedule = get_schedule()
        bot.send_message(message.chat.id, f"📅 Расписание спектаклей:\n\n{schedule}")
        
    elif message.text == "📰 Новости театра":
        news = get_news()
        bot.send_message(message.chat.id, f"📰 Последние новости:\n\n{news}")
        
    elif message.text == "🎭 О театре":
        about_text = """🎭 Наш театр - один из старейших в городе, основан в 1890 году.

Мы предлагаем:
- Классические постановки
- Современные интерпретации
- Детские спектакли
- Экспериментальные работы

Адрес: г. Москва, ул. Театральная, 1
Телефон: +7 (495) 123-45-67"""
        bot.send_message(message.chat.id, about_text)
    
    elif message.text == "🔔 Подписаться на уведомления":
        add_subscriber(message.chat.id)
        bot.send_message(message.chat.id, "✅ Вы подписались на уведомления о новых спектаклях и новостях!")
    
    elif message.text == "🔕 Отписаться от уведомлений":
        remove_subscriber(message.chat.id)
        bot.send_message(message.chat.id, "❌ Вы отписались от уведомлений.")
    
    # Админ-команды
    elif message.from_user.id == config.ADMIN_ID and message.text == "/admin":
        admin_panel(message)
    
    elif message.from_user.id == config.ADMIN_ID and message.text.startswith("/notify"):
        notification_text = message.text.replace("/notify", "").strip()
        if notification_text:
            send_notification(notification_text)
            bot.send_message(message.chat.id, "Уведомление отправлено подписчикам!")
        else:
            bot.send_message(message.chat.id, "Использование: /notify текст_уведомления")

# Админ-панель
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("/update_schedule")
    btn2 = types.KeyboardButton("/update_news")
    btn3 = types.KeyboardButton("/send_notification")
    btn4 = types.KeyboardButton("/stats")
    btn5 = types.KeyboardButton("В главное меню")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    bot.send_message(message.chat.id, "Админ-панель:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.from_user.id == config.ADMIN_ID and message.text == "/update_schedule")
def request_schedule_update(message):
    msg = bot.send_message(message.chat.id, "Отправьте новое расписание:")
    bot.register_next_step_handler(msg, update_schedule)

def update_schedule(message):
    with open('schedule.txt', 'w', encoding='utf-8') as f:
        f.write(message.text)
    bot.send_message(message.chat.id, "Расписание обновлено!")
    log_action(message.from_user.id, "updated schedule")
    
    # Уведомляем подписчиков об изменении расписания
    send_notification("Обновлено расписание спектаклей! Посмотрите новые даты в боте.")

@bot.message_handler(func=lambda message: message.from_user.id == config.ADMIN_ID and message.text == "/update_news")
def request_news_update(message):
    msg = bot.send_message(message.chat.id, "Отправьте новые новости:")
    bot.register_next_step_handler(msg, update_news)

def update_news(message):
    with open('news.txt', 'w', encoding='utf-8') as f:
        f.write(message.text)
    bot.send_message(message.chat.id, "Новости обновлены!")
    log_action(message.from_user.id, "updated news")
    
    # Уведомляем подписчиков о новых новостях
    send_notification("Появились новые новости театра! Читайте в боте.")

@bot.message_handler(func=lambda message: message.from_user.id == config.ADMIN_ID and message.text == "/stats")
def show_stats(message):
    subscribers = get_subscribers()
    bot.send_message(message.chat.id, f"📊 Статистика:\n\nПодписчиков: {len(subscribers)}")

# Проверка новых событий (для автоматических уведомлений)
def check_for_updates():
    last_news_count = 0
    last_schedule_count = 0
    
    while True:
        try:
            # Проверяем новости
            current_news_count = len(get_news().split('\n'))
            if current_news_count > last_news_count and last_news_count > 0:
                send_notification("Добавлены новые новости театра!")
            last_news_count = current_news_count
            
            # Проверяем расписание
            current_schedule_count = len(get_schedule().split('\n'))
            if current_schedule_count > last_schedule_count and last_schedule_count > 0:
                send_notification("Добавлены новые спектакли в расписание!")
            last_schedule_count = current_schedule_count
            
        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")
        
        time.sleep(3600)  # Проверяем каждый час

# Запуск бота
if __name__ == '__main__':
    init_files()
    
    # Запускаем проверку обновлений в отдельном потоке
    update_thread = threading.Thread(target=check_for_updates)
    update_thread.daemon = True
    update_thread.start()
    
    print("Бот запущен...")
    bot.polling(none_stop=True)