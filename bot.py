import logging
import asyncio
import requests
import pandas as pd
from io import BytesIO
from datetime import datetime
import tempfile
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

API_SERVER_URL = "http://localhost:8000"
BOT_TOKEN = "7608065873:AAFDaOt_VfdKDlepgZcJFLxEpbNmSLzsxAk"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class AddExpenseStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_amount = State()

class ReportStates(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()

class DeleteExpenseStates(StatesGroup):
    waiting_for_id = State()

class EditExpenseStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_new_title = State()
    waiting_for_new_amount = State()

def main_menu():
    buttons = [
        [KeyboardButton(text="Додати статтю витрат")],
        [KeyboardButton(text="Отримати звіт витрат")],
        [KeyboardButton(text="Видалити статтю витрат")],
        [KeyboardButton(text="Відредагувати статтю витрат")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Ласкаво просимо до бота контролю витрат!", reply_markup=main_menu())

@dp.message(F.text == "Додати статтю витрат")
async def add_expense_start(message: types.Message, state: FSMContext):
    await message.answer("Введіть назву статті витрат:")
    await state.set_state(AddExpenseStates.waiting_for_title)

@dp.message(AddExpenseStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введіть дату витрати у форматі dd.mm.YYYY:")
    await state.set_state(AddExpenseStates.waiting_for_date)

@dp.message(AddExpenseStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except Exception:
        await message.answer("Невірний формат дати. Будь ласка, введіть у форматі dd.mm.YYYY:")
        return
    await state.update_data(date=message.text)
    await message.answer("Введіть суму витрати (у гривнях):")
    await state.set_state(AddExpenseStates.waiting_for_amount)

@dp.message(AddExpenseStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
    except Exception:
        await message.answer("Будь ласка, введіть числове значення для суми витрати.")
        return
    await state.update_data(amount=amount)
    data = await state.get_data()
    payload = {
        "title": data["title"],
        "date": data["date"],
        "amount": data["amount"]
    }
    try:
        response = requests.post(f"{API_SERVER_URL}/expenses/", json=payload)
        if response.status_code == 200:
            await message.answer("Статтю витрат додано успішно!", reply_markup=main_menu())
        else:
            await message.answer(f"Помилка при додаванні: {response.json().get('detail')}", reply_markup=main_menu())
    except Exception as e:
        await message.answer("Помилка з'єднання з сервером.", reply_markup=main_menu())
        print("Error adding expense:", e)
    await state.clear()

@dp.message(F.text == "Отримати звіт витрат")
async def report_expense_start(message: types.Message, state: FSMContext):
    await message.answer("Введіть дату початку періоду (dd.mm.YYYY):")
    await state.set_state(ReportStates.waiting_for_start_date)

@dp.message(ReportStates.waiting_for_start_date)
async def process_report_start(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except Exception:
        await message.answer("Невірний формат дати. Введіть у форматі dd.mm.YYYY:")
        return
    await state.update_data(start_date=message.text)
    await message.answer("Введіть дату кінця періоду (dd.mm.YYYY):")
    await state.set_state(ReportStates.waiting_for_end_date)

@dp.message(ReportStates.waiting_for_end_date)
async def process_report_end(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except Exception:
        await message.answer("Невірний формат дати. Введіть у форматі dd.mm.YYYY:")
        return
    await state.update_data(end_date=message.text)

    data = await state.get_data()
    start_date = data["start_date"]
    end_date = data["end_date"]
    try:
        response = requests.get(f"{API_SERVER_URL}/expenses/", params={"start_date": start_date, "end_date": end_date})
        if response.status_code == 200:
            expenses = response.json()
            if not expenses:
                await message.answer("За вказаний період витрати відсутні.", reply_markup=main_menu())
            else:
                df = pd.DataFrame(expenses)
                total = df["amount_ua"].sum()
                total_row = {"id": "", "title": "Загальна сума", "date": "", "amount_ua": total, "amount_usd": ""}
                df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine="xlsxwriter")
                df.to_excel(writer, index=False, sheet_name="Expenses")
                writer.close()
                output.seek(0)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(output.getvalue())
                    tmp.flush()
                    tmp_path = tmp.name
                file_doc = FSInputFile(tmp_path, filename="report.xlsx")
                await message.answer_document(
                    document=file_doc,
                    caption=f"Загальна сума витрат: {total} грн",
                    reply_markup=main_menu()
                )
                os.remove(tmp_path)
        else:
            await message.answer("Помилка при отриманні даних з сервера.", reply_markup=main_menu())
    except Exception as e:
        await message.answer("Помилка з'єднання з сервером.", reply_markup=main_menu())
        print("Error generating report:", e)
    await state.clear()

@dp.message(F.text == "Видалити статтю витрат")
async def delete_expense_start(message: types.Message, state: FSMContext):
    try:
        response = requests.get(f"{API_SERVER_URL}/expenses/", params={"start_date": "01.01.2000", "end_date": "31.12.2100"})
        if response.status_code == 200:
            expenses = response.json()
            if not expenses:
                await message.answer("Немає витрат для видалення.", reply_markup=main_menu())
                return
            df = pd.DataFrame(expenses)
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine="xlsxwriter")
            df.to_excel(writer, index=False, sheet_name="Expenses")
            writer.close()
            output.seek(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(output.getvalue())
                tmp.flush()
                tmp_path = tmp.name
            file_doc = FSInputFile(tmp_path, filename="expenses.xlsx")
            await message.answer_document(
                document=file_doc,
                caption="Перегляньте ID витрат та введіть ID статті для видалення:",
                reply_markup=main_menu()
            )
            os.remove(tmp_path)
            await state.set_state(DeleteExpenseStates.waiting_for_id)
        else:
            await message.answer("Помилка при отриманні даних з сервера.", reply_markup=main_menu())
    except Exception as e:
        await message.answer("Помилка з'єднання з сервером.", reply_markup=main_menu())
        print("Error retrieving expenses for deletion:", e)

@dp.message(DeleteExpenseStates.waiting_for_id)
async def process_delete_id(message: types.Message, state: FSMContext):
    try:
        expense_id = int(message.text)
    except Exception:
        await message.answer("Введіть числове значення ID.")
        return
    try:
        response = requests.delete(f"{API_SERVER_URL}/expenses/{expense_id}")
        if response.status_code == 200:
            await message.answer("Статтю витрат видалено успішно.", reply_markup=main_menu())
        else:
            await message.answer(f"Помилка: {response.json().get('detail')}", reply_markup=main_menu())
    except Exception as e:
        await message.answer("Помилка з'єднання з сервером.", reply_markup=main_menu())
        print("Error deleting expense:", e)
    await state.clear()

@dp.message(F.text == "Відредагувати статтю витрат")
async def edit_expense_start(message: types.Message, state: FSMContext):
    try:
        response = requests.get(f"{API_SERVER_URL}/expenses/", params={"start_date": "01.01.2000", "end_date": "31.12.2100"})
        if response.status_code == 200:
            expenses = response.json()
            if not expenses:
                await message.answer("Немає витрат для редагування.", reply_markup=main_menu())
                return
            df = pd.DataFrame(expenses)
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine="xlsxwriter")
            df.to_excel(writer, index=False, sheet_name="Expenses")
            writer.close()
            output.seek(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(output.getvalue())
                tmp.flush()
                tmp_path = tmp.name
            file_doc = FSInputFile(tmp_path, filename="expenses.xlsx")
            await message.answer_document(
                document=file_doc,
                caption="Перегляньте ID витрат та введіть ID статті для редагування:",
                reply_markup=main_menu()
            )
            os.remove(tmp_path)
            await state.set_state(EditExpenseStates.waiting_for_id)
        else:
            await message.answer("Помилка при отриманні даних з сервера.", reply_markup=main_menu())
    except Exception as e:
        await message.answer("Помилка з'єднання з сервером.", reply_markup=main_menu())
        print("Error retrieving expenses for editing:", e)

@dp.message(EditExpenseStates.waiting_for_id)
async def process_edit_id(message: types.Message, state: FSMContext):
    try:
        expense_id = int(message.text)
    except Exception:
        await message.answer("Введіть числове значення ID.")
        return
    await state.update_data(expense_id=expense_id)
    await message.answer("Введіть нову назву статті витрат:")
    await state.set_state(EditExpenseStates.waiting_for_new_title)

@dp.message(EditExpenseStates.waiting_for_new_title)
async def process_edit_title(message: types.Message, state: FSMContext):
    await state.update_data(new_title=message.text)
    await message.answer("Введіть нову суму витрати (у гривнях):")
    await state.set_state(EditExpenseStates.waiting_for_new_amount)

@dp.message(EditExpenseStates.waiting_for_new_amount)
async def process_edit_amount(message: types.Message, state: FSMContext):
    try:
        new_amount = float(message.text)
    except Exception:
        await message.answer("Введіть числове значення для суми.")
        return
    data = await state.get_data()
    expense_id = data["expense_id"]
    payload = {
        "title": data["new_title"],
        "amount": new_amount
    }
    try:
        response = requests.put(f"{API_SERVER_URL}/expenses/{expense_id}", json=payload)
        if response.status_code == 200:
            await message.answer("Статтю витрат відредаговано успішно.", reply_markup=main_menu())
        else:
            await message.answer(f"Помилка: {response.json().get('detail')}", reply_markup=main_menu())
    except Exception as e:
        await message.answer("Помилка з'єднання з сервером.", reply_markup=main_menu())
        print("Error editing expense:", e)
    await state.clear()

if __name__ == '__main__':
    async def main():
        await dp.start_polling(bot, skip_updates=True)
    asyncio.run(main())
