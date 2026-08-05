import os
import telebot
import requests
import time
import threading
from flask import Flask
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === ТВОЙ НОВЫЙ ТОКЕН ===
BOT_TOKEN = "8896032923:AAG2iABXbLJOW9PEhnBluChgf60IoWeZvPk"
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
CHAT_ID = -1003811989111  # ID группы

if not WEATHER_API_KEY:
    raise ValueError("Не задан WEATHER_API_KEY! Добавь его в переменные окружения Render.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Глобальная переменная для хранения последнего города
last_city = None

# === ФУНКЦИИ ПОГОДЫ ===

def get_weather_by_city(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return None
        return parse_weather_data(data)
    except:
        return None

def get_weather_by_coords(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return None
        return parse_weather_data(data)
    except:
        return None

def parse_weather_data(data):
    try:
        temp = round(data['main']['temp'])
        feels = round(data['main']['feels_like'])
        desc = data['weather'][0]['description'].capitalize()
        humidity = data['main']['humidity']
        wind = round(data['wind']['speed'])
        return f"🌡️ {temp}°C (ощущается {feels}°C)\n{desc}\n💧 Влажность: {humidity}%\n💨 Ветер: {wind} м/с"
    except:
        return None

def get_forecast_by_city(city, days=1):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != '200':
            return None
        return parse_forecast_data(data, days)
    except:
        return None

def get_forecast_by_coords(lat, lon, days=1):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != '200':
            return None
        return parse_forecast_data(data, days)
    except:
        return None

def parse_forecast_data(data, days=1):
    try:
        target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        for item in data['list']:
            if item['dt_txt'].startswith(target_date):
                temp = round(item['main']['temp'])
                desc = item['weather'][0]['description'].capitalize()
                return f"🌡️ {temp}°C\n{desc}"
        return "Прогноз на этот день не найден."
    except:
        return None

def get_daily_forecast_by_city(city, days=3):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != '200':
            return None
        return parse_daily_forecast(data, days)
    except:
        return None

def get_daily_forecast_by_coords(lat, lon, days=3):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != '200':
            return None
        return parse_daily_forecast(data, days)
    except:
        return None

def parse_daily_forecast(data, days=3):
    try:
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

# === КНОПКИ (только сегодня, завтра, 3 дня) ===
def period_buttons():
    keyboard = InlineKeyboardMarkup(row_width=3)
    btn1 = InlineKeyboardButton("🌤️ Сегодня", callback_data='today')
    btn2 = InlineKeyboardButton("🌥️ Завтра", callback_data='tomorrow')
    btn3 = InlineKeyboardButton("📅 3 дня", callback_data='3days')
    keyboard.add(btn1, btn2, btn3)
    return keyboard

# === КОМАНДА /start ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🌤️ *Погодный бот*\n\n"
        "Просто напиши название города (например, *Минск*, *Гродно*, *Брест*)\n"
        "Затем нажми на кнопку, чтобы узнать погоду на нужный период.",
        parse_mode='Markdown',
        reply_markup=period_buttons()
    )

# === ОБРАБОТКА ВВОДА ГОРОДА ===
@bot.message_handler(func=lambda message: True)
def handle_city_input(message):
    global last_city
    city = message.text.strip()
    # Проверяем, является ли сообщение командой кнопки (чтобы не обрабатывать как город)
    if city.lower() in ["сегодня", "завтра", "3 дня"]:
        bot.reply_to(message, "Используй кнопки ниже 👇", reply_markup=period_buttons())
        return
    # Проверяем погоду для введённого города
    w = get_weather_by_city(city)
    if w:
        last_city = city  # запоминаем город
        bot.reply_to(
            message,
            f"🌤️ *{city}* сейчас:\n{w}\n\nТеперь выбери период на кнопках 👇",
            parse_mode='Markdown',
            reply_markup=period_buttons()
        )
    else:
        # Если не нашли по названию, пробуем как Логойск (по координатам)
        if city.lower() == "логойск":
            w = get_weather_by_coords(54.2035, 27.8520)
            if w:
                last_city = "Логойск"
                bot.reply_to(
                    message,
                    f"🌤️ *Логойск* сейчас:\n{w}\n\nТеперь выбери период на кнопках 👇",
                    parse_mode='Markdown',
                    reply_markup=period_buttons()
                )
                return
        bot.reply_to(message, f"❌ Город '{city}' не найден. Проверь название или попробуй другой.")

# === ОБРАБОТКА НАЖАТИЙ КНОПОК ===
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global last_city
    if not last_city:
        bot.answer_callback_query(call.id, "Сначала напиши название города!", show_alert=True)
        return

    city = last_city
    # Если город Логойск, используем координаты для точности
    if city.lower() == "логойск":
        lat, lon = 54.2035, 27.8520
        if call.data == 'today':
            w = get_weather_by_coords(lat, lon)
        elif call.data == 'tomorrow':
            w = get_forecast_by_coords(lat, lon, 1)
        elif call.data == '3days':
            w = get_daily_forecast_by_coords(lat, lon, 3)
        else:
            w = None
    else:
        if call.data == 'today':
            w = get_weather_by_city(city)
        elif call.data == 'tomorrow':
            w = get_forecast_by_city(city, 1)
        elif call.data == '3days':
            w = get_daily_forecast_by_city(city, 3)
        else:
            w = None

    if w:
        if call.data == 'today':
            header = f"🌤️ *{city}* сегодня:"
        elif call.data == 'tomorrow':
            header = f"🌥️ *{city}* завтра:"
        elif call.data == '3days':
            header = f"📅 *{city}* на 3 дня:"
        else:
            header = ""
        bot.edit_message_text(
            f"{header}\n\n{w}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=period_buttons()
        )
    else:
        bot.answer_callback_query(call.id, "Не удалось получить прогноз, попробуй позже.", show_alert=True)

    bot.answer_callback_query(call.id)

# === УТРЕННЯЯ РАССЫЛКА (Брест и Логойск) ===
def morning_broadcast():
    while True:
        now = datetime.now()
        if now.hour == 6 and now.minute == 0:
            # Брест (по названию)
            brest = get_weather_by_city("Brest")
            # Логойск (по координатам)
            logoysk = get_weather_by_coords(54.2035, 27.8520)
            text = "🌅 *Доброе утро!*\n\nПогода сегодня:\n\n"
            text += f"*Брест:*\n{brest if brest else '❌ Ошибка'}\n\n"
            text += f"*Логойск:*\n{logoysk if logoysk else '❌ Ошибка'}"
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
        # Убираем remove_webhook, чтобы не вызывать конфликт
        bot.infinity_polling()

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Веб-сервер на порту {port}")
    app.run(host="0.0.0.0", port=port)
