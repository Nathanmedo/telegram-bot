from decouple import config


ADMINS = config('ADMINS', cast=lambda v: set(int(x) for x in v.split()))
COINGECKO_API_URL = config('COINGECKO_API_URL','https://api.coingecko.com/api/v3')
DATABASE_URL = config('DATABASE_URL')
DATABASE_NAME = config('DATABASE_NAME')
NOWPAYMENTS_API_KEY = config('NOWPAYMENTS_API_KEY')
BLOG_LINK = "https://Bamcrypto.blogspot.com"
BOT_LINK = "https://t.me/BTStrading_bot"
BOT_TOKEN = config('BOT_TOKEN')
BASE_URL = "https://telegram-bot-production-4b92.up.railway.app"