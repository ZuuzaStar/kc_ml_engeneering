# 🚀 Быстрый старт тестов

## Установка зависимостей
```bash
pip install -r tests/requirements.txt
```

## Запуск тестов моделей (рекомендуется)
```bash
python -m pytest tests/test_simple.py tests/test_movie_recommendations.py tests/test_integration_scenarios.py -v
```

## Запуск всех тестов
```bash
python tests/run_tests.py
```

## Что тестируется ✅
- **Модели данных**: User, Wallet, Transaction, Movie, Prediction
- **ARRAY поля**: Жанры фильмов (эмулируются через JSON)
- **Vector поля**: Embeddings (эмулируются через JSON)
- **Связи моделей**: Пользователь → Кошелек → Транзакции
- **Бизнес-логика**: Создание, валидация, обновление данных

## Ожидаемые результаты
- **22 теста** пройдут успешно (модели и логика)
- **17 тестов** упадут с 404 (API эндпоинты - ожидаемо)

## Структура
```
tests/
├── conftest.py                    # Фикстуры и настройки
├── test_simple.py                 # Базовые тесты моделей
├── test_movie_recommendations.py  # Тесты ARRAY/Vector полей
└── test_integration_scenarios.py  # Интеграционные тесты
```

## Примечание
Тесты используют упрощенные модели для SQLite совместимости. ARRAY и Vector поля эмулируются через JSON строки.
