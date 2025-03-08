# `PAPER-AUTO`

<p align="left">
	<img src="https://img.shields.io/github/last-commit/avi4h/paper-auto?style=flat&logo=git&logoColor=white&color=green" alt="last-commit">
	<img src="https://img.shields.io/badge/Python-blue?style=flat&logo=Python&logoColor=yellow" alt="Python">
	<img src="https://img.shields.io/badge/Ghostscript-purple.svg?style=flat&logo=gitee&logoColor=black" alt="GitHub%20Actions">
	<img src="https://img.shields.io/badge/Telegram%20API-24A1DE.svg?style=flat&logo=Telegram&logoColor=white" alt="Telegram API">
    	<img src="https://img.shields.io/badge/Mailgun%20API-F06B66?style=flat&logo=mailgun&logoColor=white" alt="Mailgun%20API">
	<img src="https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat&logo=GitHub-Actions&logoColor=white" alt="GitHub%20Actions">
	<img src="https://img.shields.io/badge/Cron-DDF4FF?style=flat&logo=pythonanywhere&logoColor=black" alt="Cron Job">
</p>
	
**Automates daily download, merging, compressing, and distribution of multiple e-newspaper PDFs via email and Telegram using Python, concurrent futures, PyPDF2, Ghostscript, Telegram API and Mailgun API, scheduled via GitHub Actions.**
  
The script uses Ghostscript to compress the merged PDF file. Ensure Ghostscript is installed and added to your PATH.


Add the secrets:
`TELEGRAM_BOT_TOKEN` `TELEGRAM_CHAT_ID` `MAILGUN_API_KEY` `MAILGUN_DOMAIN` `RECEIVER_EMAIL`

The workflow in `.github/workflows/schedule.yml` is set to run daily at 2:00 AM UTC that is around 8:00 AM IST. It is written to run on Ubuntu. For other operating systems, you should just change ghostscript configs in `script.py` as mentioned in the code comments.

## ⚙️ Support

If you encounter any issues with this repository -> [Issues](https://github.com/avi4h/paper-auto/issues) 


