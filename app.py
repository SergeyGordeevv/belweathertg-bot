import os
import telebot
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import time
import threading
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748
CHECK_INTERVAL = 300

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
sent_offers = set()

# ============================================
# ПАРСИНГ (С ОБРАБОТКОЙ ОШИБОК)
# ============================================

def safe_request(url):
    """Безопасный запрос с обработкой ошибок"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r
        else:
            print(f"  Статус {r.status_code} для {url}")
            return None
    except Exception as e:
        print(f"  Ошибка запроса: {e}")
        return None

def parse_realt():
    offers = []
    url = "https://realt.by/rent/flats/"
    r = safe_request(url)
    if not r:
        return offers
    
    try:
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'offer' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://realt.by" + a['href'] if a['href'].startswith('/') else a['href']
                if txt and len(txt) > 5:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 10:
                    break
    except Exception as e:
        print(f"  Ошибка парсинга Realt: {e}")
    return offers

def get_all_offers():
    all_offers = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг...")
    
    offers = parse_realt()
    all_offers.extend(offers)
    print(f"  Realt: {len(offers)}")
    
    print(f"  Всего: {len(all_offers)}")
    return all_offers

# ============================================
# МОНИТОРИНГ
# ============================================
def monitor_offers():
    global sent_offers
    print("🔄 Мониторинг запущен...")
    
    sent_offers = set(get_all_offers())
    print(f"✅ Отслеживается {len(sent_offers)} объявлений")
    
    if sent_offers:
        try:
            bot.send_message(CHAT_ID, f"📋 ТЕКУЩИЕ ОБЪЯВЛЕНИЯ ({len(sent_offers)} шт.)")
            for offer in list(sent_offers)[:10]:
                bot.send_message(CHAT_ID, offer)
                time.sleep(0.5)
        except Exception as e:
            print(f"Ошибка отправки: {e}")
    
    while True:
        try:
            current_offers = set(get_all_offers())
            new_offers = current_offers - sent_offers
            
            if new_offers:
                print(f"🔔 НОВЫХ: {len(new_offers)}")
                bot.send_message(CHAT_ID, f"🔔 НОВЫЕ ОБЪЯВЛЕНИЯ ({len(new_offers)} шт.)")
                for offer in new_offers:
                    bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{offer}")
                    time.sleep(1)
                sent_offers = current_offers
            else:
                print("Новых объявлений нет")
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")
        
        time.sleep(CHECK_INTERVAL)

# ============================================
# КОМАНДЫ
# ============================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "🤖 Бот работает!")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    bot.reply_to(message, f"📊 Объявлений: {len(sent_offers)}")

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
    print("🤖 БОТ (РАБОЧАЯ ВЕРСИЯ)")
    print("=" * 50)
    
    threading.Thread(target=monitor_offers, daemon=True).start()
    bot.remove_webhook()
    print("✅ Вебхук удален")
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
