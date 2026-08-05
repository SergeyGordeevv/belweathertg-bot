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
CHAT_ID = -1003811989111

if not WEATHER_API_KEY:
    raise ValueError("Не задан WEATHER_API_KEY! Добавь его в переменные окружения Render.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

last_city = None

# === ФУНКЦИИ ПОГОДЫ ===
def get_weather_by_city(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return None
        return data
    except:
        return None

def get_weather_by_coords(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return None
        return data
    except:
        return None

def parse_weather_data(data):
    try:
        temp = round(data['main']['temp'])
        feels = round(data['main']['feels_like'])
        desc = data['weather'][0]['description'].capitalize()
        humidity = data['main']['humidity']
        wind = round(data['wind']['speed'])
        return temp, feels, desc, humidity, wind
    except:
        return None

def get_forecast_data(city, days=1):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != '200':
            return None
        target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        for item in data['list']:
            if item['dt_txt'].startswith(target_date):
                return item
        return None
    except:
        return None

def get_forecast_by_coords(lat, lon, days=1):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != '200':
            return None
        target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        for item in data['list']:
            if item['dt_txt'].startswith(target_date):
                return item
        return None
    except:
        return None

def get_daily_forecast_by_city(city, days=3):
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

def get_daily_forecast_by_coords(lat, lon, days=3):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
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

# === ГЕНЕРАЦИЯ СОВЕТОВ ПО ОДЕЖДЕ И ПОГОДЕ ===
def get_dressing_advice(temp, feels, desc, wind, humidity):
    advice = []
    # Температура
    if temp <= -15:
        advice.append("🥶 Очень холодно! Одевайся максимально тепло: пуховик, шапка, шарф, варежки.")
    elif temp <= -5:
        advice.append("❄️ Холодно! Надень зимнюю куртку, шапку и перчатки.")
    elif temp <= 5:
        advice.append("🧥 Прохладно. Пальто или куртка, шапка и шарф не помешают.")
    elif temp <= 12:
        advice.append("🧥 Свежо. Лёгкая куртка или толстовка, возможно, зонт.")
    elif temp <= 18:
        advice.append("👕 Умеренно тепло. Хорошо подойдут лёгкая куртка или ветровка.")
    elif temp <= 25:
        advice.append("☀️ Тепло! Футболка, шорты или лёгкое платье. Не забудь очки.")
    else:
        advice.append("🥵 Жарко! Лёгкая одежда из натуральных тканей, пей больше воды.")

    # Осадки
    if "дождь" in desc.lower():
        advice.append("☔ Не забудь зонт или дождевик!")
    elif "снег" in desc.lower():
        advice.append("🌨️ Ожидается снег – надень непромокаемую обувь и тёплые носки.")
    elif "гроза" in desc.lower():
        advice.append("⚡ Гроза! Постарайся оставаться в помещении.")

    # Ветер
    if wind >= 10:
        advice.append("💨 Ветрено! Надень ветровку или куртку с капюшоном.")
    elif wind >= 6:
        advice.append("💨 Ветер свежий, желательно закрывать уши.")

    # Влажность
    if humidity > 80 and temp > 5:
        advice.append("💦 Влажно – может быть душно, одежда должна дышать.")

    # Если нет специальных советов, добавим общий
    if not advice:
        advice.append("🌤️ Отличная погода, наслаждайся днём!")

    return "\n".join(advice)

# === КНОПКИ ===
def period_buttons():
    keyboard = InlineKeyboardMarkup(row_width=3)
    btn1 = InlineKeyboardButton("🌤️ Сегодня", callback_data='today')
    btn2 = InlineKeyboardButton("🌥️ Завтра", callback_data='tomorrow')
    btn3 = InlineKeyboardButton("📅 3 дня", callback_data='3days')
    keyboard.add(btn1, btn2, btn3)
    return keyboard

# === /start ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🌤️ *Погодный бот с советами!*\n\n"
        "Напиши название города (например, *Минск*, *Брест*, *Гродно*)\n"
        "Затем выбери период на кнопках ниже.",
        parse_mode='Markdown',
        reply_markup=period_buttons()
    )

# === ВВОД ГОРОДА ===
@bot.message_handler(func=lambda message: True)
def handle_city_input(message):
    global last_city
    city = message.text.strip()
    if city.lower() in ["сегодня", "завтра", "3 дня"]:
        bot.reply_to(message, "Напиши сначала город, а затем нажимай кнопки.", reply_markup=period_buttons())
        return

    # Проверяем, есть ли такой город (пробуем по названию)
    data = get_weather_by_city(city)
    if data:
        last_city = city
        temp, feels, desc, humidity, wind = parse_weather_data(data)
        advice = get_dressing_advice(temp, feels, desc, wind, humidity)
        response = f"🌤️ *{city}* сейчас:\n"
        response += f"🌡️ {temp}°C (ощущается {feels}°C)\n{desc}\n"
        response += f"💧 Влажность: {humidity}%\n💨 Ветер: {wind} м/с\n\n"
        response += f"💡 *Совет дня:*\n{advice}\n\n"
        response += "Теперь выбери период на кнопках 👇"
        bot.reply_to(message, response, parse_mode='Markdown', reply_markup=period_buttons())
    else:
        # Если не нашли, может быть Логойск через координаты
        if city.lower() == "логойск":
            data = get_weather_by_coords(54.2035, 27.8520)
            if data:
                last_city = "Логойск"
                temp, feels, desc, humidity, wind = parse_weather_data(data)
                advice = get_dressing_advice(temp, feels, desc, wind, humidity)
                response = f"🌤️ *Логойск* сейчас:\n"
                response += f"🌡️ {temp}°C (ощущается {feels}°C)\n{desc}\n"
                response += f"💧 Влажность: {humidity}%\n💨 Ветер: {wind} м/с\n\n"
                response += f"💡 *Совет дня:*\n{advice}\n\n"
                response += "Теперь выбери период на кнопках 👇"
                bot.reply_to(message, response, parse_mode='Markdown', reply_markup=period_buttons())
                return
        bot.reply_to(message, f"❌ Город '{city}' не найден. Проверь название или попробуй другой.")

# === ОБРАБОТКА КНОПОК ===
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global last_city
    if not last_city:
        bot.answer_callback_query(call.id, "Сначала напиши название города!", show_alert=True)
        return

    city = last_city
    if call.data == 'today':
        # Получаем текущую погоду
        if city.lower() == "логойск":
            data = get_weather_by_coords(54.2035, 27.8520)
        else:
            data = get_weather_by_city(city)
        if data:
            temp, feels, desc, humidity, wind = parse_weather_data(data)
            advice = get_dressing_advice(temp, feels, desc, wind, humidity)
            response = f"🌤️ *{city}* сегодня:\n"
            response += f"🌡️ {temp}°C (ощущается {feels}°C)\n{desc}\n"
            response += f"💧 Влажность: {humidity}%\n💨 Ветер: {wind} м/с\n\n"
            response += f"💡 *Совет дня:*\n{advice}"
            bot.edit_message_text(response, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=period_buttons())
        else:
            bot.answer_callback_query(call.id, "Не удалось получить погоду.", show_alert=True)

    elif call.data == 'tomorrow':
        if city.lower() == "логойск":
            item = get_forecast_by_coords(54.2035, 27.8520, 1)
        else:
            item = get_forecast_data(city, 1)
        if item:
            temp = round(item['main']['temp'])
            desc = item['weather'][0]['description'].capitalize()
            # Краткий совет для завтра
            if "дождь" in desc.lower():
                advice = "☔ Возможен дождь, возьми зонт."
            elif "снег" in desc.lower():
                advice = "🌨️ Ожидается снег, одевайся теплее."
            elif temp < 5:
                advice = "🧥 Завтра холодно, одевайся теплее."
            elif temp > 20:
                advice = "☀️ Завтра тепло, можно легко одеться."
            else:
                advice = "🌤️ Погода без сюрпризов, наслаждайся днём."
            response = f"🌥️ *{city}* завтра:\n"
            response += f"🌡️ {temp}°C\n{desc}\n\n"
            response += f"💡 *Совет:* {advice}"
            bot.edit_message_text(response, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=period_buttons())
        else:
            bot.answer_callback_query(call.id, "Нет данных на завтра.", show_alert=True)

    elif call.data == '3days':
        if city.lower() == "логойск":
            forecast = get_daily_forecast_by_coords(54.2035, 27.8520, 3)
        else:
            forecast = get_daily_forecast_by_city(city, 3)
        if forecast:
            response = f"📅 *{city}* на 3 дня:\n\n{forecast}\n\n"
            # Дадим общий совет на основе первого дня (приблизительно)
            # Можно добавить условный совет, но оставим кратким
            response += "💡 Следи за погодой каждый день и одевайся по сезону!"
            bot.edit_message_text(response, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=period_buttons())
        else:
            bot.answer_callback_query(call.id, "Нет данных на 3 дня.", show_alert=True)

    bot.answer_callback_query(call.id)

# === УТРЕННЯЯ РАССЫЛКА ===
def morning_broadcast():
    while True:
        now = datetime.now()
        if now.hour == 6 and now.minute == 0:
            # Брест
            brest_data = get_weather_by_city("Brest")
            # Логойск
            logoysk_data = get_weather_by_coords(54.2035, 27.8520)

            text = "🌅 *Доброе утро!*\n\n"

            if brest_data:
                temp, feels, desc, humidity, wind = parse_weather_data(brest_data)
                advice = get_dressing_advice(temp, feels, desc, wind, humidity)
                text += f"*Брест сегодня:*\n🌡️ {temp}°C (ощущается {feels}°C)\n{desc}\n"
                text += f"💧 {humidity}%  💨 {wind} м/с\n💡 {advice}\n\n"
            else:
                text += "*Брест:* ❌ Ошибка\n\n"

            if logoysk_data:
                temp, feels, desc, humidity, wind = parse_weather_data(logoysk_data)
                advice = get_dressing_advice(temp, feels, desc, wind, humidity)
                text += f"*Логойск сегодня:*\n🌡️ {temp}°C (ощущается {feels}°C)\n{desc}\n"
                text += f"💧 {humidity}%  💨 {wind} м/с\n💡 {advice}\n\n"
            else:
                text += "*Логойск:* ❌ Ошибка\n\n"

            try:
                bot.send_message(CHAT_ID, text, parse_mode='Markdown')
            except Exception as e:
                print(f"Ошибка утренней рассылки: {e}")
        time.sleep(60)

# === FLASK ===
@app.route('/')
def index():
    return "🌤️ Погодный бот с советами работает"

@app.route('/health')
def health():
    return "OK", 200

# === ЗАПУСК ===
if __name__ == "__main__":
    print("=" * 40)
    print("🌤️ ПОГОДНЫЙ БОТ С СОВЕТАМИ ЗАПУЩЕН")
    print("=" * 40)

    threading.Thread(target=morning_broadcast, daemon=True).start()

    def run_bot():
        print("🤖 Бот запущен и ждёт сообщений...")
        bot.infinity_polling()

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Веб-сервер на порту {port}")
    app.run(host="0.0.0.0", port=port)
