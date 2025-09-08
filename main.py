# pip install Flask

from flask import Flask, jsonify, request
from db_utils import ( #importing functions created in db_utils.py
    DbConnectionError,
    get_all_games, 
    insert_new_game, 
    get_all_loans,
    insert_new_loan,
    insert_new_customer, 
    get_available_games, 
    get_all_customers, 
    delete_customer_by_id, 
    get_single_customer_by_id
)

app = Flask(__name__)
@app.route('/')
def home(): 
    return "Welcome to the Video Gaming Hub Loan System!" # the home route displays a welcome message

@app.route('/games', methods=['GET'])
def api_get_all_games():
    try:
        games = get_all_games()
        return jsonify(games)
    except DbConnectionError as e:
        return jsonify({'error': str(e)}), 500 # 500 Internal Server Error

@app.route('/games', methods=['POST'])
def api_insert_new_game():
    try:
        game_data = request.json
        if not game_data:
            return jsonify({'error': 'Invalid or missing JSON data'}), 400 # 400 Bad Request

        required_fields = ['title', 'genre', 'platform', 'status'] # Game ID is auto-incremented, so it is not required in the request
        if not all(field in game_data for field in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
        
        insert_new_game(game_data)
        return jsonify({'message': 'Game inserted successfully!'}), 201 # 201 Created
    except DbConnectionError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/loans', methods=['GET'])
def api_get_all_loans():        
    try:
        loans = get_all_loans()
        return jsonify(loans)
    except DbConnectionError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/loans', methods=['POST'])
def api_insert_new_loan():
    try:
        loan_data = request.json
        if not loan_data:
            return jsonify({'error': 'Invalid or missing JSON data'}), 400

        required_fields = ['game_id', 'customer_id', 'date_of_loan', 'due_date'] # Loan ID is auto-incremented, so it is not required in the request
        if not all(field in loan_data for field in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400

        insert_new_loan(loan_data)
        return jsonify({'message': 'Loan inserted successfully!'}), 201
    except DbConnectionError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/available_games', methods=['GET'])
def api_get_available_games():
    try:
        available_games = get_available_games()
        return jsonify(available_games)
    except DbConnectionError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/customers', methods=['GET'])
def api_get_all_customers():    
    try:
        customers = get_all_customers()
        return jsonify(customers)
    except DbConnectionError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/customers', methods=['POST'])
def api_insert_new_customer():
    try:
        customer_data = request.json
        if not customer_data:
            return jsonify({'error': 'Invalid or missing JSON data'}), 400
        
        required_fields = ['name', 'email']
        if not all(field in customer_data for field in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
        
        insert_new_customer(customer_data)
        return jsonify({'message': 'Customer inserted successfully!'}), 201
    except DbConnectionError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def api_delete_customer(customer_id):   
    try:
        delete_customer_by_id(customer_id)
        return jsonify({"message": f"Customer {customer_id} deleted successfully"}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404  # 404 Not Found
    except DbConnectionError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/customers/<int:customer_id>', methods=['GET'])
def api_get_single_customer(customer_id):
    try:
        customer = get_single_customer_by_id(customer_id)
        return jsonify(customer)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except DbConnectionError as e:
        return jsonify({"error": str(e)}), 500

# other http methods not used here such as PUT (update existing record) and PATCH (partially update a record) could also be used (SOURCE = https://www.geeksforgeeks.org/python/flask-http-method/)


# I found info on the Flask error handler in the documentation here https://flask.palletsprojects.com/en/stable/errorhandling/
@app.errorhandler(DbConnectionError)
def handle_db_connection_error(error):  
    response = jsonify({"error": str(error)}) # Converts the error to a JSON response
    response.status_code = 500
    return response

@app.errorhandler(404) # Handle 404 Not Found errors 
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500) # Handle 500 Internal Server Error
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(400) # Handle 400 Bad Request errors
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Run the Flask app on port 5000

