# EVA-Bot 🤖

A Telegram bot built with Python using `telebot` and `Flask`.

## Features
- Telegram bot polling
- Flask web server for Render deployment
- Threaded execution for concurrent operations

## Setup

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/gsgshsggs649-max/EVA-Bot.git
cd EVA-Bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```bash
cp .env.example .env
```

4. Add your Telegram Bot Token to `.env`:
```
TELEGRAM_BOT_TOKEN=your_token_here
```

### Running Locally

```bash
python bot.py
```

The Flask server will start on `http://localhost:8080` and the bot will begin polling for messages.

## Deployment

### Render Deployment

1. Push to GitHub
2. Connect repository to Render
3. Set environment variable `TELEGRAM_BOT_TOKEN` in Render dashboard
4. Deploy!

## Project Structure

```
EVA-Bot/
├── bot.py              # Main bot script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
└── README.md          # This file
```

## License
MIT
