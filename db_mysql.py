import urllib.parse

from sqlalchemy import create_engine, text

MYSQL_USER = "root"
MYSQL_PASSWORD = urllib.parse.quote("Snehal@123")
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB = "valuefy_transactions"

def test_mysql_connection():
    try:
        engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM transactions LIMIT 5"))
            print("📊 Sample Transactions:")
            for row in result:
                print(row)
    except Exception as e:
        print("❌ MySQL connection failed:", e)

if __name__ == "__main__":
    test_mysql_connection()
