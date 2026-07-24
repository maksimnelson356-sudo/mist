# MIST — Стандарты разработки

## Архитектура

- **Clean Architecture**: database → services → handlers → ui
- **Event Bus**: ChronicleEvent для всех событий
- **ServiceContainer**: единая точка входа для сервисов

## Код

- Python 3.12+
- Async/await для всех DB-операций
- SQLAlchemy 2.0 async
- aiogram 3.12

## Тесты

- pytest
- Каждый новый сервис → тесты
- MockChronicle для тестирования событий

## Git

- Коммиты: `MIST-XXX: description`
- Ветки: `feature/MIST-XXX`, `fix/MIST-XXX`

## Документация

- ARCHITECTURE.md — архитектура
- GAME_RULES.md — игровые правила
- CHANGELOG.md — история версий

## Контрибьюция

1. Создай ветку `feature/MIST-XXX`
2. Реализуй функционал
3. Добавь тесты
4. Запусти `python -m pytest tests/`
5. Обнови CHANGELOG.md
6. Создай PR
