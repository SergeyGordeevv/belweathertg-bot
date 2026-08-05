import os
import telebot
import requests
import time
import threading
from flask import Flask
from datetime import datetime

# === НАСТРОЙКИ (берутся из переменных окружения) ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

if not BOT_TOKEN or not WEATHER_API_KEY:
    raise ValueError("Не заданы BOT_TOKEN или WEATHER_API_KEY!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === ФУНКЦИЯ ПОГОДЫ ===
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return f"❌ Город '{city}' не найден. Проверь название."
        temp = round(data['main']['temp'])
        feels = round(data['main']['feels_like'])
        desc = data['weather'][0]['description'].capitalize()
        humidity = data['main']['humidity']
        wind = round(data['wind']['speed'])
        return f"""🌤️ *{city.capitalize()}* сейчас:
🌡️ {temp}°C (ощущается {feels}°C)
📖 {desc}
💧 Влажность: {humidity}%
💨 Ветер: {wind} м/с"""
    except Exception as e:
        return f"❌ Ошибка получения погоды: {e}"

# === КОМАНДЫ БОТА ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🌤️ Привет! Я бот погоды.\n\n"
        "Просто напиши название города (например, *Минск* или *Логойск*), и я покажу погоду.",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)
def any_message(message):
    city = message.text.strip()
    bot.reply_to(message, get_weather(city), parse_mode='Markdown')

# === FLASK ДЛЯ RENDER ===
@app.route('/')
def index():
    return "🌤️ Погодный бот работает!"

@app.route('/health')
def health():
    return "OK", 200

# === ЗАПУСК ===
if __name__ == "__main__":
    print("=" * 40)
    print("🌤️ ПОГОДНЫЙ БОТ ЗАПУЩЕН")
    print("=" * 40)

    # Запускаем бота в фоновом потоке
    def run_bot():
        print("🤖 Бот запущен и ждёт сообщений...")
        bot.infinity_polling()

    threading.Thread(target=run_bot, daemon=True).start()

    # Запускаем веб-сервер для Render
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Веб-сервер на порту {port}")
    app.run(host="0.0.0.0", port=port)
