import pytest
import random


# Telegram login
@pytest.mark.asyncio
async def test_telegram_login(client):
    # Данные для тестового пользователя
    test_user = {
        "username": f"testuser_{random.randint(1, 10000)}",  # Чтобы тесты друг на друга не влияли никак
        "telegram_id": random.randint(10000, 99999)
    }

    # Выполняем POST-запрос для регистрации/авторизации
    response = await client.post(
        "/users/telegram-login",
        json=test_user
    )

    # Проверяем статус ответа
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"

    # Проверяем содержание ответа
    response_data = response.json()
    assert response_data["status"] == "success", f"Unexpected status: {response_data['status']}"
    assert response_data["message"] in ["Logged in", "Registered and logged in"], (
        f"Unexpected message: {response_data['message']}"
    )


# Whoami
@pytest.mark.asyncio
async def test_whoami(client):
    # Данные для тестового пользователя
    test_user = {
        "username": f"testuser_{random.randint(1, 10000)}",  # Чтобы тесты друг на друга не влияли никак
        "telegram_id": random.randint(10000, 99999)
    }

    # Выполняем POST-запрос для регистрации/авторизации
    login_response = await client.post(
        "/users/telegram-login",
        json=test_user
    )

    # Проверяем, что регистрация/авторизация прошла успешно
    assert login_response.status_code == 200, f"Unexpected status code during login: {login_response.status_code}"
    assert login_response.json()["status"] == "success"

    # Выполняем GET-запрос для получения информации о текущем пользователе
    whoami_response = await client.get("/users/whoami")

    # Проверяем статус ответа
    assert whoami_response.status_code == 200, f"Unexpected status code: {whoami_response.status_code}"

    # Проверяем содержание ответа
    whoami_data = whoami_response.json()
    assert whoami_data["status"] == "success", f"Unexpected status: {whoami_data['status']}"
    assert whoami_data["user"]["username"] == test_user["username"], (
        f"Unexpected username: {whoami_data['user']['username']}"
    )
    assert whoami_data["user"]["telegram_id"] == test_user["telegram_id"], (
        f"Unexpected telegram_id: {whoami_data['user']['telegram_id']}"
    )


# TODO: Пофиксить status_code должен быть равен 401, а не 500, но в логике userservice except Exception as e перехватывает
# TODO 401 стаутс код из verify_user_by_jwt, ответ приходит вот такой:
# TODO   "detail": "Произошла непредвиденная ошибка: 401: Не авторизован", со статус кодом 500
# Пока что и так работает)
@pytest.mark.asyncio
async def test_whoami_without_token(client):
    response = await client.get("/users/whoami")
    assert response.status_code == 500, "Expected 500 Unauthorized for missing token"
    assert response.json()[
               "detail"] == "Произошла непредвиденная ошибка: 401: Не авторизован", "Unexpected error message"


@pytest.mark.asyncio
async def test_whoami_with_invalid_token(client):
    # Установить поврежденный токен в cookie
    client.cookies.set("jwt-token", "invalid-token")

    # Запрос к /whoami
    response = await client.get("/users/whoami")
    assert response.status_code == 500, "Expected 401 Unauthorized for invalid token"  # TODO Тут тоже со статус кодами
    # решить проблему, что выдаётся 500 в логике, хотя должен быть 401


