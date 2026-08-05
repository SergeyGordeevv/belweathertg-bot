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
# НАСТРОЙКИ (задаются через переменные окружения)
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная TELEGRAM_BOT_TOKEN не установлена!")

CHAT_ID = -5568949748               # ID твоей группы
CHECK_INTERVAL = 300                # 5 минут
CITY_FILTER = "логойск"             # Фильтр по городу (нижний регистр)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Множество для хранения уже отправленных объявлений
sent_offers = set()

# ============================================
# ФУНКЦИИ ПАРСИНГА (с фильтром по городу)
# ============================================

def parse_kufar():
    """Парсинг Kufar.by (Минская область, аренда)"""
    offers = []
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Ищем все ссылки на объявления
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/l/minsk/snyat/kvartiru/' in href and 'page' not in href:
                title = a.text.strip()
                # Проверяем, содержит ли заголовок или ссылка название города
                if CITY_FILTER in title.lower() or CITY_FILTER in href.lower():
                    link = "https://re.kufar.by" + href if href.startswith('/') else href
                    # Попытка найти цену рядом
                    price_elem = a.find_next('span', class_=re.compile(r'price', re.I))
                    price = price_elem.text.strip() if price_elem else "Цена не указана"
                    offer_text = f"🏠 {title[:60]}\n💰 {price}\n🔗 {link}"
                    offers.append(offer_text)
                    if len(offers) >= 10:
                        break
    except Exception as e:
        print(f"Ошибка Kufar: {e}")
    return offers

def parse_onliner():
    """Парсинг Onliner.by (аренда)"""
    offers = []
    url = "https://r.onliner.by/flats/rent/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Ищем блоки объявлений
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
    """Парсинг Realt.by (аренда)"""
    offers = []
    url = "https://realt.by/rent/flats/"
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

# ============================================
# СБОР ВСЕХ ОБЪЯВЛЕНИЙ
# ============================================
def get_all_offers():
    """Собирает объявления со всех сайтов и возвращает список строк"""
    all_offers = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг (Логойск, долгосрочная аренда)...")
    all_offers.extend(parse_kufar())
    all_offers.extend(parse_onliner())
    all_offers.extend(parse_realt())
    print(f"  Найдено объявлений: {len(all_offers)}")
    return all_offers

# ============================================
# ФУНКЦИЯ МОНИТОРИНГА (запускается в фоновом потоке)
# ============================================
def monitor_loop():
    """Бесконечный цикл проверки новых объявлений"""
    global sent_offers
    # Первоначальное заполнение – чтобы не слать старые
    sent_offers = set(get_all_offers())
    print(f"✅ Инициализация: отслеживается {len(sent_offers)} объявлений")

    while True:
        try:
            current = set(get_all_offers())
            new = current - sent_offers
            if new:
                print(f"🔔 Найдено {len(new)} новых объявлений!")
                for offer in new:
                    try:
                        bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{offer}")
                        print("  ✅ Отправлено")
                        time.sleep(1)
                    except Exception as e:
                        print(f"  ❌ Ошибка отправки: {e}")
                sent_offers = current
            else:
                print("Новых объявлений нет")
        except Exception as e:
            print(f"Ошибка в мониторинге: {e}")

        print(f"⏳ Следующая проверка через {CHECK_INTERVAL} секунд...")
        print("-" * 40)
        time.sleep(CHECK_INTERVAL)

# ============================================
# ОБРАБОТЧИКИ КОМАНД ТЕЛЕГРАМ
# ============================================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.reply_to(message, "🤖 Бот для поиска аренды в Логойске запущен!\nОтслеживаю Kufar, Onliner, Realt.\nКоманда /stats – статистика.")

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    bot.reply_to(message, f"📊 Отслеживается объявлений: {len(sent_offers)}\n🔄 Интервал проверки: {CHECK_INTERVAL} сек")

# ============================================
# FLASK – ДЛЯ UPTIMEROBOT (ПИНГ)
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

    # Удаляем вебхук на случай, если он остался
    bot.delete_webhook()
    print("✅ Вебхук удален")

    # Запускаем мониторинг в фоновом потоке
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()

    # Запускаем polling для обработки команд в отдельном потоке
    def start_polling():
        print("🚀 Бот запущен и слушает команды")
        bot.infinity_polling()
    polling_thread = threading.Thread(target=start_polling, daemon=True)
    polling_thread.start()

    # Запускаем Flask-сервер
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Запуск веб-сервера на порту {port}...")
    app.run(host="0.0.0.0", port=port)
