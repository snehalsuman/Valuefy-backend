import pymysql

def get_mysql_connection():
    conn = pymysql.connect(
        host='localhost',     # Use 127.0.0.1 if needed
        user='root',          # Change if needed
        password='Snehal@123',  # Set your MySQL root password here
        database='valuefy'    # DB name
    )
    return conn
