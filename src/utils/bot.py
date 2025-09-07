import logging
import os

from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.models import Users

from aiogram import Bot


bot = Bot(token=os.getenv("TOKEN"))

characters = {
    1: "Баба Яга",
    2: "Водяной",
    3: "Жыж",
    4: "Змей Горыныч - 3 голова",
    5: "Белочка",
    6: "Добрыня Никитич",
    7: "Снегурочка",
    8: "Ырка",
    9: "Вий",
    10: "Золотая рыбка",
    11: "Кот Баюн",
    12: "Банник",
    13: "Серый волк",
    14: "Жар Птица",
    15: "Курочка Ряба",
    16: "Птица Гамаюн",
    17: "Колобок",
    18: "Соловей разбойник",
    19: "Царевна Лягушка",
    20: "Кикимора",
    21: "Илья Муромец",
    22: "Хихитун",
    23: "Змей Горыныч - 1 голова",
    24: "Избушка на курьих ножках",
    25: "Василиса",
    26: "Иван дурак",
    27: "Бабай",
    28: "Аука",
    29: "Гуси-лебеди",
    30: "Мавка",
    31: "Полуденница",
    32: "Кощей Бессмертный",
    33: "Леший",
    34: "Змей Горыныч - 2 голова",
    35: "Алеша Попович",
    36: "Барабашка"
}


async def notify_user_task_checked_correctly(session: Session, user_id: int, task_id: int):
    stmt = select(Users).where(Users.id == user_id)
    result = session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.telegram_id:
        return

    message = (f"Здрав будь, добрый молодец или красна девица!\nЗадание твоё проверено! Всё правильно ты решил, "
               f"славно потрудился!\n\n Задание «{characters[task_id]}» решено верно ✅")

    try:
        await bot.send_message(chat_id=user.telegram_id, text=message)
    except Exception as e:
        logging.warning(f"Не удалось отправить сообщение пользователю {user.telegram_id}: {e}")


async def notify_user_task_checked_incorrectly(session: Session, user_id: int, task_id: int):
    stmt = select(Users).where(Users.id == user_id)
    result = session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.telegram_id:
        return

    message = (f"Здрав будь, добрый молодец или красна девица!\nЗадание твоё проверено! Увы, но не правильно ты его "
               f"решил, попробуй ещё раз!\n\nЗадание «{characters[task_id]}» решено неверно ❌")

    try:
        await bot.send_message(chat_id=user.telegram_id, text=message)
    except Exception as e:
        logging.warning(f"Не удалось отправить сообщение пользователю {user.telegram_id}: {e}")
