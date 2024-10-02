Efficient Python script that automates the daily download, merging, and email distribution of PDF files from the Saamana e-newspaper. Concurrency techniques and secure HTTP requests, this script ensures timely and automated delivery of the newspaper to the specified recipient.

## Setup

### Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/avi4h/saamana-auto.git
    cd saamana-auto
    ```

2. **Install dependencies**:
    ```sh
    python -m pip install --upgrade pip
    pip install requests PyPDF2
    ```

3. **Set up environment variables**:
    Create a `.env` file in the project directory with the following content:
    ```env
    MAILGUN_API_KEY=your-mailgun-api-key
    MAILGUN_DOMAIN=your-mailgun-domain
    RECEIVER_EMAIL=receiver-email@example.com
    ```

### GitHub Actions Configuration

1. **Add Secrets**:
    - Go to your GitHub repository.
    - Click on "Settings".
    - In the left sidebar, click on "Secrets and variables" and then "Actions".
    - Add the following secrets:
        - `MAILGUN_API_KEY`
        - `MAILGUN_DOMAIN`
        - `RECEIVER_EMAIL`

2. **Workflow Configuration**:
    The workflow is defined in `.github/workflows/schedule.yml` and is set to run daily at 2:00 AM UTC.

## Usage

The script is designed to run automatically via GitHub Actions. However, you can also run it manually:

```sh
python script.py
```

## Code Excerpt

Here's a technical excerpt from the script showcasing the SSL adapter for secure HTTP requests and the PDF merging functionality:

```sh
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
```

## Support

If you encounter any issues with this repository or have any questions, please open an issue in the Issues section. 

## Issues 

If necessary, I can remove this repository upon request.
