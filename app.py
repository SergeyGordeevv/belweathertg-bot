import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import time
import threading
from datetime import datetime

# ============================================
# НАСТРОЙКИ
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748
CHECK_INTERVAL = 300

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

sent_offers = {}
offers_lock = threading.Lock()

# ============================================
# КЛАВИАТУРА
# ============================================
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📋 Показать объявления"),
        KeyboardButton("📊 Статистика")
    )
    keyboard.add(
        KeyboardButton("🔄 Обновить"),
        KeyboardButton("ℹ️ Помощь")
    )
    return keyboard

# ============================================
# ПАРСИНГ KUFAR (УНИВЕРСАЛЬНЫЙ)
# ============================================
def parse_kufar():
    offers = []
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Ищем все ссылки, которые ведут на объявления
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/l/minsk/snyat/kvartiru/' in href and 'page' not in href:
                title = a.text.strip()
                if len(title) > 5:
                    # Пробуем найти цену рядом
                    price_elem = a.find_next('span', class_=lambda x: x and 'price' in x.lower())
                    price = price_elem.text.strip() if price_elem else "Цена не указана"
                    link = "https://re.kufar.by" + href if href.startswith('/') else href
                    offer_text = f"🏠 {title[:50]}\n💰 {price}\n🔗 {link}"
                    offers.append(offer_text)
                    if len(offers) >= 15:
                        break
    except Exception as e:
        print(f"Ошибка Kufar: {e}")
    return offers

# ============================================
# ПАРСИНГ REALT (оставляем как есть)
# ============================================
def parse_realt():
    offers = []
    url = "https://realt.by/rent/flats/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'offer' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://realt.by" + a['href'] if a['href'].startswith('/') else a['href']
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 15:
                    break
    except Exception as e:
        print(f"Ошибка Realt: {e}")
    return offers

# ============================================
# ПАРСИНГ DOMOVITA
# ============================================
def parse_domovita():
    offers = []
    url = "https://domovita.by/minsk/arenda-kvartir/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('offer' in x.lower() or 'item' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://domovita.by" + a['href'] if a['href'].startswith('/') else a['href']
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 15:
                    break
    except Exception as e:
        print(f"Ошибка Domovita: {e}")
    return offers

# ============================================
# ПАРСИНГ NEAGENT
# ============================================
def parse_neagent():
    offers = []
    url = "https://neagent.by/rent/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'offer' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://neagent.by" + a['href'] if a['href'].startswith('/') else a['href']
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 15:
                    break
    except Exception as e:
        print(f"Ошибка Neagent: {e}")
    return offers

# ============================================
# ПАРСИНГ HATA
# ============================================
def parse_hata():
    offers = []
    url = "https://hata.by/logojskij-rajon/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'offer' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://hata.by" + a['href'] if a['href'].startswith('/') else a['href']
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 15:
                    break
    except Exception as e:
        print(f"Ошибка Hata: {e}")
    return offers

# ============================================
# ПАРСИНГ GDE
# ============================================
def parse_gde():
    offers = []
    url = "https://gde.by/arenda/kvartiry/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'offer' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://gde.by" + a['href'] if a['href'].startswith('/') else a['href']
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 15:
                    break
    except Exception as e:
        print(f"Ошибка Gde: {e}")
    return offers

# ============================================
# СБОР ВСЕХ ОБЪЯВЛЕНИЙ
# ============================================
def get_all_offers():
    result = {}
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг (Минская область)...")
    
    sites = {
        "Kufar": parse_kufar,
        "Realt": parse_realt,
        "Domovita": parse_domovita,
        "Neagent": parse_neagent,
        "Hata": parse_hata,
        "Gde": parse_gde,
    }
    
    for name, func in sites.items():
        try:
            offers = func()
            result[name] = set(offers)
            print(f"  {name}: {len(offers)}")
        except Exception as e:
            print(f"  {name}: Ошибка - {e}")
            result[name] = set()
    
    total = sum(len(s) for s in result.values())
    print(f"  Всего: {total}")
    return result

