import psycopg2
from sqlalchemy.engine.url import make_url
from config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_sync_database():
    url = make_url(DATABASE_URL)
    
    conn_params = {
        "host": url.host,
        "port": url.port,
        "user": url.username,
        "password": url.password,
        "database": "postgres"
    }
    
    conn = None
    try:
        # Подключаемся к базе данных postgres для проверки существования целевой БД
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True  # Включаем autocommit для создания БД
        
        cursor = conn.cursor()
        
        # Проверяем существование базы данных
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (url.database,)
        )
        
        db_exists = cursor.fetchone()
        
        if not db_exists:
            cursor.execute(
                f"CREATE DATABASE {url.database} ENCODING 'UTF8'"
            )
            print(f"БД {url.database} создана")
        else:
            print(f"БД {url.database} уже существует")
            
        cursor.close()
            
    except psycopg2.Error as e:
        print(f"Ошибка PostgreSQL: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_sync_database()