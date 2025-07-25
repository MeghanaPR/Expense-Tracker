import sqlite3

def view_database():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    # Viewing Users Table
    print("Users Table:")
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    for user in users:
        print(user)

    # Viewing Expenses Table
    print("\nExpenses Table:")
    cursor.execute('SELECT * FROM expenses')
    expenses = cursor.fetchall()
    for expense in expenses:
        print(expense)

    conn.close()

view_database()