# ============================================
# МОНИТОРИНГ
# ============================================
def monitor_offers():
    global sent_offers
    print("🔄 Мониторинг запущен...")
    
    with offers_lock:
        sent_offers = get_all_offers()
        total = sum(len(s) for s in sent_offers.values())
        print(f"✅ Отслеживается {total} объявлений")
    
    if total > 0:
        try:
            bot.send_message(CHAT_ID, f"📋 ТЕКУЩИЕ ОБЪЯВЛЕНИЯ (всего {total})")
            for site, offers in sent_offers.items():
                if offers:
                    bot.send_message(CHAT_ID, f"🔹 *{site}* — {len(offers)} объявлений", parse_mode='Markdown')
                    for offer in list(offers)[:5]:
                        bot.send_message(CHAT_ID, offer)
                        time.sleep(0.3)
                    if len(offers) > 5:
                        bot.send_message(CHAT_ID, f"... и еще {len(offers)-5} на {site}")
        except Exception as e:
            print(f"Ошибка отправки: {e}")
    
    while True:
        try:
            with offers_lock:
                current_offers = get_all_offers()
                new_by_site = {}
                total_new = 0
                for site, curr_set in current_offers.items():
                    prev_set = sent_offers.get(site, set())
                    new_set = curr_set - prev_set
                    if new_set:
                        new_by_site[site] = new_set
                        total_new += len(new_set)
            
            if total_new > 0:
                print(f"🔔 НОВЫХ: {total_new}")
                bot.send_message(CHAT_ID, f"🔔 НОВЫЕ ОБЪЯВЛЕНИЯ (всего {total_new})")
                for site, new_set in new_by_site.items():
                    bot.send_message(CHAT_ID, f"🔹 *{site}* — {len(new_set)} новых", parse_mode='Markdown')
                    for offer in new_set:
                        bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{offer}")
                        time.sleep(1)
                with offers_lock:
                    for site, curr_set in current_offers.items():
                        sent_offers[site] = curr_set
            else:
                print("Новых объявлений нет")
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")
        
        time.sleep(CHECK_INTERVAL)

# ============================================
# КОМАНДЫ И КНОПКИ
# ============================================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "🏠 *Бот аренды Минской области*\n\n"
        "Я ищу объявления об аренде квартир в Минской области на 6 сайтах.\n\n"
        "📌 *Что умею:*\n"
        "• Показывать текущие объявления с разбивкой по сайтам\n"
        "• Отслеживать новые каждые 5 минут\n"
        "• Присылать уведомления о новых\n\n"
        "👇 *Используй кнопки ниже:*",
        reply_markup=main_keyboard(),
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    with offers_lock:
        total = sum(len(s) for s in sent_offers.values())
        stats_lines = [f"📊 *СТАТИСТИКА*\n\nОбщее объявлений: *{total}*"]
        for site, offers in sent_offers.items():
            stats_lines.append(f"• {site}: *{len(offers)}*")
    bot.send_message(
        message.chat.id,
        "\n".join(stats_lines),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    global sent_offers
    text = message.text
    
    if text == "📋 Показать объявления":
        with offers_lock:
            total = sum(len(s) for s in sent_offers.values())
        if total == 0:
            bot.send_message(message.chat.id, "😕 Пока нет объявлений")
            return
        
        bot.send_message(message.chat.id, f"📋 *ВСЕ ОБЪЯВЛЕНИЯ (всего {total})*", parse_mode='Markdown')
        with offers_lock:
            for site, offers in sent_offers.items():
                if offers:
                    bot.send_message(message.chat.id, f"🔹 *{site}* — {len(offers)} объявлений", parse_mode='Markdown')
                    for offer in list(offers)[:5]:
                        bot.send_message(message.chat.id, offer)
                        time.sleep(0.3)
                    if len(offers) > 5:
                        bot.send_message(message.chat.id, f"... и еще {len(offers)-5} на {site}")
    
    elif text == "📊 Статистика":
        stats_cmd(message)
    
    elif text == "🔄 Обновить":
        bot.send_message(message.chat.id, "🔄 Обновляю объявления...")
        with offers_lock:
            sent_offers = get_all_offers()
            total = sum(len(s) for s in sent_offers.values())
        bot.send_message(
            message.chat.id,
            f"✅ Обновлено! Отслеживается *{total}* объявлений",
            parse_mode='Markdown'
        )
    
    elif text == "ℹ️ Помощь":
        bot.send_message(
            message.chat.id,
            "ℹ️ *Помощь*\n\n"
            "📌 *Команды:*\n"
            "• /start — Главное меню\n"
            "• /stats — Статистика\n\n"
            "📌 *Кнопки:*\n"
            "• Показать объявления — список с разбивкой по сайтам\n"
            "• Статистика — количество по каждому сайту\n"
            "• Обновить — принудительно обновить\n\n"
            "🔄 *Авто-уведомления:* новые объявления приходят сами каждые 5 минут",
            parse_mode='Markdown'
        )
    
    else:
        bot.send_message(
            message.chat.id,
            "🤔 Используй кнопки ниже 👇",
            reply_markup=main_keyboard()
        )

# ============================================
# ВЕБХУК
# ============================================
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
            bot.process_new_updates([update])
            return "OK", 200
        except Exception as e:
            print(f"Ошибка вебхука: {e}")
            return "ERROR", 500
    return "Бот работает", 200

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# ЗАПУСК
# ============================================
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 БОТ АРЕНДА (БЕЗ ФИЛЬТРА)")
    print("=" * 50)
    
    threading.Thread(target=monitor_offers, daemon=True).start()
    bot.remove_webhook()
    print("✅ Вебхук удален")
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
