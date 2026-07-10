# Database and Migration Rules

## Rules

- Create Alembic migrations for schema changes.
- Register every new SQLAlchemy model in `app/db/models/__init__.py`.
- Run `alembic upgrade head` before generating a new migration.
- Do not edit old migrations unless explicitly asked.
- Prefer explicit constraints for enum-like strings.
- Preserve cascade behavior for user-owned data.

## Common commands

```powershell
alembic upgrade head
alembic revision --autogenerate -m "message"
alembic upgrade head
pytest -q