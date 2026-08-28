# KinoBot

KinoBot is a Telegram movie-delivery bot built with Python and aiogram. It allows admins to upload videos to a private storage channel and share them with users through short access codes, while requiring users to join configured channels before they can request content.

## Features

- Upload and store movie videos in a dedicated Telegram channel
- Assign a unique access code to each movie
- Share movies to users by sending the code in chat
- Enforce channel membership before users can access content
- Manage required channels and movie entries from admin commands
- Store movie metadata in SQLite

## Tech Stack

- Python 3
- aiogram
- SQLite
- python-dotenv

## Project Structure

```text
.
├── app/
│   ├── handlers/
│   │   ├── admin.py      # Admin flows and moderation commands
│   │   ├── join.py       # Join-request handling
│   │   └── user.py       # User-facing movie lookup and access flow
│   ├── services/
│   │   └── channel_links.py
│   ├── config.py         # Environment configuration
│   ├── db.py             # SQLite setup and database helpers
│   ├── keyboards.py      # Telegram inline keyboards
│   ├── states.py         # FSM states for admin upload flow
│   ├── utils.py          # Helper functions for membership checks, formatting, etc.
│   └── __init__.py
├── .env.example          # Example environment variables
├── main.py               # Bot startup
├── movies.db             # SQLite database file
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## Prerequisites

- Python 3.10+
- A Telegram bot token from BotFather
- A Telegram channel where the bot can upload videos
- At least one admin user ID
- Optional configured membership channels the bot checks before allowing access

## Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Then update it with your values:

```env
BOT_TOKEN="1234567:ABCD-EFGH"
ADMIN_IDS="123456,12344312"
STORAGE_CHANNEL_ID="-1001234567"
DB_PATH="movies.db"
```

Notes:

- `BOT_TOKEN`: Telegram bot token
- `ADMIN_IDS`: Comma-separated Telegram user IDs that can manage the bot
- `STORAGE_CHANNEL_ID`: Channel where new movies are uploaded before being shared
- `DB_PATH`: Optional database path; defaults to `movies.db`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Bot

```bash
python main.py
```

The bot will start polling Telegram for updates using aiogram.

## Admin Commands

These commands are intended for bot admins:

- `/add` — start the movie upload flow
- `/remove <code>` — remove a movie by its code
- `/addchannel <chat_id> <invite_link>` — register a channel that users must join
- `/channels` — list configured membership channels
- `/removechannel <chat_id>` — remove a configured channel
- `/help` — show admin help text
- `/cancel` — cancel the current FSM flow

## User Flow

1. User starts the bot with `/start`
2. If the user is not a member of required channels, the bot shows invite links
3. Once membership is confirmed, the user can send a movie code
4. The bot fetches the matching movie and sends the video back

## Example usage

- Admin: `/add`
- Bot prompts for video, name, description, and code
- User: `ABC123`
- Bot sends the corresponding video in chat

## How Data is Stored

The project uses SQLite to keep:

- movie codes
- file IDs
- storage message IDs
- names and descriptions
- configured channels
- join-request tracking

## License

This project is currently distributed without a formal license file. If you plan to share or deploy it publicly, add a license before production use.

## Notes

- The bot must be an admin of the storage channel to upload media successfully.
- Channel invite links must point to the correct Telegram chats and remain valid for membership checks.
- The bot is designed for a specific movie-sharing workflow and can be adapted for other content distribution scenarios.
