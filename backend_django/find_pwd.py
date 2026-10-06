import pymysql

passwords = [
    'root', 'admin', 'password', '1234', '123456', 
    '12345678', 'root123', 'Root@123', 'root1234', 
    'admin123', 'Admin@123', 'mysql', 'Admin@1234'
]

found = False
for pwd in passwords:
    try:
        conn = pymysql.connect(host='127.0.0.1', user='root', password=pwd)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS credit_card_db;")
        conn.close()
        print("\n" + "=" * 45)
        print(f">>> SUCCESS! Your MySQL password is: '{pwd}'")
        print(">>> Database 'credit_card_db' created successfully!")
        print("=" * 45 + "\n")
        found = True
        break
    except pymysql.err.OperationalError:
        continue

if not found:
    print("\nNone of the common passwords matched.")
    print("If you recall a personal password, add it to the 'passwords' list in find_pwd.py and run again.")