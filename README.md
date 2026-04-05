# 🤖 AI Newsletter Bot

A fully automated pipeline that fetches AI-related posts from X (Twitter), curates them into a beautiful newsletter, and delivers it to your Gmail inbox every morning — so you stay updated without opening social media.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- 📡 **Multi-source fetching** — X API v2, Nitter scraping, RSS feeds
- 🧠 **Smart AI filtering** — keyword matching, relevance scoring, junk removal
- 🗂 **Auto-categorization** — Breaking News, Research, Tools, Tips, Industry
- ⭐ **Top Pick of the Day** — highlights the most important update
- 🎨 **Beautiful HTML emails** — dark mode, mobile-friendly, clean design
- 🔄 **Deduplication** — tracks history to never send the same post twice
- ⏰ **Daily scheduling** — cron or built-in scheduler with retry logic
- ⚙️ **Easy configuration** — single YAML file for everything

---

## 🚀 Quick Start

### 1. Setup

```bash
chmod +x setup.sh && ./setup.sh
```

### 2. Configure

1. Copy the example configuration:
   ```bash
   cp config.example.yaml config.yaml
   ```
2. Edit `config.yaml` with your details:

```yaml
# Add/remove X (Twitter) accounts to follow
accounts:
  - OpenAI
  - AndrewYNg
  - GoogleDeepMind

# Your Gmail credentials
email:
  sender: "your_email@gmail.com"
  receiver: "your_email@gmail.com"
  app_password: "xxxx xxxx xxxx xxxx"   # Gmail App Password
```

### 3. Gmail App Password

> ⚠️ You must use a **Gmail App Password**, not your regular password.

1. Go to [Google Account → Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to **App Passwords** → Generate new
4. Copy the 16-character password into `config.yaml`

### 4. Run

```bash
# Activate virtual environment
source venv/bin/activate

# Demo mode (no API needed)
python main.py --demo

# Run once
python main.py

# Start daily scheduler
python main.py --schedule

# Preview newsletter without sending
python main.py --preview
```

---

## 📖 Usage

| Command | Description |
|---------|-------------|
| `python main.py` | Run pipeline once and send email |
| `python main.py --demo` | Generate newsletter with sample data |
| `python main.py --preview` | Generate HTML preview only |
| `python main.py --schedule` | Start daily auto-scheduler |
| `python main.py --test-email` | Send a test email |
| `python main.py --verbose` | Enable debug logging |
| `python main.py --config path/to/config.yaml` | Use custom config |

---

## ⏰ Cron Setup (Recommended)

For the most reliable daily automation:

```bash
chmod +x setup_cron.sh && ./setup_cron.sh
```

This automatically:
- Converts your IST time to UTC
- Installs a cron job
- Saves logs to `logs/cron.log`

Or manually:

```bash
# Edit crontab
crontab -e

# Add (example: 8:00 AM IST = 02:30 UTC)
30 2 * * * cd /path/to/project1 && ./venv/bin/python main.py >> logs/cron.log 2>&1
```

---

## 📁 Project Structure

```
project1/
├── main.py              # Entry point with CLI
├── config.yaml          # All configuration
├── requirements.txt     # Python dependencies
├── setup.sh             # Auto-setup script
├── setup_cron.sh        # Cron installation
├── README.md
├── src/
│   ├── __init__.py
│   ├── config_loader.py # Configuration management
│   ├── fetcher.py       # X post fetching (API/scraping/RSS)
│   ├── filter.py        # AI content filtering & scoring
│   ├── newsletter.py    # Newsletter generation
│   ├── template_builder.py  # Inline HTML builder
│   ├── emailer.py       # Gmail SMTP sender
│   ├── scheduler.py     # Daily scheduling with retry
│   └── demo_data.py     # Sample data for testing
├── templates/
│   └── newsletter.html  # Jinja2 email template
├── history/             # Deduplication tracking
└── logs/                # Application logs
```

---

## 🛠 X (Twitter) Data Sources

The bot tries multiple methods in order:

| Priority | Method | Requirements |
|----------|--------|-------------|
| 1 | **X API v2** | Bearer token (apply at [developer.x.com](https://developer.x.com)) |
| 2 | **Nitter** | No credentials needed |
| 3 | **RSS bridges** | No credentials needed |

For best results, add your X API bearer token to `config.yaml`:

```yaml
x_api:
  bearer_token: "your_bearer_token_here"
```

---

## 📰 Newsletter Sections

| Section | Emoji | Content |
|---------|-------|---------|
| Breaking News | 🔥 | Major announcements, launches |
| Research & Papers | 🧠 | Arxiv papers, studies, benchmarks |
| Tools & Releases | 🛠 | Libraries, SDKs, open-source |
| Practical Tips | 💡 | Tutorials, guides, best practices |
| Industry Updates | 📊 | Funding, regulation, market trends |

---

## 🎨 Customization

### Add/Remove Accounts

```yaml
accounts:
  - NewAccount
  # - RemovedAccount  (comment out to disable)
```

### Change Send Time

```yaml
schedule:
  time: "07:30"          # Any 24hr format
  timezone: "Asia/Kolkata"
```

### Toggle Dark Mode

```yaml
newsletter:
  dark_mode: false   # Switch to light mode
```

### Adjust Content Volume

```yaml
newsletter:
  max_items_per_section: 8   # More items per section
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| No posts fetched | Check internet; try `--demo` to verify pipeline |
| Auth error | Regenerate Gmail App Password |
| "2-Step Verification required" | Enable 2FA on Google Account first |
| Empty newsletter | Add more accounts or broaden keywords |
| Nitter blocked | Instances rotate; system auto-tries alternatives |

---

## 📄 License

MIT License — free for personal and commercial use.
