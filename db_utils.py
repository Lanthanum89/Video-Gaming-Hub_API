
# pip install mysql-connector-python
import mysql.connector

class DbConnectionError(Exception):
    pass

def get_db_connection():
    from config import HOST, USER, PASSWORD, DATABASE  # Importing database configuration from config.py
    try:
        conn = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        return conn # Returns a connection object to the MySQL database
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Database connection failed: {err}")

def get_all_games():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # Using dictionary=True to fetch rows as dictionaries
        query = "SELECT * FROM Games"
        cursor.execute(query)
        games = cursor.fetchall() # fetchall() retrieves all or all remaining rows from the query (source: https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-fetchall.html)
        cursor.close()
        conn.close()
        return games 
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to fetch games: {err}")

def insert_new_game(game_data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO Games (title, genre, platform, status) VALUES (%s, %s, %s, %s)" # Game ID is auto-incremented, so it is not required in the request
        cursor.execute(query, (
            game_data["title"],
            game_data["genre"],
            game_data["platform"],
            game_data["status"]
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to insert game: {err}")

def get_all_loans():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Game_Loans")
        loans = cursor.fetchall()
        cursor.close()
        conn.close()
        return loans
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to fetch loans: {err}")

def insert_new_loan(loan_data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO Game_Loans (game_id, customer_id, date_of_loan, due_date) VALUES (%s, %s, %s, %s)" # didn't include returned date because it can be NULL, loan ID is auto-incremented so it is not required in the request
        cursor.execute(query, (
            loan_data["game_id"],
            loan_data["customer_id"],
            loan_data["date_of_loan"],
            loan_data["due_date"]
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to insert loan: {err}")

def get_all_customers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Customers")
        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        return customers
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to fetch customers: {err}")

def insert_new_customer(customer_data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO Customers (name, email) VALUES (%s, %s)" # Customer ID is auto-incremented, so it is not required in the request
        cursor.execute(query, (
            customer_data["name"],
            customer_data["email"]
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to insert customer: {err}")

def delete_customer_by_id(customer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Customers WHERE id = %s", (customer_id,))
        if cursor.rowcount == 0: # Check if any rows were affected
            raise ValueError("Customer not found") # If no rows were affected, it means the customer ID does not exist
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to delete customer: {err}")

def get_single_customer_by_id(customer_id):
    try:    
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        cursor.close()
        conn.close()
        if not customer:
            raise ValueError("Customer not found")
        return customer
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to fetch customer: {err}")

def get_available_games():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Games WHERE status = 'available' ORDER BY title")  # Fetching only available games, ordered by title
        available_games = cursor.fetchall()  
        cursor.close()
        conn.close()
        return available_games
    except mysql.connector.Error as err:
        raise DbConnectionError(f"Failed to fetch available games: {err}")

# could add functions to get loaned games, etc.