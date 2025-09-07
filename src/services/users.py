import csv
import logging

from fastapi import HTTPException, Request
from fastapi import Response
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from starlette import status

from src.repositories.users import UserRepository
from src.schemas.users import (
    UserCreateSchema,
    TelegramLoginResponse,
    UpdatePersonalDataSchema, BaseResponse, UserSchema,
)
from src.utils.auth import verify_user_by_jwt

from src.jwt.tokens import (
    create_jwt_token, verify_jwt_token,
)
from src.utils.bot import notify_user_task_checked_correctly, notify_user_task_checked_incorrectly


def verify_data_check_string(data_check_string: str, expected_string: str, hash_value: str) -> bool:
    return CryptContext(schemes=["sha256_crypt"]).verify(data_check_string, hash_value)


def find_user_by_username(csv_filename, tg_username):
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            if row['telegram_username'] == tg_username:
                return row['name'], row['group']

        return None, None


class UserService:
    @staticmethod
    async def auth_user(
            session: Session,
            response: Response,
            user: UserCreateSchema
    ):
        """
        Основной метод аутентификации пользователя:
        - Если пользователь существует, создаётся JWT-токен.
        - Если пользователь не существует, создаётся новый пользователь, а затем создаётся JWT-токен.
        """
        csv_filename = "data.csv"
        username = user.username
        telegram_id = user.telegram_id
        logging.info({username, telegram_id})
        # data_check_string = user.data_check_string
        # hash_value = user.hash
        #
        # if not verify_data_check_string(data_check_string, "?????", hash_value):
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Неверная строка проверки или хэш"
        #     )

        token = create_jwt_token(username, telegram_id)
        logging.info(token)

        try:
            existing_user = UserRepository.get_user_by_username(session=session, username=username)
            if existing_user:
                response.set_cookie(key="jwt-token", value=token, httponly=True)
                return TelegramLoginResponse(
                    status="success",
                    message="Logged in"
                )

            full_name, group = find_user_by_username(csv_filename, username)
            logging.info({full_name, group})
            if not full_name or not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователь с tg_username '{username}' не найден."
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при нахождении юзера: {str(e)}")

        # TODO проверить
        users_dict = {
            "full_name": full_name,
            "group_number": group,
            "username": username,
            "telegram_id": telegram_id,
            "done_tasks": [],
            "in_progress": [],
            "balance": 0
        }
        try:
            logging.info(users_dict)
            UserRepository.create_user(session=session, data=users_dict)
        except Exception as e:
            logging.error(e)
            raise HTTPException(status_code=500, detail=f"Ошибка при создании юзера: {e}")
        response.set_cookie(key="jwt-token", value=token, httponly=True)
        return TelegramLoginResponse(
            status="success",
            message="Registered and logged in"
        )

        # except IntegrityError as e:
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail="Пользователь с таким telegram_id уже существует"
        #     )

        # except Exception as e:
        #     # Ловлю любые неожиданные ошибки
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Внутренняя ошибка базы данных: {e}"
        #         # Решил не выводить здесь с помощью str(e) полностью ошибку, так как она раскрывает все поля
        #         # базы данных, думаю так безопаснее
        #     )

    @staticmethod
    async def get_user_info(
            request: Request,
            session: Session
    ) -> BaseResponse:

        """
        Получает информацию о пользователе на основе JWT-токена.
        """
        try:
            user = await verify_user_by_jwt(request, session)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

            return BaseResponse(
                status="success",
                message="Пользователь по этому jwt-токену найден.",
                user=user
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Произошла непредвиденная ошибка: {e}"
            )

    @staticmethod
    async def manage_user_balance(
            request: Request,
            session: Session,
            value: int,
            user_id: int,
            task_id: int,
            task_status: str,
            tg: bool
    ) -> BaseResponse:
        """
        Получает значение и изменяет баланс пользователя на это значение, а также добавляет id задачи пользователю в "выполненные"
        """
        # Проверка по JWT-токену
        if not tg:
            try:
                user = await verify_user_by_jwt(request, session)
                if not user:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
                logging.debug(f"Пользователь найден: {user}")
            except Exception as e:
                logging.error(f"Ошибка при верификации JWT: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Произошла непредвиденная ошибка: {e}"
                )

        try:
            if task_status == "approved":
                user = UserRepository.update_user_balance(session, user_id, value, task_id)
                await notify_user_task_checked_correctly(session=session, user_id=user_id, task_id=task_id)
                logging.debug(user)

                return BaseResponse(
                    status="success",
                    message="Баланс пользователя успешно обновлен",
                    user=user
                )
            elif task_status == "rejected":
                user = UserRepository.delete_task_from_in_progress(session=session, user_id=user_id, task_id=task_id)
                await notify_user_task_checked_incorrectly(session=session, user_id=user_id, task_id=task_id)
                return BaseResponse(
                    status="success",
                    message="Задача удалена из статуса 'На проверке'",
                    user=user
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Произошла непредвиденная ошибка: {e}"
            )

    @staticmethod
    async def update_user_personal_data(
            request: Request,
            session: Session,
            new_data: UpdatePersonalDataSchema,
    ) -> BaseResponse:
        """
        Получает значение и изменяет баланс пользователя на это значение
        """
        # Проверка по JWT-токену
        try:
            user = await verify_user_by_jwt(request, session)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Произошла непредвиденная ошибка: {e}"
            )

        try:
            if not new_data.full_name and not new_data.group_number:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустое тело запроса")

            user = await verify_user_by_jwt(request, session)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

            user = UserRepository.update_user_personal_data(session, user.username, new_data)

            return BaseResponse(
                status="success",
                message="Данные пользователя успешно обновлены",
                user=user
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Произошла непредвиденная ошибка: {e}"
            )

    @staticmethod
    async def get_top_users_by_balance(session: Session, request: Request) -> tuple[list[UserSchema, dict], dict]:
        try:
            user = await verify_user_by_jwt(request, session)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Произошла непредвиденная ошибка: {e}"
            )
        try:
            token = request.cookies.get("jwt-token")
            verified_token = verify_jwt_token(token)
            telegram_id = verified_token.get("telegram_id")
            top_users = UserRepository.get_top_users_by_balance(session, telegram_id)
            return top_users
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении топ-юзеров: {e}"
            )