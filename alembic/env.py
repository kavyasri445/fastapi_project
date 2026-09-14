from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

# Database Base
from app.database.connection import Base

# Import ALL models so Alembic can detect their tables
from app.models.user import User
from app.models.form import Form
from app.models.form_version import FormVersion
from app.models.field import Field
from app.models.field_option import FieldOption
from app.models.conditional_rule import ConditionalRule
from app.models.submission import Submission
from app.models.response_value import ResponseValue
from app.models.public_link import PublicLink
from app.models.uploaded_file import UploadedFile


# =========================================================
# Alembic Config
# =========================================================

config = context.config


# =========================================================
# Load .env
# =========================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set in .env")

config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL
)


# =========================================================
# Logging
# =========================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# =========================================================
# Metadata
# =========================================================

target_metadata = Base.metadata


# =========================================================
# Offline Migration
# =========================================================

def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# Online Migration
# =========================================================

def run_migrations_online() -> None:
    """
    Run migrations in online mode.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# =========================================================
# Run Migration
# =========================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()