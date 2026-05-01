from app.models import Base
from app.database import engine

from app.config import settings

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    from alembic import context
    from sqlalchemy import create_engine

    url = settings.database_url.replace("+asyncpg", "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    import asyncio
    from alembic import context
    from sqlalchemy.ext.asyncio import AsyncEngine

    connectable = engine

    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(_do_run_migrations)

        await connectable.dispose()

    def _do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(run_async_migrations())


from alembic import context

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
