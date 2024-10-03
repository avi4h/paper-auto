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
    response = requests.get(url)
    if response.status_code == 200 and len(response.content) > 0:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename
    return None

def merge_pdfs(pdf_files, output_filename):
    merger = PdfMerger()
    for pdf in sorted(pdf_files, key=lambda x: int(x.split('_')[1].split('.')[0])):
        if pdf:
            merger.append(pdf)
    merger.write(output_filename)
    merger.close()

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

def download_and_merge_newspaper(date_str):
    base_url = "https://epaper.saamana.com/download.php?file=https://enewspapr.com/News/SAMANA/PUN/{year}/{month}/{day}/{date_str}_{page}.PDF&pageno={page}"
    
    year, month, day = date_str[:4], date_str[4:6], date_str[6:]
    formatted_url = base_url.format(year=year, month=month, day=day, date_str=date_str, page="{page}")

    pdf_files = []
    page = 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_page = {}
        while True:
            future = executor.submit(download_pdf, formatted_url.format(page=page), f"page_{page}.pdf")
            future_to_page[future] = page
            page += 1
            if len(future_to_page) >= 5:
                for future in concurrent.futures.as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        filename = future.result()
                        if filename:
                            pdf_files.append(filename)
                        else:
                            break
                    except Exception as e:
                        print(f"Error downloading page {page_num}: {e}")
                future_to_page.clear()
                if not filename:
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
        output_filename = f"SAAMANA_PUNE_{date_str}.pdf"
        merge_pdfs(pdf_files, output_filename)

        for pdf in pdf_files:
            os.remove(pdf)
        
        original_size = os.path.getsize(output_filename) / (1024 * 1024)  
        print(f"Merged {len(pdf_files)} pages into {output_filename} with size {original_size:.2f} MB")

        compressed_output_filename = f"COMPRESSED_SAAMANA_PUNE_{date_str}.pdf"
        compress_pdf(output_filename, compressed_output_filename)
        
        compressed_size = os.path.getsize(compressed_output_filename) / (1024 * 1024)  
        print(f"Compressed {output_filename} to {compressed_output_filename} with size {compressed_size:.2f} MB")
        
        return compressed_output_filename
    else:
        print("No pages were downloaded. Please check the date and try again.")
        return None

if __name__ == "__main__":
    today_date = datetime.now().strftime("%Y%m%d")
    today_date_word = datetime.now().strftime("%b %d, %Y")
    output_file = download_and_merge_newspaper(today_date)
    
    if output_file:
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
            
            try:
                os.remove(output_file)
            except OSError as e:
                print(f"Error removing file {output_file}: {e}")
    else:
        print("Failed to generate PDF. No email sent.")