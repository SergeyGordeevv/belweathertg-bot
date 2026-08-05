import os
import telebot
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import time
import threading
from datetime import datetime
import re

# ============================================
# НАСТРОЙКИ
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748  # ТВОЙ ID ГРУППЫ!
CHECK_INTERVAL = 300   # 5 минут

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

sent_offers = set()

# Ключевые слова для фильтрации (только аренда в Логойске)
KEYWORDS = [
    'аренда', 'снять', 'логойск', 'logoysk',
    'длительный срок', 'долгосрочно', 'на год'
]

# Слова-исключения (продажа, посуточно)
EXCLUDE_KEYWORDS = [
    'продажа', 'продам', 'купить', 'посуточно', 'посуточная',
    'продается', 'продаётся'
]

def is_valid_offer(text):
    """Проверяет, подходит ли объявление (аренда в Логойске, не продажа)"""
    text_lower = text.lower()
    
    # Проверяем, что есть ключевые слова
    has_keyword = any(kw in text_lower for kw in KEYWORDS)
    
    # Проверяем, что нет слов-исключений
    has_exclude = any(ex in text_lower for ex in EXCLUDE_KEYWORDS)
    
    return has_keyword and not has_exclude

# ============================================
# ПАРСИНГ ВСЕХ САЙТОВ
# ============================================

def parse_kufar():
    """Kufar.by - Логойск, аренда"""
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
                
                # Проверяем, что объявление про Логойск и аренду
                if not is_valid_offer(title):
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
    """Realt.by - Логойск, аренда"""
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
                
                if not is_valid_offer(txt):
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
    """Domovita.by - Логойск, аренда"""
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
                
                if not is_valid_offer(txt):
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
    """Neagent.by - Логойск, аренда"""
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
                
                if not is_valid_offer(txt):
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
    """Hata.by - Логойский район, аренда"""
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
                
                if not is_valid_offer(txt):
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
    """Gde.by - Логойск, аренда"""
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
                
                if not is_valid_offer(txt):
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг (Логойск, аренда)...")
    
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
    
    print(f"  Всего (после фильтрации): {len(all_offers)}")
    return all_offers

# ============================================
# МОНИТОРИНГ НОВЫХ ОБЪЯВЛЕНИЙ
# ============================================
def monitor_offers():
    global sent_offers
    print("🔄 Мониторинг запущен (только аренда в Логойске)...")
    
    # Первый запуск - запоминаем все текущие объявления
    sent_offers = set(get_all_offers())
    print(f"✅ Отслеживается {len(sent_offers)} объявлений")
    
    # Отправляем все текущие объявления в группу
    if sent_offers:
        bot.send_message(CHAT_ID, f"📋 ТЕКУЩИЕ ОБЪЯВЛЕНИЯ ПО АРЕНДЕ В ЛОГОЙСКЕ ({len(sent_offers)} шт.)")
        for offer in list(sent_offers)[:10]:
            bot.send_message(CHAT_ID, offer)
            time.sleep(0.5)
        if len(sent_offers) > 10:
            bot.send_message(CHAT_ID, f"... и еще {len(sent_offers) - 10} объявлений")
    
    while True:
        try:
            current_offers = set(get_all_offers())
            new_offers = current_offers - sent_offers
            
            if new_offers:
                print(f"🔔 НОВЫХ: {len(new_offers)}")
                bot.send_message(CHAT_ID, f"🔔 НОВЫЕ ОБЪЯВЛЕНИЯ В ЛОГОЙСКЕ ({len(new_offers)} шт.)")
                for offer in new_offers:
                    bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{offer}")
                    print("  ✅ Отправлено")
                    time.sleep(1)
                sent_offers = current_offers
            else:
                print("Новых объявлений нет")
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")
        
        time.sleep(CHECK_INTERVAL)

# ============================================
# КОМАНДЫ БОТА
# ============================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, 
        "🤖 Бот для мониторинга АРЕНДЫ в ЛОГОЙСКЕ!\n\n"
        "🏠 Ищет только:\n"
        "• Аренда квартир\n"
        "• Длительный срок\n"
        "• Логойск и район\n\n"
        "❌ НЕ показывает:\n"
        "• Продажу\n"
        "• Посуточную аренду\n\n"
        "🔄 Проверка каждые 5 минут\n"
        "📊 Статистика: /stats\n"
        "🔄 Обновить: /update"
    )

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    bot.reply_to(message,
        f"📊 СТАТИСТИКА\n\n"
        f"• Отслеживается: {len(sent_offers)} объявлений\n"
        f"• Интервал: {CHECK_INTERVAL} сек (5 мин)\n"
        f"• Сайтов: 6\n"
        f"• Фильтр: Аренда в Логойске\n"
        f"• Статус: ✅ Активен"
    )

@bot.message_handler(commands=['update'])
def update_cmd(message):
    bot.reply_to(message, "🔄 Обновляю объявления по аренде в Логойске...")
    global sent_offers
    sent_offers = set(get_all_offers())
    bot.reply_to(message, f"✅ Обновлено! Отслеживается {len(sent_offers)} объявлений")

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
    return "Бот работает (Логойск, аренда)", 200

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
    
    monitor_thread = threading.Thread(target=monitor_offers, daemon=True)
    monitor_thread.start()
    
    bot.remove_webhook()
    print("✅ Вебхук удален")
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
