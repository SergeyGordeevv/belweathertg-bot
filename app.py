import os
import re
import time
import threading
from datetime import datetime
from flask import Flask
import telebot
import requests
from bs4 import BeautifulSoup

# ============================================
# НАСТРОЙКИ
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная TELEGRAM_BOT_TOKEN не установлена!")

CHAT_ID = -5568949748
CHECK_INTERVAL = 300
CITY_FILTER = "логойск"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
sent_offers = set()
polling_running = True

# ============================================
# ПАРСИНГ САЙТОВ
# ============================================

def parse_onliner():
    offers = []
    url = "https://r.onliner.by/flats/rent/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda c: c and ('offer' in c.lower() or 'form' in c.lower())):
            a = div.find('a')
            if a and a.get('href'):
                title = a.text.strip()
                if CITY_FILTER in title.lower():
                    link = a['href']
                    if link.startswith('/'):
                        link = "https://r.onliner.by" + link
                    price_elem = div.find('span', class_=re.compile(r'price', re.I))
                    price = price_elem.text.strip() if price_elem else "Цена не указана"
                    offer_text = f"🏠 {title[:60]}\n💰 {price}\n🔗 {link}"
                    offers.append(offer_text)
                    if len(offers) >= 10:
                        break
    except Exception as e:
        print(f"Ошибка Onliner: {e}")
    return offers

def parse_realt():
    offers = []
    url = "https://realt.by/rent/flats/logojsk/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda c: c and ('item' in c.lower() or 'offer' in c.lower())):
            a = div.find('a')
            if a and a.get('href'):
                title = a.text.strip()
                if CITY_FILTER in title.lower():
                    link = a['href']
                    if link.startswith('/'):
                        link = "https://realt.by" + link
                    price_elem = div.find('span', class_=re.compile(r'price|cost', re.I))
                    price = price_elem.text.strip() if price_elem else "Цена не указана"
                    offer_text = f"🏠 {title[:60]}\n💰 {price}\n🔗 {link}"
                    offers.append(offer_text)
                    if len(offers) >= 10:
                        break
    except Exception as e:
        print(f"Ошибка Realt: {e}")
    return offers

def parse_domovita():
    offers = []
    url = "https://domovita.by/rent/logojsk/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Ищем карточки объявлений (актуальные классы нужно уточнить)
        for div in soup.find_all('div', class_=lambda c: c and ('item' in c.lower() or 'card' in c.lower())):
            a = div.find('a')
            if a and a.get('href'):
                title = a.text.strip()
                if CITY_FILTER in title.lower():
                    link = a['href']
                    if link.startswith('/'):
                        link = "https://domovita.by" + link
                    price_elem = div.find('span', class_=re.compile(r'price', re.I))
                    price = price_elem.text.strip() if price_elem else "Цена не указана"
                    offer_text = f"🏠 {title[:60]}\n💰 {price}\n🔗 {link}"
                    offers.append(offer_text)
                    if len(offers) >= 10:
                        break
    except Exception as e:
        print(f"Ошибка Domovita: {e}")
    return offers

def parse_neagent():
    offers = []
    url = "https://neagent.by/logojsk/rent"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda c: c and ('item' in c.lower() or 'offer' in c.lower())):
            a = div.find('a')
            if a and a.get('href'):
                title = a.text.strip()
                if CITY_FILTER in title.lower():
                    link = a['href']
                    if link.startswith('/'):
                        link = "https://neagent.by" + link
                    price_elem = div.find('span', class_=re.compile(r'price', re.I))
                    price = price_elem.text.strip() if price_elem else "Цена не указана"
                    offer_text = f"🏠 {title[:60]}\n💰 {price}\n🔗 {link}"
                    offers.append(offer_text)
                    if len(offers) >= 10:
                        break
    except Exception as e:
        print(f"Ошибка Neagent: {e}")
    return offers

def parse_khata():
    offers = []
    url = "https://khata.by/logojsk/rent"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda c: c and ('item' in c.lower() or 'offer' in c.lower())):
            a = div.find('a')
            if a and a.get('href'):
                title = a.text.strip()
                if CITY_FILTER in title.lower():
                    link = a['href']
                    if link.startswith('/'):
                        link = "https://khata.by" + link
                    price_elem = div.find('span', class_=re.compile(r'price', re.I))
                    price = price_elem.text.strip() if price_elem else "Цена не указана"
                    offer_text = f"🏠 {title[:60]}\n💰 {price}\n🔗 {link}"
                    offers.append(offer_text)
                    if len(offers) >= 10:
                        break
    except Exception as e:
        print(f"Ошибка Khata: {e}")
    return offers

