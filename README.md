# Expense Tracker Telegram Bot & API

This project is a Telegram bot for tracking expenses along with a FastAPI backend server that handles CRUD operations for expense items. The server uses SQLAlchemy with an SQLite database and includes currency conversion (UAH to USD) via web parsing (using requests and BeautifulSoup). The Telegram bot is built with aiogram and allows users to add expenses, get an expense report as an Excel file, delete an expense, or edit an expense.

## Features

- **FastAPI Server**

  - **CRUD Endpoints:** Create, read (by date range), update, and delete expense records.
  - **Currency Conversion:** Converts expense amounts in UAH to USD using live exchange rates (with fallback to a default rate).
  - **Database:** Uses SQLAlchemy ORM with SQLite.

- **Telegram Bot**
  - **Expense Entry:** Step-by-step process to add a new expense.
  - **Expense Report:** Request an expense report for a specific date range; returns a detailed `.xlsx` file with total expenses.
  - **Delete Expense:** Presents a list (via Excel file) and deletes an expense by its ID.
  - **Edit Expense:** Presents a list (via Excel file) and allows editing an expense’s title and amount.

## Project Structure

expense_tracker/

├── README.md # Project description and instructions.

├── requirements.txt # List of dependencies.

├── server.py # FastAPI server implementation.

└── bot.py # Telegram bot implementation using aiogram.

## Requirements

Make sure you have [Python 3.8+](https://www.python.org/downloads/) installed.

## Setup & Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/expense_tracker.git
   cd expense_tracker
   ```

2. **Install dependencies:**

   Use pip to install all required packages listed in requirements.txt:

   ```bash
   pip install -r requirements.txt
   ```

3. **Running the FastAPI Server:**

   1. Open a terminal in the project directory.
   2. Start the server using Uvicorn with auto-reload:

   ```bash
   uvicorn server:app --reload
   ```

   or

   ```bash
   python -m uvicorn server:app --reload
   ```

   The server will be available at http://localhost:8000.

4. **Running the Telegram Bot:**

   1. Open a separate terminal in the project directory.
   2. Make sure you have updated BOT_TOKEN in bot.py with your actual Telegram Bot token.
   3. Start the bot by running:

   ```bash
   python bot.py
   ```
