# 📡 API Reference - ML сервис рекомендаций фильмов

## 🔗 Базовый URL

```
http://localhost:8000
```

## 🔐 Аутентификация

Система использует **HTTP Basic Authentication** для защищенных endpoint'ов.

### Формат заголовка
```
Authorization: Basic <base64(email:password)>
```

### Пример
```bash
# Для пользователя test@example.com с паролем password123
curl -u "test@example.com:password123" http://localhost:8000/api/users/balance
```

## 📋 Общие заголовки

### Request Headers
```
Content-Type: application/json
Authorization: Basic <credentials>  # для защищенных endpoints
```

### Response Headers
```
X-Process-Time: <время_обработки_в_секундах>
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

## 🏠 Публичные Endpoints

### 1. **Информация о сервисе**
```http
GET /
```

**Описание**: Возвращает основную информацию о сервисе

**Response**:
```json
{
  "message": "Welcome to Movie Recommender API"
}
```

**Status Codes**:
- `200 OK` - Успешный ответ
- `500 Internal Server Error` - Ошибка сервера

### 2. **Проверка состояния**
```http
GET /health
```

**Описание**: Проверка работоспособности сервиса

**Response**:
```json
{
  "status": "healthy"
}
```

**Status Codes**:
- `200 OK` - Сервис работает
- `503 Service Unavailable` - Сервис недоступен

## 👤 Пользователи (Users)

### 1. **Регистрация пользователя**
```http
POST /api/users/signup
```

**Описание**: Создание нового пользователя

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "StrongPass123",
  "is_admin": false
}
```

**Валидация пароля**:
- Минимум 8 символов
- Обязательно: верхний регистр, нижний регистр, цифры

**Response**:
```json
{
  "message": "User successfully registered"
}
```

**Status Codes**:
- `201 Created` - Пользователь создан
- `400 Bad Request` - Неверный формат пароля
- `409 Conflict` - Пользователь уже существует
- `500 Internal Server Error` - Ошибка создания

### 2. **Аутентификация пользователя**
```http
POST /api/users/signin
```

**Описание**: Вход в систему

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "StrongPass123"
}
```

**Response**:
```json
{
  "message": "User signed in successfully"
}
```

**Status Codes**:
- `200 OK` - Успешный вход
- `403 Forbidden` - Неверные учетные данные
- `500 Internal Server Error` - Ошибка сервера

## 💰 Баланс и транзакции

### 1. **Получение баланса**
```http
GET /api/users/balance
```

**Описание**: Получение текущего баланса пользователя

**Требует**: Аутентификация

**Response**:
```json
{
  "Current balance": 150.0
}
```

**Status Codes**:
- `200 OK` - Баланс получен
- `401 Unauthorized` - Не авторизован
- `500 Internal Server Error` - Ошибка сервера

### 2. **Изменение баланса**
```http
POST /api/users/balance/adjust
```

**Описание**: Пополнение или списание баланса

**Требует**: Аутентификация

**Request Body**:
```json
{
  "email": "user@example.com",
  "amount": 50.0
}
```

**Правила**:
- Пользователь может изменять только свой баланс
- Администраторы: тип транзакции `admin_adjustment`
- Обычные пользователи: тип транзакции `deposit`

**Response**:
```json
{
  "message": "Successful balance adjustment"
}
```

**Status Codes**:
- `200 OK` - Баланс изменен
- `401 Unauthorized` - Не авторизован
- `403 Forbidden` - Попытка изменить чужой баланс
- `500 Internal Server Error` - Ошибка сервера

### 3. **История транзакций**
```http
GET /api/users/transaction/history
```

**Описание**: Получение истории всех транзакций пользователя

**Требует**: Аутентификация

**Response**:
```json
[
  {
    "id": 1,
    "amount": 20.0,
    "type": "entry_bonus",
    "timestamp": "2025-08-19T10:00:00Z",
    "wallet_id": 1
  },
  {
    "id": 2,
    "amount": -10.0,
    "type": "prediction",
    "timestamp": "2025-08-19T11:00:00Z",
    "wallet_id": 1
  }
]
```

**Типы транзакций**:
- `entry_bonus` - Начальный бонус при регистрации
- `deposit` - Пополнение баланса
- `withdrawal` - Списание средств
- `prediction` - Оплата за предсказание
- `admin_adjustment` - Административная корректировка

**Status Codes**:
- `200 OK` - История получена
- `401 Unauthorized` - Не авторизован
- `500 Internal Server Error` - Ошибка сервера

## 🎬 Предсказания и рекомендации

### 1. **История предсказаний**
```http
GET /api/events/prediction/history
```

**Описание**: Получение истории всех предсказаний пользователя

**Требует**: Аутентификация

**Response**:
```json
[
  {
    "id": 1,
    "input_text": "Рекомендуйте мне фантастические фильмы",
    "cost": 10.0,
    "timestamp": "2025-08-19T11:00:00Z",
    "user_id": 1,
    "movies": [
      {
        "id": 1,
        "title": "Матрица",
        "description": "Фантастический боевик...",
        "year": 1999,
        "genres": ["фантастика", "боевик"]
      }
    ]
  }
]
```

**Status Codes**:
- `200 OK` - История получена
- `401 Unauthorized` - Не авторизован
- `500 Internal Server Error` - Ошибка сервера

### 2. **Новые предсказания**
```http
POST /api/events/prediction/new
```

**Описание**: Получение новых рекомендаций фильмов

**Требует**: Аутентификация

**Query Parameters**:
- `message` (string, required) - Текст запроса пользователя
- `top` (integer, optional, default: 10) - Количество рекомендаций

**Request Example**:
```bash
curl -X POST "http://localhost:8000/api/events/prediction/new?message=Рекомендуйте%20мне%20фантастические%20фильмы&top=5" \
  -u "user@example.com:password123"
