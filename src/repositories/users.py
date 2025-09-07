import logging

from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import insert, select, update, func
from typing import Optional

from src.models.models import Users
from src.schemas.users import UserSchema, UpdatePersonalDataSchema


class UserRepository:
    @staticmethod
    def create_user(session: Session, data: dict) -> UserSchema:
        statement = insert(Users).values(**data).returning(Users)
        result = session.execute(statement)
        logging.info(result)
        session.commit()

        created_user = result.scalars().first()
        logging.info(created_user)
        new_user = created_user.to_read_model()
        logging.info(new_user)
        return new_user

    @staticmethod
    def get_user_by_username(session: Session, username: str) -> Optional[UserSchema]:
        statement = select(Users).options(joinedload(Users.prizes)).filter_by(username=username)
        result = session.execute(statement).unique()

        user = result.scalar_one_or_none()
        if not user:
            return None

        return user.to_read_model()

    @staticmethod
    def update_user_balance(session: Session, user_id: int, value: int, task_id: int):
        user_check_stmt = select(Users.in_progress).where(Users.id == user_id)
        result = session.execute(user_check_stmt)
        user_in_progress = result.scalar_one_or_none()

        if user_in_progress and task_id in user_in_progress:
            remove_task_stmt = update(Users).where(Users.id == user_id).values(
                in_progress=func.array_remove(Users.in_progress, task_id)
            )
            session.execute(remove_task_stmt)
            logging.debug(f"Удален task_id {task_id} из in_progress.")

            update_done_tasks_stmt = update(Users).where(Users.id == user_id).values(
                done_tasks=func.array_append(Users.done_tasks, task_id)
            )
            session.execute(update_done_tasks_stmt)
            logging.debug(f"Добавлен task_id {task_id} в done_tasks.")

        statement = update(Users).where(Users.id == user_id).values(balance=Users.balance + value)
        result = session.execute(statement)
        logging.debug(result)

        update_tasks_stmt = (
            update(Users)
            .where(Users.id == user_id)
            .values(done_tasks=func.array_append(Users.done_tasks, task_id))
        )
        result = session.execute(update_tasks_stmt)
        logging.debug(result)

        session.commit()

        statement = select(Users).filter_by(id=user_id)
        result = session.execute(statement)
        logging.debug(result)

        user = result.scalar_one_or_none()

        if not user:
            return None
        return user.to_read_model()

    @staticmethod
    def update_user_personal_data(session: Session, username: str, new_data: UpdatePersonalDataSchema):
        update_values = {}

        if new_data.full_name is not None and new_data.full_name != "":
            update_values['full_name'] = new_data.full_name

        if new_data.group_number is not None and new_data.group_number != "":
            update_values['group_number'] = new_data.group_number

        statement = update(Users).where(Users.username == username).values(**update_values)
        session.execute(statement)
        session.commit()

        statement = select(Users).filter_by(username=username)
        result = session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return None
        return user.to_read_model()

    @staticmethod
    def delete_task_from_in_progress(session: Session, user_id: int, task_id: int):
        user_check_stmt = select(Users.in_progress).where(Users.id == user_id)
        result = session.execute(user_check_stmt)
        user_in_progress = result.scalar_one_or_none()

        if user_in_progress and task_id in user_in_progress:
            remove_task_stmt = update(Users).where(Users.id == user_id).values(
                in_progress=func.array_remove(Users.in_progress, task_id)
            )
            session.execute(remove_task_stmt)
            logging.debug(f"Удален task_id {task_id} из in_progress.")
            session.commit()
        statement = select(Users).filter_by(id=user_id)
        result = session.execute(statement)
        logging.debug(result)

        user = result.scalar_one_or_none()

        if not user:
            return None
        return user.to_read_model()

    @staticmethod
    def get_top_users_by_balance(session: Session, telegram_id: int):
        statement = (
            select(Users)
            .options(selectinload(Users.prizes))
        )
        result = session.execute(statement)
        users = result.scalars().all()

        def calculate_possible_balance(user):
            done_tasks = set(user.done_tasks)
            return sum([
                {
                    1: 100, 2: 100, 3: 100, 4: 100, 5: 100, 6: 100,
                    7: 200, 8: 200, 9: 200, 10: 200, 11: 200,
                    12: 200, 13: 200, 14: 300, 15: 300, 16: 300,
                    17: 100, 18: 100, 19: 100, 20: 200, 21: 200,
                    22: 200, 23: 200, 24: 200, 25: 300, 26: 300,
                    27: 300, 28: 100, 29: 100, 30: 200, 31: 200,
                    32: 300, 33: 300, 34: 300, 35: 300, 36: 300
                }.get(task_id, 0)
                for task_id in done_tasks
            ])

        enriched_users = [{
            "user": user,
            "max_balance": calculate_possible_balance(user)
        } for user in users]

        enriched_users.sort(key=lambda x: x["max_balance"], reverse=True)

        top_users = [u["user"].to_read_model() for u in enriched_users[:10]]

        user_info = None
        if telegram_id is not None:
            for index, entry in enumerate(enriched_users):
                if entry["user"].telegram_id == telegram_id:
                    user_info = {
                        "rank": index + 1,
                        "username": entry["user"].username,
                        "telegram_id": entry["user"].telegram_id,
                        "max_possible_balance": entry["max_balance"]
                    }
                    break

        return top_users, user_info

