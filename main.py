import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Telegram BotFather'dan aldığınız YENİ BOT TOKEN'ını buraya yazın
TOKEN = "8917356721:AAE6ejLCwSiSLfSnFwDUxhZftYNgc1AR75k"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

USER_CHAT_ID = None
NOTIFIED_SYMBOLS = set()

# Otomatik Taranacak Liste (İstediğiniz sembolleri ekleyebilirsiniz)
TRACK_LIST = [
    # Kriptolar
    "BTC", "ETH", "SOL", "XRP", "AVAX", "DOGE", "PEPE", "SHIB", "ADA", "LINK",
    # BİST Hisseleri
    "THYAO", "ASELS", "ASTOR", "GARAN", "EREGL", "SASA", "KONTR", "HEKTS", "TUPRS", "EKGYO"
]

def get_crypto_binance(symbol: str):
    try:
        clean_symbol = symbol.upper().replace("-USD", "").replace(".IS", "").strip()
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={clean_symbol}USDT"
        res = requests.get(url, timeout=5)
        data = res.json()
        if "priceChangePercent" in data:
            return float(data["priceChangePercent"]), float(data["lastPrice"])
    except Exception as e:
        logging.error(f"Binance Hata ({symbol}): {e}")
    return None

def get_stock_stooq(symbol: str):
    try:
        clean_symbol = symbol.upper().replace(".IS", "").replace("-USD", "").strip()
        url = f"https://stooq.com/q/l/?s={clean_symbol}.TR&f=sdohcv&h&e=csv"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        lines = res.text.strip().split('\n')
        if len(lines) >= 2:
            row = lines[1].split(',')
            if len(row) >= 6 and row[1] != 'N/A':
                open_p, close_p = float(row[2]), float(row[5])
                if open_p > 0:
                    return ((close_p - open_p) / open_p) * 100, close_p
    except Exception as e:
        logging.error(f"Stooq Hata ({symbol}): {e}")
    return None

def get_symbol_change(symbol: str):
    res = get_crypto_binance(symbol)
    if res:
        return res
    return get_stock_stooq(symbol)

async def check_high_gainers(context: ContextTypes.DEFAULT_TYPE):
    global USER_CHAT_ID, NOTIFIED_SYMBOLS
    if not USER_CHAT_ID:
        return

    for symbol in TRACK_LIST:
        res = get_symbol_change(symbol)
        if res:
            change_percent, last_price = res
            if change_percent >= 3.0 and symbol not in NOTIFIED_SYMBOLS:
                NOTIFIED_SYMBOLS.add(symbol)
                msg = (
                    f"🚀 *YÜKSELİŞ SİNYALİ! (%3+)*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📌 *Sembol:* `{symbol}`\n"
                    f"📈 *Günlük Yükseliş:* `%{change_percent:.2f}`\n"
                    f"💵 *Güncel Fiyat:* `{last_price:.2f}`\n\n"
                    f"🔥 Piyasada sert yükseliş hareketi tespit edildi!"
                )
                await context.bot.send_message(chat_id=USER_CHAT_ID, text=msg, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USER_CHAT_ID
    USER_CHAT_ID = update.effective_chat.id
    await update.message.reply_text(
        "🔔 *Yükseliş Alarm Botu Aktif!*\n\n"
        "Taranan listede %3 ve üzeri yükseliş yaşandığında buradan anlık bildirim alacaksınız.",
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    
    # 15 dakikada bir tarama yapar (900 saniye)
    app.job_queue.run_repeating(check_high_gainers, interval=600, first=10)
    
    app.run_polling(drop_pending_updates=True)

import asyncio
import httpx

# Arka planda 10 dakikada bir kendi Render URL'sine istek atan fonksiyon
async def keep_alive_self_ping():
    # Kendi Render URL'niz
    RENDER_URL = "https://alarm-jbkc.onrender.com"
    
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(600)  # 600 saniye = 10 dakika
            try:
                response = await client.get(RENDER_URL)
                print(f"Self-ping başarılı! Durum Kodu: {response.status_code}")
            except Exception as e:
                print(f"Self-ping hatası: {e}")

# asyncio event loop içerisine eklenebilir:
# asyncio.create_task(keep_alive_self_ping())
