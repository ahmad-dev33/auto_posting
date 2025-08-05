import os
import logging
from telegram import Bot, InputFile
from telegram.error import TelegramError
from datetime import datetime
import time
from dotenv import load_dotenv
import asyncio

# تكوين السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('book_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تحميل الإعدادات
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
BOOKS_FOLDER = os.getenv('BOOKS_FOLDER', '/storage/emulated/0/books')
PUBLISHED_FOLDER = os.getenv('PUBLISHED_FOLDER', '/storage/emulated/0/published_books')
DELAY_SECONDS = int(os.getenv('DELAY_SECONDS', '30'))
PUBLISHED_LOG = os.getenv('PUBLISHED_LOG', '/storage/emulated/0/published_books.txt')

# إنشاء مجلدات إذا لم تكن موجودة
os.makedirs(BOOKS_FOLDER, exist_ok=True)
os.makedirs(PUBLISHED_FOLDER, exist_ok=True)

def load_published_books():
    try:
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def mark_as_published(book_name):
    with open(PUBLISHED_LOG, 'a', encoding='utf-8') as f:
        f.write(f"{book_name}\n")

def extract_book_name(filename):
    try:
        return filename.split(' - ')[0].strip()
    except:
        return filename

def generate_title(book_name, publisher):
    prefixes = [
        "📚 اكتشف أسرار",
        "🔍 دليلك الشامل ل",
        "🌟 كنز المعرفة:",
        "📖 رحلة في عالم",
        "🧠 موسوعة",
        "✨ الجديد في",
        "🏆 أفضل مرجع ل"
    ]
    from random import choice
    return f"{choice(prefixes)} {book_name}"

async def publish_book(bot, file_path, filename):
    book_name = extract_book_name(filename)
    publisher = filename.split(' - ')[1].split('.')[0] if ' - ' in filename else "ناشر غير معروف"
    
    caption = (
        f"{generate_title(book_name, publisher)}\n\n"
        f"📖 الكتاب: {book_name}\n"
        f"🏢 الناشر: {publisher}\n"
        f"📅 تاريخ النشر: {datetime.now().strftime('%Y-%m-%d')}\n"
        "#كتب #قراءة #مكتبة"
    )
    
    try:
        with open(file_path, 'rb') as file:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                await bot.send_photo(chat_id=CHANNEL_ID, photo=InputFile(file), caption=caption)
            else:
                await bot.send_document(chat_id=CHANNEL_ID, document=InputFile(file), caption=caption)
        
        os.rename(file_path, os.path.join(PUBLISHED_FOLDER, filename))
        mark_as_published(book_name)
        logger.info(f"تم نشر الكتاب بنجاح: {filename}")
        return True
    except Exception as e:
        logger.error(f"فشل نشر الكتاب {filename}: {e}")
        return False

async def publish_books():
    bot = Bot(token=TOKEN)
    published_books = load_published_books()
    new_published = 0

    for filename in sorted(os.listdir(BOOKS_FOLDER)):
        file_path = os.path.join(BOOKS_FOLDER, filename)
        
        if os.path.isfile(file_path) and not filename.startswith('.'):
            book_name = extract_book_name(filename)
            
            if book_name in published_books:
                logger.info(f"الكتاب منشور مسبقاً: {book_name}")
                continue
                
            if await publish_book(bot, file_path, filename):
                new_published += 1
                await asyncio.sleep(DELAY_SECONDS)
    
    return new_published

async def main_loop():
    logger.info("بدء تشغيل البوت في وضع المراقبة...")
    while True:
        try:
            count = await publish_books()
            if count > 0:
                logger.info(f"تم نشر {count} كتاب/كتب جديدة")
            await asyncio.sleep(3600)  # انتظر ساعة قبل الفحص التالي
        except KeyboardInterrupt:
            logger.info("إيقاف البوت...")
            break
        except Exception as e:
            logger.error(f"حدث خطأ غير متوقع: {e}")
            await asyncio.sleep(300)  # انتظر 5 دقائق قبل إعادة المحاولة

if __name__ == '__main__':
    asyncio.run(main_loop())