# ============================================
# СБОР ВСЕХ ОБЪЯВЛЕНИЙ
# ============================================
def get_all_offers():
    all_offers = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг (Логойск)...")
    all_offers.extend(parse_onliner())
    all_offers.extend(parse_realt())
    all_offers.extend(parse_domovita())
    all_offers.extend(parse_neagent())
    all_offers.extend(parse_khata())
    print(f"  Найдено: {len(all_offers)}")
    return all_offers

# ============================================
# ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА
# ============================================
def force_check():
    global sent_offers
    try:
        current = set(get_all_offers())
        new = current - sent_offers
        if new:
            for offer in new:
                bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{offer}")
                time.sleep(1)
            sent_offers = current
            bot.send_message(CHAT_ID, f"✅ Отправлено {len(new)} новых объявлений.")
        else:
            bot.send_message(CHAT_ID, "Новых объявлений нет.")
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Ошибка: {e}")

# ============================================
# МОНИТОРИНГ
# ============================================
def monitor_loop():
    global sent_offers
    sent_offers = set(get_all_offers())
    print(f"✅ Отслеживается {len(sent_offers)} объявлений")
    while True:
        try:
            current = set(get_all_offers())
            new = current - sent_offers
            if new:
                print(f"🔔 Найдено {len(new)} новых!")
                for offer in new:
                    try:
                        bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{offer}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"Ошибка отправки: {e}")
                sent_offers = current
            else:
                print("Новых нет")
        except Exception as e:
            print(f"Ошибка мониторинга: {e}")
        time.sleep(CHECK_INTERVAL)

# ============================================
# ЗАПУСК POLLING С ПЕРЕЗАПУСКОМ ПРИ 409
# ============================================
def start_polling_with_retry():
    """Запускает polling и перезапускает его при ошибке 409"""
    global polling_running
    while polling_running:
        try:
            print("🚀 Бот запущен и слушает команды")
            bot.infinity_polling(timeout=30, long_polling_timeout=20)
        except Exception as e:
            if "409" in str(e) or "Conflict" in str(e):
                print("⚠️ Ошибка 409: перезапускаю polling через 5 секунд...")
                time.sleep(5)
                # Сбрасываем вебхук перед перезапуском
                try:
                    bot.delete_webhook()
                except:
                    pass
            else:
                print(f"❌ Ошибка polling: {e}")
                time.sleep(5)

# ============================================
# КОМАНДЫ
# ============================================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.reply_to(message,
        "🤖 Бот для аренды в Логойске запущен!\n"
        "Отслеживаю: Onliner, Realt, Domovita, Neagent, Khata\n"
        "/stats – статистика\n/help – помощь\n/update – проверка")

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    bot.reply_to(message,
        f"📊 Отслеживается: {len(sent_offers)}\n"
        f"⏱ Интервал: {CHECK_INTERVAL} сек")

@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.reply_to(message,
        "📌 Команды:\n/start – запуск\n/stats – статистика\n"
        "/help – справка\n/update – принудительная проверка")

@bot.message_handler(commands=['update'])
def cmd_update(message):
    bot.reply_to(message, "🔄 Проверка...")
    threading.Thread(target=force_check).start()

# ============================================
# FLASK
# ============================================
@app.route('/')
def index():
    return "🤖 Бот для аренды в Логойске работает!"

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 БОТ АРЕНДА ЛОГОЙСК (5 САЙТОВ)")
    print("=" * 50)

    # Удаляем вебхук
    try:
        bot.delete_webhook()
        print("✅ Вебхук удален")
    except:
        print("⚠️ Не удалось удалить вебхук")

    # Мониторинг в фоне
    threading.Thread(target=monitor_loop, daemon=True).start()

    # Polling с обработкой 409
    polling_thread = threading.Thread(target=start_polling_with_retry, daemon=True)
    polling_thread.start()

    # Flask
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Запуск веб-сервера на порту {port}...")
    app.run(host="0.0.0.0", port=port)
