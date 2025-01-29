from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, Message
from pydantic import BaseModel
from datetime import date, datetime
import uuid

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class MessageCreate(BaseModel):
    message: str


def get_date_from_header(request: Request) -> date:
    x_date = request.headers.get("x-date")
    if not x_date:
        raise HTTPException(status_code=400, detail="Missing x-date header")
    try:
        return date.fromisoformat(x_date)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid x-date format. Expected YYYY-MM-DD."
        )


@app.get("/messages")
def get_messages(request: Request, db: Session = Depends(get_db)):
    messages = db.query(Message).all()
    return messages


@app.post("/messages")
def create_message(
    message: MessageCreate, request: Request, db: Session = Depends(get_db)
):
    filter_date = get_date_from_header(request)
    new_message = Message(date=filter_date, message=message.message
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


@app.put("/messages/{old_message}")
def update_message(old_message: str, request: Request, db: Session = Depends(get_db)):
    new_message = request.headers.get("new-message")
    filter_date = get_date_from_header(request)

    print(old_message, new_message, filter_date)
    
    
    # Поиск старого сообщения по тексту
    db_message = db.query(Message).filter(Message.message == old_message, Message.date == filter_date).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Обновление сообщения
    db_message.message = new_message
    db.commit()
    return {"detail": "Message updated successfully"}

@app.delete("/messages/{message}")
def delete_message(message: str, request: Request, db: Session = Depends(get_db)):
    filter_date = get_date_from_header(request)

    # Поиск сообщения по тексту
    db_message = db.query(Message).filter(Message.message == message, Message.date == filter_date).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(db_message)
    db.commit()
    return {"detail": "Message deleted"}


