import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
from PyPDF2 import PdfMerger
import os
from datetime import datetime
import concurrent.futures
import subprocess

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
        "gs", # For windows use "gswin64c" for 64-bit or "gswin32c" for 32-bit
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
    except FileNotFoundError:
        print("Ghostscript not found. Please ensure Ghostscript is installed and added to your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Ghostscript error: {e}")

# formatted_url_saamana = "https://epaper.saamana.com/download.php?file=https://enewspapr.com/News/SAMANA/PUN/2024/10/05/20241005_1.PDF&pageno=1"
# formatted_url_pudhari = "https://epaper.pudhari.news/download.php?file=https://enewspapr.com/News/PUDHARI/KOL/2024/10/05/20241005_1.PDF&pageno=1"

def download_and_merge_newspaper(date_str, paper):
    if paper == "saamana":
        base_url = "https://epaper.saamana.com/download.php?file=https://enewspapr.com/News/SAMANA/PUN/{year}/{month}/{day}/{date_str}_{page}.PDF&pageno={page}"
        max_pages = 30
        paper_name = "SAAMANA_PUNE"

    elif paper == "pudhari":
        base_url = "https://epaper.pudhari.news/download.php?file=https://enewspapr.com/News/PUDHARI/KOL/{year}/{month}/{day}/{date_str}_{page}.PDF&pageno={page}"
        max_pages = 40
        paper_name = "PUDHARI_KOLHAPUR"

    else:
        print("Invalid paper")
    

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
        print(f"Merged {len(pdf_files)} pages into {output_filename} with size {original_size:.2f} MB")

        compressed_output_filename = f"COMPRESSED_{paper_name}_{date_str}.pdf"
        compress_pdf(output_filename, compressed_output_filename)
        
        compressed_size = os.path.getsize(compressed_output_filename) / (1024 * 1024)  
        print(f"Compressed {output_filename} to {compressed_output_filename} with size {compressed_size:.2f} MB")
        
        os.remove(output_filename)

        print(f"Downloaded, merged, and compressed {len(pdf_files)} pages into {compressed_output_filename}")
        return compressed_output_filename
    else:
        print("No pages were downloaded. Please check the date and try again.")
        return None

def send_email_mailgun(subject, body, to_email, attachment_path, date_str):
    MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
    MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')

    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        print("Mailgun API key or domain not set. Please set the MAILGUN_API_KEY and MAILGUN_DOMAIN environment variables.")
        return None
    
    session = requests.Session()
    session.mount('https://', SSLAdapter())

    attachment_filename = f"Saamana_{date_str}.pdf"

    with open(attachment_path, "rb") as attachment_file:
        return requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files=[("attachment", (attachment_filename, attachment_file.read()))],
            data={"from": f"Cosmoo <mailgun@{MAILGUN_DOMAIN}>",
                "to": [to_email],
                "subject": subject,
                "text": body})      

def send_pdf_to_telegram(pdf_filename, paper_name, today_date_word):
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    place_name = "pune" if paper_name.lower() == "saamana" else "kolhapur"
    
    with open(pdf_filename, 'rb') as pdf_file:
        files = {
            'document': pdf_file,
        }
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'caption': f"{paper_name.upper()}_{place_name.upper()}_{today_date_word}.pdf"
        }
        response = requests.post(url, data=data, files=files)

    if response.status_code == 200:
        print(f"{paper_name.upper()} PDF sent to Telegram successfully.")
    else:
        print(f"Failed to send {paper_name.upper()} PDF. Response: {response.text}")

if __name__ == "__main__":
    today_date = datetime.now().strftime("%Y%m%d")
    today_date_word = datetime.now().strftime("%b %d, %Y")
    output_file_saamana = download_and_merge_newspaper(today_date, "saamana")
    
    if output_file_saamana:
        subject = f"Saamana - {today_date_word}"
        body = f"Please find today's Saamana epaper attached as a PDF for {today_date_word}."
        to_email = os.getenv('RECEIVER_EMAIL')
        
        if not to_email:
            print("Receiver email not set. Please set the RECEIVER_EMAIL environment variable.")
        else:
            response = send_email_mailgun(subject, body, to_email, output_file, today_date)
            if response and response.status_code == 200:
                print(f"Email sent successfully with attachment: {output_file}")
            else:
                print(f"Failed to send email. Status code: {response.status_code if response else 'N/A'}")
                print(f"Response: {response.text if response else 'N/A'}")
        
        send_pdf_to_telegram(output_file_saamana, "saamana", today_date_word)
            
        try:
            os.remove(output_file_saamana)
        except OSError as e:
            print(f"Error removing file {output_file_saamana}: {e}")
    else:
        print("Failed to generate Saamana PDF. No email and telegram sent.")

    output_file_pudhari = download_and_merge_newspaper(today_date, "pudhari")   

    if output_file_pudhari:
        send_pdf_to_telegram(output_file_pudhari, "saamana", today_date_word)
            
        try:
            os.remove(output_file_pudhari)
        except OSError as e:
            print(f"Error removing file {output_file_pudhari}: {e}")
    
    else:
        print("Failed to generate Pudhari PDF. No telegram sent.")
