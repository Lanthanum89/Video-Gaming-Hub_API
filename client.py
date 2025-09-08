# pip install requests
import requests

BASE_URL = "http://localhost:5000"  # the base URL of the API

def get_all_games():
    print("Fetching all games from the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/games"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP errors
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching games: {e}")
        return {"error": "Failed to retrieve games"}, 500 # Internal Server Error

def insert_new_game(game_data):
    print("Inserting a new game into the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/games"
    try:
        response = requests.post(url, json=game_data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error inserting game: {e}")
        return {"error": "Failed to insert game"}, 500
    
def get_all_loans():
    print("Fetching all loans from the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/loans"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching loans: {e}")
        return {"error": "Failed to retrieve loans"}, 500

def insert_new_loan(loan_data):
    print("Inserting a new loan into the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/loans"
    try:
        response = requests.post(url, json=loan_data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error inserting loan: {e}")
        return {"error": "Failed to insert loan"}, 500
    
def get_all_customers():
    print("Fetching all customers from the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/customers"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching customers: {e}")
        return {"error": "Failed to retrieve customers"}, 500

def insert_new_customer(customer_data):
    print("Inserting a new customer into the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/customers"
    try:
        response = requests.post(url, json=customer_data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error inserting customer: {e}")
        return {"error": "Failed to insert customer"}, 500

def delete_customer_by_id(customer_id):
    print(f"Deleting customer with ID {customer_id} from the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/customers/{customer_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return {"message": f"Customer {customer_id} deleted successfully"}
    except requests.RequestException as e:
        print(f"Error deleting customer: {e}")
        return {"error": "Failed to delete customer"}, 500

    
def get_available_games():
    print("Fetching available games from the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/available_games"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching available games: {e}")
        return {"error": "Failed to retrieve available games"}, 500

    
def get_single_customer_by_id(customer_id):
    print(f"Fetching customer with ID {customer_id} from the Video Gaming Hub Loan System...")
    url = f"{BASE_URL}/customers/{customer_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching customer: {e}")
        return {"error": "Failed to retrieve customer"}, 500
    
def run():
    get_all_customers()
    get_all_games()
    get_all_loans()
    insert_new_game({"title": "New Game", "genre": "Action", "platform": "PC", "status": "Available"})
    insert_new_customer({"name": "Richard Smith", "email": "richard.sm@domain.com"})
    insert_new_loan({"game_id": 1, "customer_id": 1, "date_of_loan": "2025-06-27", "due_date": "2025-07-15"})
    get_available_games()
    get_single_customer_by_id(1)
    
if __name__ == "__main__":
    run()  # Call the run function to execute the script

