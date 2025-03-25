from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import requests
from bs4 import BeautifulSoup

DATABASE_URL = "sqlite:///./expenses.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    date = Column(Date, index=True)
    amount_ua = Column(Float)
    amount_usd = Column(Float)

Base.metadata.create_all(bind=engine)

app = FastAPI()

class ExpenseCreate(BaseModel):
    title: str
    date: str
    amount: float

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None

class ExpenseOut(BaseModel):
    id: int
    title: str
    date: str
    amount_ua: float
    amount_usd: float

    class Config:
        from_attributes = True

    @field_validator("date", mode="before")
    def format_date(cls, v):
        if isinstance(v, date):
            return v.strftime("%d.%m.%Y")
        return v

def get_exchange_rate():
    try:
        url = "https://www.exchangerates.org.uk/UAH-USD-exchange-rate-history.html"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        rate_tag = soup.find("span", id="usd-rate")
        if rate_tag is None:
            return 0.041
        rate = float(rate_tag.text.strip())
        return rate
    except Exception:
        return 0.041

def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%d.%m.%Y").date()

@app.post("/expenses/", response_model=ExpenseOut)
def create_expense(expense_data: ExpenseCreate):
    db: Session = SessionLocal()
    try:
        expense_date = parse_date(expense_data.date)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use dd.mm.YYYY")
    rate = get_exchange_rate()
    amount_usd = expense_data.amount * rate
    db_expense = Expense(
        title=expense_data.title, 
        date=expense_date, 
        amount_ua=expense_data.amount, 
        amount_usd=amount_usd
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    db.close()
    return db_expense

@app.get("/expenses/", response_model=List[ExpenseOut])
def get_expenses(start_date: str, end_date: str):
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use dd.mm.YYYY")
    db: Session = SessionLocal()
    expenses = db.query(Expense).filter(Expense.date >= start, Expense.date <= end).all()
    db.close()
    return expenses

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    db: Session = SessionLocal()
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense is None:
        db.close()
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    db.close()
    return {"detail": "Expense deleted"}

@app.put("/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, expense_update: ExpenseUpdate):
    db: Session = SessionLocal()
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense is None:
        db.close()
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense_update.title is not None:
        expense.title = expense_update.title
    if expense_update.date is not None:
        try:
            expense.date = parse_date(expense_update.date)
        except Exception:
            db.close()
            raise HTTPException(status_code=400, detail="Invalid date format. Use dd.mm.YYYY")
    if expense_update.amount is not None:
        expense.amount_ua = expense_update.amount
        rate = get_exchange_rate()
        expense.amount_usd = expense_update.amount * rate
    db.commit()
    db.refresh(expense)
    db.close()
    return expense
