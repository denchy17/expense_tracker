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
