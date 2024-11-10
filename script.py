import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
from PyPDF2 import PdfMerger
import os
from datetime import datetime
import concurrent.futures
import subprocess

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

SENDERS_NAME = "PaperClip"
DEVICE_CODE = "gs" # For windows use "gswin64c" for 64-bit or "gswin32c" for 32-bit
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
MAILGUN_API_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

# formatted_url_saamana = "https://epaper.saamana.com/download.php?file=https://enewspapr.com/News/SAMANA/PUN/2024/10/05/20241005_1.PDF&pageno=1"
SAAMANA_BASE_URL = "https://epaper.saamana.com/download.php?file=https://enewspapr.com/News/SAMANA/PUN/{year}/{month}/{day}/{date_str}_{page}.PDF&pageno={page}"
SAAMANA_MAX_PAGES = 30
SAAMANA_PAPER_NAME = "SAAMANA_PUNE"

# formatted_url_pudhari = "https://epaper.pudhari.news/download.php?file=https://enewspapr.com/News/PUDHARI/KOL/2024/10/05/20241005_1.PDF&pageno=1"
PUDHARI_BASE_URL = "https://epaper.pudhari.news/download.php?file=https://enewspapr.com/News/PUDHARI/KOL/{year}/{month}/{day}/{date_str}_{page}.PDF&pageno={page}"
PUDHARI_MAX_PAGES = 40
PUDHARI_PAPER_NAME = "PUDHARI_KOLHAPUR"

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

def download_pdf(url, filename):
    try:
        response = requests.get(url)
        if response.status_code == 200 and len(response.content) > 0:
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

def merge_pdfs(pdf_files, output_filename):
    try:
        merger = PdfMerger()
        for pdf in sorted(pdf_files, key=lambda x: int(x.split('_')[1].split('.')[0])):
            if pdf:
                merger.append(pdf)
        merger.write(output_filename)
        merger.close()
    except Exception as e:
        print(f"Error merging PDFs: {e}")

def compress_pdf(input_pdf, output_pdf):
    gs_command = [
        DEVICE_CODE, 
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.3",
        "-dPDFSETTINGS=/printer",
        "-dNOPAUSE",
        "-dBATCH",
        "-dDownsampleColorImages=true",
        "-dColorImageResolution=180",
        f"-sOutputFile={output_pdf}",
        input_pdf
    ]
    try:
        subprocess.run(gs_command, check=True)
        compressed_size = os.path.getsize(output_pdf) / (1024 * 1024)
        print(f"Compressed {input_pdf} to {output_pdf} with size {compressed_size:.2f} MB")
        os.remove(input_pdf)
    except FileNotFoundError:
        print("Ghostscript not found. Please ensure Ghostscript is installed and added to your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Ghostscript error: {e}")

def download_and_merge_newspaper(date_str, base_url, max_pages, paper_name):
    year, month, day = date_str[:4], date_str[4:6], date_str[6:]
    formatted_url = base_url.format(year=year, month=month, day=day, date_str=date_str, page="{page}")

    pdf_files = []
    page = 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_page = {}
        while True:
            future = executor.submit(download_pdf, formatted_url.format(page=page), f"page_{page}.pdf")
            future_to_page[future] = page
            page += 1
            if len(future_to_page) >= 10:
                for future in concurrent.futures.as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        filename = future.result()
                        if filename:
                            pdf_files.append(filename)
                    except Exception as e:
                        print(f"Error downloading page {page_num}: {e}")
                future_to_page.clear()
                if not filename:
                    break
            if page > max_pages:
                break

        for future in concurrent.futures.as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                filename = future.result()
                if filename:
                    pdf_files.append(filename)
            except Exception as e:
                print(f"Error downloading page {page_num}: {e}")

    if pdf_files:
        output_filename = f"{paper_name}_{date_str}.pdf"
        merge_pdfs(pdf_files, output_filename)

        for pdf in pdf_files:
            os.remove(pdf)

        original_size = os.path.getsize(output_filename) / (1024 * 1024)
        print(f"Downloaded and Merged {len(pdf_files)} pages into {output_filename} with size {original_size:.2f} MB")

        return output_filename
    else:
        print("No pages were downloaded. Please check the date and try again.")
        return None

