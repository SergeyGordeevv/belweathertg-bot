import asyncio
import json
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp

# ---------- КОНФИГУРАЦИЯ ----------
TOKEN = os.environ.get("BOT_TOKEN")          # Токен бота (Render)
OWM_API_KEY = os.environ.get("OWM_API_KEY")  # API-ключ OpenWeatherMap (Render)
DATA_FILE = "chats_data.json"                # Файл с настройками чатов

if not TOKEN or not OWM_API_KEY:
    raise ValueError("Переменные окружения BOT_TOKEN и/или OWM_API_KEY не заданы!")

# Загружаем/сохраняем данные чатов
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

chats = load_data()

# ---------- ФУНКЦИИ ПОГОДЫ ----------
async def get_weather(city: str):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OWM_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

def degrees_to_direction(deg):
    dirs = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
    ix = round(deg / 45) % 8
    return dirs[ix]

def get_recommendation(temp, humidity, wind_speed, desc):
    rec = []
    # Одежда
    if temp <= -10:
        rec.append("🧥 Очень холодно: пуховик, шапка, шарф, перчатки.")
    elif -10 < temp <= 0:
        rec.append("🧣 Холодно: тёплая куртка, шапка, перчатки.")
    elif 0 < temp <= 10:
        rec.append("🧥 Прохладно: куртка или плотная кофта.")
    elif 10 < temp <= 18:
        rec.append("👕 Лёгкая куртка, ветровка или свитер.")
    elif 18 < temp <= 25:
        rec.append("👕 Комфортно: футболка, лёгкие брюки/юбка.")
    elif 25 < temp <= 32:
        rec.append("🩳 Тепло: шорты, платье, солнечные очки.")
    else:
        rec.append("🔥 Жарко: максимально лёгкая одежда, головной убор.")

    low_desc = desc.lower()
    if any(w in low_desc for w in ["дождь", "ливень", "морось", "гроза"]):
        rec.append("☔️ Ожидается дождь — обязательно возьмите зонт!")
    elif "снег" in low_desc:
        rec.append("❄️ Снегопад — одевайтесь теплее, обувь нескользящая.")
    elif "туман" in low_desc:
        rec.append("🌫 Туман — будьте внимательны на дорогах.")

    if wind_speed > 12:
        rec.append("💨 Сильный ветер — одежда должна быть непродуваемой.")
    elif wind_speed > 8:
        rec.append("🌬 Ветрено — рекомендую ветровку.")
    return "\n".join(rec)

def format_weather(data: dict, city: str) -> str:
    main = data["main"]
    wind = data["wind"]
    weather_desc = data["weather"][0]
    clouds = data["clouds"]["all"]
    visibility = data.get("visibility", "—")

    temp = main["temp"]
    feels = main["feels_like"]
    humidity = main["humidity"]
    pressure = main["pressure"]
    wind_speed = wind.get("speed", 0)
    wind_deg = wind.get("deg", 0)
    wind_dir = degrees_to_direction(wind_deg)
    desc = weather_desc["description"].capitalize()

    vis_km = f"{visibility / 1000:.1f} км" if isinstance(visibility, int) else "—"

    text = (
        f"🌤 <b>Погода на сегодня — {city}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🌡 Температура: <b>{temp}°C</b> (ощущается как {feels}°C)\n"
        f"💧 Влажность: {humidity}%\n"
        f"🌀 Давление: {pressure} гПа\n"
        f"🌬 Ветер: {wind_speed} м/с, {wind_dir}\n"
        f"☁️ Облачность: {clouds}%\n"
        f"👀 Видимость: {vis_km}\n"
        f"📝 Описание: {desc}\n"
        f"━━━━━━━━━━━━━━━━\n"
    )
    text += get_recommendation(temp, humidity, wind_speed, desc)
    return text

# ---------- КОМАНДЫ БОТА ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Я бот погоды для группы.\n"
        "Команды:\n"
        "/setcity <город> — выбрать город\n"
        "/settz <часы> — часовой пояс относительно UTC (например, 3 для Москвы)\n"
        "/weather — показать погоду прямо сейчас\n"
        "/help — эта справка"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    args = context.args
    if not args:
        await update.message.reply_text("❌ Использование: /setcity Москва")
        return
    city = " ".join(args)
    data = await get_weather(city)
    if data is None:
        await update.message.reply_text(f"❌ Город '{city}' не найден. Проверьте название.")
        return
    if chat_id not in chats:
        chats[chat_id] = {}
    chats[chat_id]["city"] = city
    if "tz" not in chats[chat_id]:
        chats[chat_id]["tz"] = 3
    save_data(chats)
    await update.message.reply_text(f"✅ Город установлен: {city}")

async def set_tz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    args = context.args
    if not args:
        await update.message.reply_text("❌ Использование: /settz 3 (для Москвы UTC+3)")
        return
    try:
        tz = float(args[0])
    except ValueError:
        await update.message.reply_text("❌ Часовой пояс должен быть числом (например, 3, -5).")
        return
    if chat_id not in chats:
        chats[chat_id] = {}
    chats[chat_id]["tz"] = tz
    save_data(chats)
    await update.message.reply_text(f"✅ Часовой пояс UTC{tz:+g} установлен.")

async def weather_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in chats or "city" not in chats[chat_id]:
        await update.message.reply_text("❌ Сначала установите город: /setcity <название>")
        return
    city = chats[chat_id]["city"]
    data = await get_weather(city)
    if data is None:
        await update.message.reply_text("⚠️ Не удалось получить погоду. Попробуйте позже.")
        return
    text = format_weather(data, city)
    await update.message.reply_text(text, parse_mode="HTML")

# ---------- УТРЕННЯЯ РАССЫЛКА ----------
async def morning_broadcast(bot_app):
    now_utc = datetime.utcnow()
    for chat_id, settings in list(chats.items()):
        city = settings.get("city")
        tz = settings.get("tz", 3)
        if not city:
            continue
        local_time = now_utc + timedelta(hours=tz)
        if local_time.hour == 6 and local_time.minute < 5:
            last_date = settings.get("last_sent_date")
            today_str = local_time.strftime("%Y-%m-%d")
            if last_date == today_str:
                continue
            data = await get_weather(city)
            if data is None:
                continue
            text = format_weather(data, city)
            try:
                await bot_app.bot.send_message(chat_id=int(chat_id), text=text, parse_mode="HTML")
                chats[chat_id]["last_sent_date"] = today_str
                save_data(chats)
            except Exception as e:
                print(f"Ошибка отправки в чат {chat_id}: {e}")

# ---------- ГЛАВНАЯ ФУНКЦИЯ ----------
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setcity", set_city))
    app.add_handler(CommandHandler("settz", set_tz))
    app.add_handler(CommandHandler("weather", weather_now))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(morning_broadcast, 'interval', minutes=5, args=[app])
    scheduler.start()

    print("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
