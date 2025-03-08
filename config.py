import os

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DEVICE_CODE = "gs" # For windows use "gswin64c" for 64-bit or "gswin32c" for 32-bit
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

SAAMANA_BASE_URL = "https://epaper.saamana.com/download.php?file=https://enewspapr.com/News/SAMANA/PUN/{year}/{month}/{day}/{date_str}_{page}.PDF&pageno={page}"
SAAMANA_MAX_PAGES = 30
SAAMANA_PAPER_NAME = "SAAMANA_PUNE"

PUDHARI_BASE_URL = "https://epaper.pudhari.news/download.php?file=https://enewspapr.com/News/PUDHARI/KOL/{year}/{month}/{day}/{date_str}_{page}.PDF&pageno={page}"
PUDHARI_MAX_PAGES = 40
PUDHARI_PAPER_NAME = "PUDHARI_KOLHAPUR"