```

**Правила**:
- Стоимость: 10 кредитов для обычных пользователей, 0 для администраторов
- Минимальный баланс: 10 кредитов
- Максимальное количество: 50 рекомендаций

**Response**:
```json
[
  {
    "id": 1,
    "title": "Матрица",
    "description": "Фантастический боевик о хакере...",
    "year": 1999,
    "genres": ["фантастика", "боевик", "триллер"],
    "embedding": [0.1, 0.2, ...]
  },
  {
    "id": 2,
    "title": "Бегущий по лезвию",
    "description": "Киберпанк фильм...",
    "year": 1982,
    "genres": ["фантастика", "триллер", "драма"],
    "embedding": [0.3, 0.4, ...]
  }
]
```

**Status Codes**:
- `200 OK` - Рекомендации получены
- `400 Bad Request` - Неверный параметр top
- `401 Unauthorized` - Не авторизован
- `402 Payment Required` - Недостаточно средств
- `500 Internal Server Error` - Ошибка сервера

## 🌐 Web UI Endpoints

### 1. **Главная страница**
```http
GET /web
```

**Описание**: Основной веб-интерфейс для пользователей

**Response**: HTML страница с JavaScript функциональностью

### 2. **История предсказаний**
```http
GET /web/prediction-history
```

**Описание**: Страница с историей предсказаний пользователя

**Требует**: Аутентификация через Web UI

**Response**: HTML страница с историей

### 3. **История транзакций**
```http
GET /web/transaction-history
```

**Описание**: Страница с историей транзакций пользователя

**Требует**: Аутентификация через Web UI

**Response**: HTML страница с историей

## 📊 Модели данных

### UserSignupRequest
```json
{
  "email": "string (EmailStr)",
  "password": "string (min 8 chars, uppercase, lowercase, digit)",
  "is_admin": "boolean (default: false)"
}
```

### UserSigninRequest
```json
{
  "email": "string (EmailStr)",
  "password": "string"
}
```

### BalanceAdjustRequest
```json
{
  "email": "string (EmailStr)",
  "amount": "float"
}
```

### MovieOut
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "year": "integer",
  "genres": "array of strings",
  "embedding": "array of floats (384 dimensions)"
}
```

### PredictionOut
```json
{
  "id": "integer",
  "input_text": "string",
  "cost": "float",
  "timestamp": "datetime",
  "user_id": "integer",
  "movies": "array of MovieOut"
}
```

### Transaction
```json
{
  "id": "integer",
  "amount": "float",
  "type": "string (enum)",
  "timestamp": "datetime",
  "wallet_id": "integer"
}
```

## ⚠️ Обработка ошибок

### Общий формат ошибки
```json
{
  "detail": "Описание ошибки"
}
```

### Коды ошибок
- `400 Bad Request` - Неверный запрос
- `401 Unauthorized` - Не авторизован
- `403 Forbidden` - Доступ запрещен
- `404 Not Found` - Ресурс не найден
- `409 Conflict` - Конфликт данных
- `422 Unprocessable Entity` - Ошибка валидации
- `429 Too Many Requests` - Превышен лимит запросов
- `500 Internal Server Error` - Ошибка сервера

### Rate Limiting
- **Логин**: 5 попыток за 5 минут
- **Регистрация**: 3 попытки за 5 минут
- **API запросы**: 100 запросов за минуту

## 🔍 Примеры использования

### Полный цикл работы с API

```bash
# 1. Регистрация пользователя
curl -X POST "http://localhost:8000/api/users/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'

# 2. Вход в систему
curl -X POST "http://localhost:8000/api/users/signin" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'

# 3. Получение баланса
curl -u "test@example.com:TestPass123" \
  "http://localhost:8000/api/users/balance"

# 4. Запрос рекомендаций
curl -X POST "http://localhost:8000/api/events/prediction/new?message=фантастика&top=5" \
  -u "test@example.com:TestPass123"

# 5. История предсказаний
curl -u "test@example.com:TestPass123" \
  "http://localhost:8000/api/events/prediction/history"

# 6. История транзакций
curl -u "test@example.com:TestPass123" \
  "http://localhost:8000/api/users/transaction/history"
```

### Создание администратора

```bash
curl -X POST "http://localhost:8000/api/users/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"AdminPass123","is_admin":true}'
```

## 📚 Дополнительные ресурсы

- [README.md](README.md) - Общее описание проекта
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архитектура системы
- [SECURITY_RECOMMENDATIONS.md](SECURITY_RECOMMENDATIONS.md) - Рекомендации по безопасности
- [Swagger UI](http://localhost:8000/docs) - Интерактивная документация API
- [ReDoc](http://localhost:8000/redoc) - Альтернативная документация API