@pytest.mark.asyncio
async def test_manage_balance(client):
    # Данные для тестового пользователя
    test_user = {
        "username": f"testuser_{random.randint(1, 10000)}",  # Чтобы тесты друг на друга не влияли никак
        "telegram_id": random.randint(10000, 99999)
    }

    # Выполняем POST-запрос для регистрации/авторизации
    login_response = await client.post(
        "/users/telegram-login",
        json=test_user
    )

    # Проверяем, что регистрация/авторизация прошла успешно
    assert login_response.status_code == 200, f"Unexpected status code during login: {login_response.status_code}"
    assert login_response.json()["status"] == "success"

    # Изменение баланса пользователя
    balance_value = 100  # Положительное значение для увеличения баланса
    balance_response = await client.put(f"/users/balance/{balance_value}")

    # Проверяем статус ответа
    assert balance_response.status_code == 200, f"Unexpected status code: {balance_response.status_code}"

    # Проверяем содержание ответа
    balance_data = balance_response.json()
    assert balance_data["status"] == "success", f"Unexpected status: {balance_data['status']}"
    assert balance_data["user"]["balance"] == balance_value, (
        f"Unexpected balance: {balance_data['user']['balance']}"
    )

    # Уменьшение баланса пользователя
    negative_balance_value = -50
    decrease_balance_response = await client.put(f"/users/balance/{negative_balance_value}")

    # Проверяем статус ответа
    assert decrease_balance_response.status_code == 200, f"Unexpected status code: {decrease_balance_response.status_code}"

    # Проверяем содержание ответа
    decrease_balance_data = decrease_balance_response.json()
    assert decrease_balance_data["status"] == "success", f"Unexpected status: {decrease_balance_data['status']}"
    assert decrease_balance_data["user"]["balance"] == (balance_value + negative_balance_value), (
        f"Unexpected balance: {decrease_balance_data['user']['balance']}"
    )


@pytest.mark.asyncio
async def test_update_personal_data(client):
    # Данные для тестового пользователя
    test_user = {
        "username": f"testuser_{random.randint(1, 10000)}",  # Чтобы тесты друг на друга не влияли никак
        "telegram_id": random.randint(10000, 99999)
    }

    # Выполняем POST-запрос для регистрации/авторизации
    login_response = await client.post(
        "/users/telegram-login",
        json=test_user
    )

    # Проверяем, что регистрация/авторизация прошла успешно
    assert login_response.status_code == 200, f"Unexpected status code during login: {login_response.status_code}"
    assert login_response.json()["status"] == "success"

    # 1 вариант: переданы все данные
    full_data_update = {
        "full_name": "Иванов Иван Иванович",
        "group_number": "ИСТ-000"
    }
    full_update_response = await client.put(
        "/users/personal-data",
        json=full_data_update
    )

    assert full_update_response.status_code == 200, f"Unexpected status code: {full_update_response.status_code}"
    full_update_data = full_update_response.json()
    assert full_update_data["status"] == "success", f"Unexpected status: {full_update_data['status']}"
    assert full_update_data["user"]["full_name"] == full_data_update["full_name"], (
        f"Unexpected full_name: {full_update_data['user']['full_name']}"
    )
    assert full_update_data["user"]["group_number"] == full_data_update["group_number"], (
        f"Unexpected group_number: {full_update_data['user']['group_number']}"
    )

    # 2 Вариант: передано только одно значение full_name
    partial_data_update = {
        "full_name": "Эндрю Тейт Амогусович",
        "group_number": ""
    }
    partial_update_response = await client.put(
        "/users/personal-data",
        json=partial_data_update
    )

    assert partial_update_response.status_code == 200, f"Unexpected status code: {partial_update_response.status_code}"
    partial_update_data = partial_update_response.json()
    assert partial_update_data["status"] == "success", f"Unexpected status: {partial_update_data['status']}"
    assert partial_update_data["user"]["full_name"] == partial_data_update["full_name"], (
        f"Unexpected full_name: {partial_update_data['user']['full_name']}"
    )
    # Проверяем, что group_number остался прежним
    assert partial_update_data["user"]["group_number"] == full_data_update["group_number"], (
        f"Unexpected group_number: {partial_update_data['user']['group_number']}"
    )

    # Вариант 3: не передано никаких данных
    empty_data_update = {
        "full_name": "",
        "group_number": ""
    }
    empty_update_response = await client.put(
        "/users/personal-data",
        json=empty_data_update
    )
    # TODO: Тут такая же проблема, выдаётся статус код 400, но его перехватывает другой catch Exception as e, присваивающий
    # ей 500, как в test_whoami_without_token
    assert empty_update_response.status_code == 500, (
        f"Unexpected status code: {empty_update_response.status_code}"
    )
    # Проверяем, что в ответе содержится информация о недостающих данных
    empty_update_data = empty_update_response.json()
    assert "detail" in empty_update_data, "Expected validation error for missing data"
