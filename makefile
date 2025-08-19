run_app:
    uvicorn main:app

run_venv:
    .\venv\Scripts\Activate.ps1

migrate_upgrade:
    alembic upgrade head

migrate_downgrade:
    alembic downgrade -1

migrate_current:
    alembic current

migrate_history:
    alembic history --verbose

migrate_stamp:
    alembic stamp $(REVISION)

migrate_revision:
    alembic revision --autogenerate -m "$(MESSAGE)"

migrate_reset:
    alembic downgrade base && alembic upgrade head