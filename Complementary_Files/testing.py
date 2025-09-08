# testing Video Gaming Hub API (found examples here https://flask.palletsprojects.com/en/stable/testing/)

import requests
BASE_URL = "http://localhost:5000"  # the base URL of the API

def test_home(): 
    response = requests.get(BASE_URL + '/') #tests the home endpoint
    assert response.status_code == 200 # hoping to get status code 200 (OK)
    assert response.text == "Welcome to the Video Gaming Hub Loan System!" # expecting to see this welcome text
    print ("Home endpoint is working correctly.") # prints confirmation message if the test passes
    

def test_get_all_games():
    response = requests.get(BASE_URL + '/games') #tests the games endpoint
    assert response.status_code == 200 
    games = response.json()
    assert isinstance(games, list)  # Check if the response is a list, isinstance() function info https://www.w3schools.com/python/ref_func_isinstance.asp
    assert len(games) > 0  # Check if there are games in the list
    print ("Get all games endpoint is working correctly.")


def test_get_all_customers():
    response = requests.get(BASE_URL + '/customers') #tests the customers endpoint
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)
    assert len(customers) > 0
    print ("Get all customers endpoint is working correctly.")
    
def test_get_all_loans():
    response = requests.get(BASE_URL + '/loans') #tests the loans endpoint
    assert response.status_code == 200
    loans = response.json()
    assert isinstance(loans, list)
    assert len(loans) > 0
    print ("Get all loans endpoint is working correctly.")
    
test_home() # runs the home endpoint test
test_get_all_games() 
test_get_all_customers() 
test_get_all_loans() 

# Add more tests for other endpoints as needed, such as checking for 201 code (created) for POST endpoints and 404 (not found) for DELETE endpoints

