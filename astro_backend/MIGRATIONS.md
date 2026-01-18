# Database Migrations Guide

Этот проект использует **Alembic** для управления миграциями базы данных.

## Основные команды

### Создание новой миграции

После изменения моделей в `models.py`:

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Создать миграцию автоматически (autogenerate)
alembic revision --autogenerate -m "описание_изменений"
```

### Применение миграций

```bash
# Применить все неприменённые миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Откатить все миграции
alembic downgrade base
```

### Просмотр текущего состояния

```bash
# Показать текущую версию базы данных
alembic current

# Показать историю миграций
alembic history --verbose
```

## Важные моменты

1. **Всегда проверяйте сгенерированные миграции** перед применением
2. **Для существующих данных** добавляйте колонки в 3 шага:
   - Добавить колонку как nullable
   - Заполнить значения по умолчанию
   - Сделать колонку NOT NULL

3. **Виртуальное окружение** - все команды alembic выполняются в активированном venv

4. **База данных должна быть запущена**:
   ```bash
   docker-compose up -d
   ```

## Структура

- `alembic/` - директория с миграциями
- `alembic/versions/` - файлы миграций
- `alembic/env.py` - конфигурация Alembic
- `alembic.ini` - настройки Alembic

## Пример миграции

Файл: `alembic/versions/5ebcd687a977_add_gender_to_boyfriends.py`

```python
def upgrade() -> None:
    # Добавить колонку как nullable
    op.add_column('boyfriends', sa.Column('gender', ...))
    # Заполнить значения
    op.execute("UPDATE boyfriends SET gender = 'male' WHERE gender IS NULL")
    # Сделать NOT NULL
    op.alter_column('boyfriends', 'gender', nullable=False)
```

## Troubleshooting

### Ошибка подключения к БД
- Проверьте, что PostgreSQL запущен: `docker-compose ps`
- Проверьте настройки в `.env`

### sqlmodel не определен
- Добавьте `import sqlmodel` в начало файла миграции

### NOT NULL constraint failed
- Используйте трёхшаговый подход для добавления колонок (см. выше)
