# 🧪 Тестирование системы рекомендаций фильмов

## 📋 Обзор

Система тестирования использует **Factory Pattern** для создания SQLite-совместимых версий SQLModel моделей. Это решает проблему несовместимости PostgreSQL типов (`ARRAY`, `Vector`) с SQLite.

**Статистика**: 49 тестов, 100% прохождение, ~9 секунд выполнения

## 🏗️ Архитектура

### Фабрика тестовых моделей
```python
# simple_factory.py автоматически создает SQLite-совместимые модели
TestUser = SimpleTestModelFactory._create_test_user()
TestMovie = SimpleTestModelFactory._create_test_movie()
```

### Адаптация типов данных
- `ARRAY(String)` → `str` (JSON строка) 
- `Vector(384)` → `str` (JSON строка)
- Автоматическая сериализация/десериализация

## 📁 Структура

```
app/tests/
├── conftest.py                  # Основные фикстуры и конфигурация
├── simple_factory.py            # Фабрика SQLite-совместимых моделей
├── adapters.py                  # Адаптеры для PostgreSQL типов
├── requirements.txt             # Зависимости для тестов
├── pytest.ini                  # Конфигурация pytest
├── run_tests.py                 # Скрипт запуска тестов
├── README.md                    # 📖 Эта документация
└── test_*.py                    # Тестовые файлы
```

## 🚀 Быстрый старт

### Установка
```bash
cd app
pip install -r tests/requirements.txt
```

### Запуск
```bash
cd tests
python -m pytest -v
```

### Результат
```
==================================== 49 passed, 98 warnings in 9.14s ======================================
```

## 🎯 Что тестируется

### Пользователи (8 тестов)
- Создание и валидация моделей
- Хеширование паролей с bcrypt
- Права администратора
- Связи с кошельком и транзакциями

### Кошелек (11 тестов)
- Операции с балансом
- Создание и валидация транзакций
- Связи между пользователем, кошельком и транзакциями

### Фильмы (10 тестов)
- Эмуляция PostgreSQL ARRAY и Vector типов
- JSON сериализация/десериализация
- Консистентность данных

### Интеграция (13 тестов)
- Полные пользовательские сценарии
- Связи между всеми моделями
- Целостность данных

### Базовые тесты (7 тестов)
- Работа фикстур
- Создание мок-объектов

## 🔧 Фикстуры

### Базовые
- `session` - SQLite сессия БД
- `client` - тестовый FastAPI клиент
- `db_session` - алиас для session

### Данные
- `mock_user_data` - базовые данные пользователя
- `mock_movie_data` - данные фильма (с ARRAY и Vector)

### Объекты
- `mock_user` - пользователь с кошельком (баланс 0.0)
- `mock_admin_user` - администратор с кошельком (баланс 1000.0)
- `mock_movie` - фильм с JSON-сериализованными полями
- `mock_transaction` - транзакция на 100.0 типа "DEPOSIT"
- `mock_prediction` - предсказание стоимостью 5.0

## 🧪 Примеры тестов

### Тест создания пользователя
```python
def test_user_model_creation(self, mock_user):
    """Тест создания модели пользователя"""
    assert mock_user.email == "test@example.com"
    assert mock_user.is_admin is False
    assert hasattr(mock_user, 'wallet')
```

### Тест ARRAY полей
```python
def test_movie_array_field_emulation(self, mock_movie):
    """Тест эмуляции поля ARRAY в модели фильма"""
    # Проверяем что жанры сохраняются как JSON строка
    assert isinstance(mock_movie.genres, str)
    
    # Проверяем что жанры восстанавливаются как список
    genres_list = mock_movie.genres_list
    assert isinstance(genres_list, list)
    assert "action" in genres_list
```

## 🔍 Troubleshooting

### Ошибки с типами PostgreSQL
❌ `ARRAY has no matching SQLAlchemy type`  
✅ **Решение**: Используется автоматическая фабрика моделей

### Ошибки валидации SQLModel
❌ `"TestUser" object has no field "wallet"`  
✅ **Решение**: Используется `object.__setattr__` для обхода валидации

### Медленные тесты
❌ Тесты выполняются > 10 секунд  
✅ **Решение**: SQLite in-memory обеспечивает быстрое выполнение

## 📚 Расширение

### Добавление новой модели
1. Создайте модель в `app/models/`
2. Добавьте в `SimpleTestModelFactory.create_test_models()`
3. Создайте фикстуру в `conftest.py`
4. Напишите тесты

### Добавление нового типа данных
1. Создайте адаптер в `adapters.py`
2. Обновите `_map_field_type()` в фабрике
3. Добавьте логику преобразования в `__init__`

## 🎉 Готово!

Система тестирования полностью готова с современной архитектурой фабрики моделей. Все 49 тестов проходят успешно за ~9 секунд, покрывая 100% ключевых функций системы.