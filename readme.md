
# Video Gaming Hub API

A Flask-based RESTful API for managing a video game lending system. The API allows you to manage games, customers, and game loans, and is backed by a MySQL database.

## Features

- Add, view, and manage video games
- Register and manage customers
- Record and view game loans
- See available games for loan

## Project Structure

```text
main.py           # Flask API server
client.py         # Example client for API interaction
config.py         # Database credentials (not included, see below)
db_utils.py       # Database utility functions
video_gaming_hub_API_schema.sql  # MySQL schema
Complementary_Files/             # Assignment instructions, diagrams, screenshots
```

## Setup Instructions

### 1. Clone the Repository

```sh
git clone <repo-url>
cd Video-Gaming-Hub_API
```

### 2. Install Requirements

```sh
pip install Flask mysql-connector-python requests
```

### 3. Configure Database

- Create a MySQL database using the provided `video_gaming_hub_API_schema.sql` file:

	- Open MySQL and run:

		```sql
		SOURCE path/to/video_gaming_hub_API_schema.sql;
		```

- Create a `config.py` file in the project root with your DB credentials:

		```python
		HOST = "YOUR_HOST"
		USER = "YOUR_USER"
		PASSWORD = "YOUR_PASSWORD"
		DATABASE = "Video_Gaming_Hub_API"
		```

### 4. Run the API Server

```sh
python main.py
```

- The API will be available at `http://localhost:5000/`

### 5. (Optional) Run the Example Client

```sh
python client.py
```

## API Endpoints

### Home

- `GET /` — Welcome message

### Games

- `GET /games` — List all games
- `POST /games` — Add a new game
	- JSON body: `{ "title": str, "genre": str, "platform": str, "status": str }`
- `GET /available_games` — List all available games

### Customers

- `GET /customers` — List all customers
- `POST /customers` — Add a new customer
	- JSON body: `{ "name": str, "email": str }`
- `GET /customers/<customer_id>` — Get a single customer
- `DELETE /customers/<customer_id>` — Delete a customer

### Loans

- `GET /loans` — List all loans
- `POST /loans` — Add a new loan
	- JSON body: `{ "game_id": int, "customer_id": int, "date_of_loan": "YYYY-MM-DD", "due_date": "YYYY-MM-DD" }`

## Database Schema

See `video_gaming_hub_API_schema.sql` for full details. Main tables:

- **Games**: Game_id, Title, Platform, Genre, Status
- **Customers**: Customer_id, Name, Email
- **Game_Loans**: Loan_id, Game_id, Customer_id, Date_of_Loan, Due_Date, Returned_Date

## Error Handling

- Returns JSON error messages with appropriate HTTP status codes (400, 404, 500)

## Notes

- Do **not** commit your real `config.py` with credentials to public repositories.
- For assignment details, see `Complementary_Files/assignment instructions.md`.

## License

This project is for educational purposes.
