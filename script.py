import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
from PyPDF2 import PdfMerger
import os
from datetime import datetime
import concurrent.futures

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

def send_email_mailgun(subject, body, to_email, attachment_path):
    MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
    MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
    
    session = requests.Session()
    session.mount('https://', SSLAdapter())

    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        files=[("attachment", ("Saamana.pdf", open(attachment_path, "rb").read()))],
        data={"from": f"Cos <mailgun@{MAILGUN_DOMAIN}>",
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
                    filename = future.result()
                    if filename:
                        pdf_files.append(filename)
                    else:
                        break
                future_to_page.clear()
                if not filename:
                    break

    if pdf_files:
        output_filename = f"SAAMANA_PUN_{date_str}.pdf"
        merge_pdfs(pdf_files, output_filename)
        
        # Clean up individual page PDFs
        for pdf in pdf_files:
            os.remove(pdf)
        
        print(f"Downloaded {len(pdf_files)} pages into {output_filename}")
        return output_filename
    else:
        print("No pages were downloaded. Please check the date and try again.")
        return None

if __name__ == "__main__":
    today_date = datetime.now().strftime("%Y%m%d")
    today_date_word = datetime.now().strftime("%b %d, %Y")
    output_file = download_and_merge_newspaper(today_date)
    
    if output_file:
        subject = f"Sammna - {today_date_word}"
        body = f"Please find attached PDF for {today_date_word}."
        to_email = os.getenv('RECEIVER_EMAIL')
        
        response = send_email_mailgun(subject, body, to_email, output_file)
        if response.status_code == 200:
            print(f"Email sent successfully with attachment: {output_file}")
        else:
            print(f"Failed to send email. Status code: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Optional: Remove the merged PDF after sending
        os.remove(output_file)
    else:
        print("Failed to generate PDF. No email sent.")