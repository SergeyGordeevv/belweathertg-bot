import os
import telebot
import requests
import time
import threading
from flask import Flask
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === ВСЕ ДАННЫЕ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
CHAT_ID = -1003811989111

if not BOT_TOKEN or not WEATHER_API_KEY:
    raise ValueError("BOT_TOKEN или WEATHER_API_KEY не заданы!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === НОРМАЛИЗАЦИЯ ЛОГОЙСКА ===
def normalize_city(city):
    if city.lower() in ["логойск", "logoysk", "lahoysk"]:
        return "lahoysk"
    return city

# === ПОГОДА ===
def get_weather(city):
    city = normalize_city(city)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return None
        temp = round(data['main']['temp'])
        feels = round(data['main']['feels_like'])
        desc = data['weather'][0]['description'].capitalize()
        humidity = data['main']['humidity']
        wind = round(data['wind']['speed'])
        return f"🌡️ {temp}°C (ощущается {feels}°C)\n{desc}\n💧 Влажность: {humidity}%\n💨 Ветер: {wind} м/с"
    except:
        return None

def get_forecast(city, days=1):
    city = normalize_city(city)
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != '200':
            return None
        target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        for item in data['list']:
            if item['dt_txt'].startswith(target_date):
                temp = round(item['main']['temp'])
                desc = item['weather'][0]['description'].capitalize()
                return f"🌡️ {temp}°C\n{desc}"
        return "Прогноз на этот день не найден."
    except:
        return None

def get_daily_forecast(city, days=3):
    city = normalize_city(city)
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != '200':
            return None
        result = []
        seen_dates = set()
        for item in data['list']:
            date = item['dt_txt'].split(' ')[0]
            if date not in seen_dates and len(seen_dates) < days:
                seen_dates.add(date)
                day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%a')
                temp = round(item['main']['temp'])
                desc = item['weather'][0]['description'].capitalize()
                result.append(f"{day_name}: {temp}°C, {desc}")
        return '\n'.join(result) if result else None
    except:
        return None

# === СОВЕТ ДНЯ ===
def get_tip(temp):
    if temp is None:
        return ""
    if temp < 0:
        return "🧥 Очень холодно! Одевайся тепло, не забудь шапку и перчатки."
    elif temp < 10:
        return "🧣 Прохладно. Лучше надеть куртку и взять зонт."
    elif temp < 20:
        return "👕 Приятная погода. Можно гулять в кофте или лёгкой куртке."
    elif temp < 30:
        return "☀️ Тепло! Футболка, шорты или лёгкое платье. Не забудь очки."
    else:
        return "🥵 Жарко! Пей воду, носи лёгкую одежду и избегай солнца."

# === КНОПКИ ===
def weather_buttons():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🌤️ Сегодня", callback_data='today'),
        InlineKeyboardButton("🌥️ Завтра", callback_data='tomorrow'),
        InlineKeyboardButton("📅 3 дня", callback_data='3days')
    )
    return keyboard

# === КОМАНДЫ ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🌤️ *Погодный бот для семьи!*\n\n"
        "Напиши название города (например, *Минск*, *Брест*, *Логойск*)\n"
        "Или нажми кнопку ниже, чтобы увидеть погоду в Бресте и Логойске.",
        parse_mode='Markdown',
        reply_markup=weather_buttons()
    )

@bot.message_handler(func=lambda message: True)
def handle_weather_request(message):
    city = message.text.strip()
    if city.lower() in ["сегодня", "завтра", "3 дня"]:
        bot.reply_to(message, "Используй кнопки ниже 👇", reply_markup=weather_buttons())
        return
    if city.lower() == "оба города":
        bot.reply_to(message, "❌ Кнопки показывают сразу оба города. Выбери 'Сегодня', 'Завтра' или '3 дня'.")
        return

    w = get_weather(city)
    if w:
        # Достаём температуру для совета
        temp_str = w.split("🌡️ ")[1].split("°")[0] if "🌡️ " in w else None
        temp = int(temp_str) if temp_str and temp_str.lstrip('-').isdigit() else None
        tip = get_tip(temp)
        text = f"🌤️ *{city}* сейчас:\n{w}\n\n💡 *Совет дня:* {tip}"
        bot.reply_to(message, text, parse_mode='Markdown', reply_markup=weather_buttons())
    else:
        bot.reply_to(message, f"❌ Не удалось получить погоду для '{city}'. Проверь название.")

# === ОБРАБОТКА КНОПОК ===
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cities = {"Брест": "Brest", "Логойск": "lahoysk"}
    if call.data == 'today':
        text = "🌤️ *Погода сегодня:*\n\n"
        for name, eng in cities.items():
            w = get_weather(eng)
            text += f"*{name}:*\n{w}\n\n" if w else f"*{name}:* ❌ Ошибка\n\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=weather_buttons())
    elif call.data == 'tomorrow':
        text = "🌥️ *Погода завтра:*\n\n"
        for name, eng in cities.items():
            f = get_forecast(eng, 1)
            text += f"*{name}:*\n{f}\n\n" if f else f"*{name}:* ❌ Нет данных\n\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=weather_buttons())
    elif call.data == '3days':
        text = "📅 *Прогноз на 3 дня:*\n\n"
        for name, eng in cities.items():
            f = get_daily_forecast(eng, 3)
            text += f"*{name}:*\n{f}\n\n" if f else f"*{name}:* ❌ Нет данных\n\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=weather_buttons())
    bot.answer_callback_query(call.id)

# === УТРЕННЯЯ РАССЫЛКА ===
def morning_broadcast():
    while True:
        now = datetime.now()
        if now.hour == 6 and now.minute == 0:
            cities = {"Брест": "Brest", "Логойск": "lahoysk"}
            text = "🌅 *Доброе утро!*\n\nПогода сегодня:\n\n"
            for name, eng in cities.items():
                w = get_weather(eng)
                text += f"*{name}:*\n{w}\n\n" if w else f"*{name}:* ❌ Ошибка\n\n"
            try:
                bot.send_message(CHAT_ID, text, parse_mode='Markdown')
            except Exception as e:
                print(f"Ошибка утренней рассылки: {e}")
        time.sleep(60)

# === FLASK ===
@app.route('/')
def index():
    return "🌤️ Погодный бот работает"

@app.route('/health')
def health():
    return "OK", 200

# === ЗАПУСК ===
if __name__ == "__main__":
    print("=" * 40)
    print("🌤️ ПОГОДНЫЙ БОТ ЗАПУЩЕН")
    print("=" * 40)

    threading.Thread(target=morning_broadcast, daemon=True).start()

    def run_bot():
        print("🤖 Бот запущен и ждёт сообщений...")
        bot.infinity_polling()

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Веб-сервер на порту {port}")
    app.run(host="0.0.0.0", port=port)
