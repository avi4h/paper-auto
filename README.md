### Paper-Auto
	
Automates daily download, merging, compressing, and distribution of multiple e-newspaper PDFs via email and Telegram using Python, concurrent futures, PyPDF2, Ghostscript, Telegram API and Mailgun API, scheduled via GitHub Actions.
  


Add the secrets:
`TELEGRAM_BOT_TOKEN` `TELEGRAM_CHAT_ID` `MAILGUN_API_KEY` `MAILGUN_DOMAIN` `RECEIVER_EMAIL`

The workflow in `.github/workflows/schedule.yml` is set to run daily at 2:00 AM UTC that is around 8:00 AM IST. It is written to run on Ubuntu. For other operating systems, you should just change ghostscript configs in `script.py` as mentioned in the code comments.

<<<<<<< HEAD
=======


>>>>>>> f7ac3b9a4cb60c85da476d78c333992f6b26e9a5
