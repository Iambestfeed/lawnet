from logging.config import fileConfig
from alembic import context
import os
import sys
from dotenv import load_dotenv

# Thêm đường dẫn gốc của project vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.models.base import Base
except ImportError:
    sys.path.append(os.getcwd())  # Thử thêm cả thư mục hiện tại
    from core.models.base import Base

load_dotenv()

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = config.attributes.get('connection', None)
    
    if connectable is None:
        from sqlalchemy import create_engine
        connectable = create_engine(os.environ.get('DATABASE_URL'))

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

if __name__ == '__main__':
    run_migrations_online()