import os
import telebot
import requests
import time
import threading
from flask import Flask
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === ТВОИ ДАННЫЕ ===
BOT_TOKEN = "8896032923:AAEknV_8BncvHKO_555q41qwTUwNEW75sYM"
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
CHAT_ID = -1003811989111

if not WEATHER_API_KEY:
    raise ValueError("Не задан WEATHER_API_KEY! Добавь его в переменные окружения Render.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === ФУНКЦИИ ПОГОДЫ ===
def get_weather(city):
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

# === КНОПКИ ===
def weather_buttons():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🌤️ Сегодня", callback_data='today')
    btn2 = InlineKeyboardButton("🌥️ Завтра", callback_data='tomorrow')
    btn3 = InlineKeyboardButton("📅 3 дня", callback_data='3days')
    btn4 = InlineKeyboardButton("🏠 Оба города", callback_data='both')
    keyboard.add(btn1, btn2, btn3, btn4)
    return keyboard

# === КОМАНДЫ ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🌤️ *Погодный бот для семьи!*\n\n"
        "Я покажу погоду в Бресте и Логойске.\n"
        "Выбери действие ниже 👇",
        parse_mode='Markdown',
        reply_markup=weather_buttons()
    )

@bot.message_handler(commands=['weather'])
def weather_cmd(message):
    bot.reply_to(message, "Выбери город и период:", reply_markup=weather_buttons())

# === ОБРАБОТКА НАЖАТИЙ ===
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # ИСПРАВЛЕНО: Логойск с кодом страны
    cities = {"Брест": "Brest", "Логойск": "Lahojsk,BY"}
    if call.data == 'today':
        text = "🌤️ *Погода сегодня:*\n\n"
        for name, eng in cities.items():
            w = get_weather(eng)
            if w:
                text += f"*{name}:*\n{w}\n\n"
            else:
                text += f"*{name}:* ❌ Ошибка\n\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=weather_buttons())
    elif call.data == 'tomorrow':
        text = "🌥️ *Погода завтра:*\n\n"
        for name, eng in cities.items():
            f = get_forecast(eng, 1)
            if f:
                text += f"*{name}:*\n{f}\n\n"
            else:
                text += f"*{name}:* ❌ Нет данных\n\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=weather_buttons())
    elif call.data == '3days':
        text = "📅 *Прогноз на 3 дня:*\n\n"
        for name, eng in cities.items():
            f = get_daily_forecast(eng, 3)
            if f:
                text += f"*{name}:*\n{f}\n\n"
            else:
                text += f"*{name}:* ❌ Нет данных\n\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=weather_buttons())
    elif call.data == 'both':
        text = "🌍 *Сводка по городам:*\n\n"
        for name, eng in cities.items():
            w = get_weather(eng)
            if w:
                text += f"*{name}* сейчас:\n{w}\n\n"
            else:
                text += f"*{name}:* ❌ Ошибка\n\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=weather_buttons())
    bot.answer_callback_query(call.id)

# === УТРЕННЯЯ РАССЫЛКА ===
def morning_broadcast():
    while True:
        now = datetime.now()
        if now.hour == 6 and now.minute == 0:
            cities = {"Брест": "Brest", "Логойск": "Lahojsk,BY"}
            text = "🌅 *Доброе утро!*\n\nПогода сегодня:\n\n"
            for name, eng in cities.items():
                w = get_weather(eng)
                if w:
                    text += f"*{name}:*\n{w}\n\n"
                else:
                    text += f"*{name}:* ❌ Ошибка\n\n"
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
        bot.remove_webhook()
        bot.infinity_polling()

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Веб-сервер на порту {port}")
    app.run(host="0.0.0.0", port=port)
