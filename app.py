import os
import telebot
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
sent_offers = set()

# ============================================
# ПРОВЕРКА - ТОЛЬКО ЛОГОЙСК
# ============================================
def is_logoysk(text):
    """Проверяет, есть ли в тексте Логойск"""
    text_lower = text.lower()
    keywords = ['логойск', 'logoysk', 'logojsk', 'логойский']
    return any(kw in text_lower for kw in keywords)

# ============================================
# ПАРСИНГ 6 САЙТОВ
# ============================================

def parse_kufar():
    offers = []
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru?m=1"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for item in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'card' in x.lower())):
            try:
                title_elem = item.find('a', class_=lambda x: x and ('title' in x.lower() or 'link' in x.lower()))
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                link = title_elem.get('href')
                if link and link.startswith('/'):
                    link = "https://re.kufar.by" + link
                
                if not is_logoysk(title):
                    continue
                
                price_elem = item.find('span', class_=lambda x: x and 'price' in x.lower())
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                offer_text = f"🏠 {title[:50]}\n💰 {price}\n🔗 {link}"
                offers.append(offer_text)
                if len(offers) >= 10:
                    break
            except:
                continue
    except Exception as e:
        print(f"Ошибка Kufar: {e}")
    return offers

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
                
                if not is_logoysk(txt):
                    continue
                
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 10:
                    break
    except Exception as e:
        print(f"Ошибка Realt: {e}")
    return offers

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
                
                if not is_logoysk(txt):
                    continue
                
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 10:
                    break
    except Exception as e:
        print(f"Ошибка Domovita: {e}")
    return offers

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
                
                if not is_logoysk(txt):
                    continue
                
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 10:
                    break
    except Exception as e:
        print(f"Ошибка Neagent: {e}")
    return offers

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
                
                if not is_logoysk(txt):
                    continue
                
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 10:
                    break
    except Exception as e:
        print(f"Ошибка Hata: {e}")
    return offers

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
                
                if not is_logoysk(txt):
                    continue
                
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 10:
                    break
    except Exception as e:
        print(f"Ошибка Gde: {e}")
    return offers

# ============================================
# СБОР ВСЕХ ОБЪЯВЛЕНИЙ
# ============================================
def get_all_offers():
    all_offers = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг (только Логойск)...")
    
    sites = [
        ("Kufar", parse_kufar),
        ("Realt", parse_realt),
        ("Domovita", parse_domovita),
        ("Neagent", parse_neagent),
        ("Hata", parse_hata),
        ("Gde", parse_gde),
    ]
    
    for name, func in sites:
        try:
            offers = func()
            all_offers.extend(offers)
            print(f"  {name}: {len(offers)}")
        except Exception as e:
            print(f"  {name}: Ошибка - {e}")
    
    print(f"  Всего (Логойск): {len(all_offers)}")
    return all_offers

# ============================================
# МОНИТОРИНГ
# ============================================
def monitor_offers():
    global sent_offers
    print("🔄 Мониторинг запущен (только Логойск)...")
    
    sent_offers = set(get_all_offers())
    print(f"✅ Отслеживается {len(sent_offers)} объявлений")
    
    if sent_offers:
        try:
            bot.send_message(CHAT_ID, f"📋 ТЕКУЩИЕ ОБЪЯВЛЕНИЯ В ЛОГОЙСКЕ ({len(sent_offers)} шт.)")
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
                bot.send_message(CHAT_ID, f"🔔 НОВЫЕ ОБЪЯВЛЕНИЯ В ЛОГОЙСКЕ ({len(new_offers)} шт.)")
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
    bot.reply_to(message, 
        "🤖 Бот для мониторинга АРЕНДЫ в ЛОГОЙСКЕ!\n\n"
        "🏠 Отслеживает 6 сайтов:\n"
        "• Kufar.by\n"
        "• Realt.by\n"
        "• Domovita.by\n"
        "• Neagent.by\n"
        "• Hata.by\n"
        "• Gde.by\n\n"
        "🔄 Проверка каждые 5 минут\n"
        "📊 Статистика: /stats"
    )

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    bot.reply_to(message,
        f"📊 СТАТИСТИКА\n\n"
        f"• Отслеживается: {len(sent_offers)} объявлений\n"
        f"• Интервал: {CHECK_INTERVAL} сек (5 мин)\n"
        f"• Сайтов: 6\n"
        f"• Фильтр: Только Логойск\n"
        f"• Статус: ✅ Активен"
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
    return "Бот работает (Логойск)", 200

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# ЗАПУСК
# ============================================
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 БОТ АРЕНДА ЛОГОЙСК")
    print("=" * 50)
    
    threading.Thread(target=monitor_offers, daemon=True).start()
    bot.remove_webhook()
    print("✅ Вебхук удален")
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