def send_email_mailgun(mailgun_api_url, mailgun_api_key, mailgun_domain, sender, to_email, attachment_path, date_str, date_word, paper_name):
    subject = f"{paper_name} Newspaper - {date_word}"
    body = f"Please find attached the {paper_name} newspaper for {date_word}."
    attachment_filename = f"{paper_name}_{date_str}.pdf"

    if not mailgun_api_key or not mailgun_domain:
        print("Mailgun API key or domain not set. Please set the MAILGUN_API_KEY and MAILGUN_DOMAIN environment variables.")
        return None

    try:
        session = requests.Session()
        session.mount('https://', SSLAdapter())

        with open(attachment_path, "rb") as attachment_file:
            response = requests.post(
                mailgun_api_url,
                auth=("api", mailgun_api_key),
                files=[("attachment", (attachment_filename, attachment_file.read()))],
                data={"from": f"{sender} <mailgun@{mailgun_domain}>",
                    "to": [to_email],
                    "subject": subject,
                    "text": body})

        if response.status_code == 200:
            print(f"Email sent successfully with attachment: {attachment_filename}")
        else:
            print(f"Failed to send email. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to send email: {e}")
        return None

def send_pdf_to_telegram(telegram_api_url, telegram_chat_id, pdf_filename, paper_name, date_word):
    with open(pdf_filename, 'rb') as pdf_file:
        files = {
            'document': pdf_file,
        }
        data = {
            'chat_id': telegram_chat_id,
            'caption': f"{paper_name}_{date_word}.pdf"
        }
        response = requests.post(telegram_api_url, data=data, files=files)

    if response.status_code == 200:
        print(f"{paper_name} PDF sent to Telegram successfully.")
    else:
        print(f"Failed to send {paper_name} PDF. Response: {response.text}")

if __name__ == "__main__":
    today_date = datetime.now().strftime("%Y%m%d")
    today_date_word = datetime.now().strftime("%b %d, %Y")

    output_file_saamana = download_and_merge_newspaper(today_date, SAAMANA_BASE_URL, SAAMANA_MAX_PAGES, SAAMANA_PAPER_NAME)
    if output_file_saamana:
        saamana_file_size = os.path.getsize(output_file_saamana) / (1024 * 1024)
        if saamana_file_size > 23:
            compressed_output_file_saamana = f"compressed_{output_file_saamana}"
            compress_pdf(output_file_saamana, compressed_output_file_saamana)
            os.remove(output_file_saamana)
            output_file_saamana = compressed_output_file_saamana
        send_email_mailgun(MAILGUN_API_URL, MAILGUN_API_KEY, MAILGUN_DOMAIN, SENDERS_NAME, RECEIVER_EMAIL, output_file_saamana, today_date, today_date_word, SAAMANA_PAPER_NAME)
        send_pdf_to_telegram(TELEGRAM_API_URL, TELEGRAM_CHAT_ID, output_file_saamana, SAAMANA_PAPER_NAME, today_date_word)
        try:
            os.remove(output_file_saamana)
        except OSError as e:
            print(f"Error removing file {output_file_saamana}: {e}")
    else:
        print("Failed to generate Saamana PDF. No email and telegram sent.")

    output_file_pudhari = download_and_merge_newspaper(today_date, PUDHARI_BASE_URL, PUDHARI_MAX_PAGES, PUDHARI_PAPER_NAME)
    if output_file_pudhari:
        compressed_output_file_pudhari = f"compressed_{output_file_pudhari}"
        compress_pdf(output_file_pudhari, compressed_output_file_pudhari)
        send_pdf_to_telegram(TELEGRAM_API_URL, TELEGRAM_CHAT_ID, compressed_output_file_pudhari, PUDHARI_PAPER_NAME, today_date_word)
        try:
            os.remove(compressed_output_file_pudhari)
        except OSError as e:
            print(f"Error removing file {compressed_output_file_pudhari}: {e}")
    else:
        print("Failed to generate Pudhari PDF. No telegram sent.")
