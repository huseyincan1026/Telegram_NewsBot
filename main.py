from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)

import requests 
from bs4 import BeautifulSoup
import json
import nest_asyncio
nest_asyncio.apply()

TOKEN = '8125258101:AAGdL8ViAJ7hNp6N-ZjMns5p7BS3I4UKzDs'

NEWSAPI_KEY = '0d768d83e4e74f1b9bfc7ea82c967b75'

# Haber basliklari ve icerikleri icin degiskenler
urls = []
titles = []
articles = []

# Durumlar icin sabitler
TITLE_SELECTION = 0  # Sabiti tanımladık

print('Bot started working...')

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # NewsAPI uzerinden haberler alinacak ve kullaniciya basliklar gosterilecek
    
    global titles, urls, articles
    titles, urls, articles = [], [], []  # verileri sifirlamis olduk
    
    # newsapi'deki haber verilerini cekelim
    url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'sources': 'bbc-news',
        'apiKey': NEWSAPI_KEY,
        'pageSize': 10
    }
    
    r = requests.get(url, params=params)
    data = r.json()

    # Tum linkleri toparladik
    for article in data['articles']:
        urls.append(article['url'])
        titles.append(article['title'])
        articles.append(fetch_article_content(article['url']))  # fonksiyonla o linke gitmesini saglayacagiz
                        
    # Kullaniciya haber basliklarini gosterelim
    reply_keyboard = [[title] for title in titles]
    await update.message.reply_text(
        'Pick a title:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return TITLE_SELECTION  # Sabiti döndürüyoruz

def fetch_article_content(article_url: str) -> str:
    # Haber icerigini BBC sayfasindan ayristiralim
    
    try:
        response = requests.get(article_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Haber metnini ayristiralim
        content = soup.findAll('div', {'data-component': 'text-block'})
        article_text = "".join([block.get_text() for block in content])
    
        return article_text.replace('\\"', '"').replace("\\'", "'")

    except Exception as e:
        return 'Could not get news content'


def split_message(text: str, max_length: int = 4096) -> list:
    """Metni 4096 karakterlik parçalara böler."""
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

        
async def send_selected_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Kullanıcının seçtiği haber başlığını bulalım ve haber içeriğini gönderelim
    selected_title = update.message.text
    
    if selected_title in titles:
        index = titles.index(selected_title)
        # Haber başlığını gönderelim
        await update.message.reply_text(f'<b>{titles[index]}</b>\n\n', parse_mode='HTML')

        # Haber içeriğini parçalayalım ve her parçayı sırayla gönderelim
        article_text = articles[index]
        parts = split_message(article_text)

        for part in parts:
            await update.message.reply_text(part)

        # Haber linkini gönderelim
        await update.message.reply_text(f"Click the link to examine the news : {urls[index]}")
    
    else:
        await update.message.reply_text("You made an invalid selection. Please choose a title.")
    
    return ConversationHandler.END




async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Konusmayi sonlandir
    await update.message.reply_text("The news selection is canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END



def main():
    # Application nesnesi olusturuluyor 
    application = Application.builder().token(TOKEN).build()
    
    # Haber secimi icin konusma yoneticisi
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', get_news)],
        states={
            TITLE_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_selected_news)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    
    # Botu baslat
    application.run_polling()

if __name__ == '__main__':
    main()
