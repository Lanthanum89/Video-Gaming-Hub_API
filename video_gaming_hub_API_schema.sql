
CREATE DATABASE IF NOT EXISTS Video_Gaming_Hub_API; -- create the database if it does not exist

USE Video_Gaming_Hub_API; -- ensure we are using the correct database

CREATE TABLE Games ( -- Table to store game information
    Game_id INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(100) NOT NULL,
    Platform VARCHAR(50) NOT NULL,
    Genre VARCHAR(50),
    Status VARCHAR(20) NOT NULL DEFAULT 'Available' -- Status can be 'Available' or 'Borrowed' (a Boolean value could also be used. I tried this but it got too complex for my current knowledge (I hypothesised TRUE = available and FALSE = borrowed). I couldn't get it to sync with the loan table, but this would be ideal, especially if it could update with the loan table automatically)
);

CREATE TABLE Customers ( -- Table to store customer information
    Customer_id INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE Game_Loans ( -- Table to store game loan information
    Loan_id INT AUTO_INCREMENT PRIMARY KEY,
    Game_id INT NOT NULL,
    Customer_id INT NOT NULL,
    Date_of_Loan DATE NOT NULL,
    Due_Date DATE NOT NULL,
    Returned_Date DATE, -- NULL is allowed because the game might not be due to be returned yet, or is overdue
    FOREIGN KEY (Game_id) REFERENCES Games(Game_id),
    FOREIGN KEY (Customer_id) REFERENCES Customers(Customer_id)
);

INSERT INTO Games (Title, Platform, Genre, Status) VALUES
('The Legend of Pillars', 'Nintendo Switch', 'Action-Adventure', 'Available'),
('Garden Ring', 'PlayStation 5', 'Action RPG', 'Available'),
('The Simulations', 'PC', 'Simulation', 'Borrowed'),
('Galaxyfield', 'Xbox Series X', 'RPG', 'Borrowed'),
('Cybergoth 3077', 'PlayStation 5', 'Action RPG', 'Available'),
('Wizard School Legacy', 'PlayStation 5', 'Action RPG', 'Available'),
('Chess Madness', 'PC', 'Strategy', 'Borrowed');


INSERT INTO Customers (Name, Email) VALUES
('Laura Smith', 'lauras@domain.com'),
('Amelia Barker', 'ameliab@domain.com'),
('Freddie Creese', 'freddiec@domain.com'),
('Jack Pearce', 'jackp@domain.com');

-- Loan data for the games (linked via Game_id and Customer_id)

-- The Legend of Pillars (Game_id = 1) borrowed by Laura Smith (Customer_id = 1)
INSERT INTO Game_Loans (Game_id, Customer_id, Date_of_Loan, Due_Date) VALUES
(1, 1, CURDATE() - INTERVAL 5 DAY, CURDATE() + INTERVAL 9 DAY); -- borrowed 5 days ago and due in 9 days (current date MINUS 5 days ago, due to be returned current date + 9 days)
(4, 4, CURDATE() - INTERVAL 2 DAY, CURDATE() + INTERVAL 12 DAY); -- borrowed 2 days ago and due in 12 days (current date MINUS 2 days ago, due to be returned current date + 12 days)
(5, 1, CURDATE() - INTERVAL 10 DAY, CURDATE() + INTERVAL 4 DAY); -- borrowed 10 days ago and due in 4 days (current date MINUS 10 days ago, due to be returned current date + 4 days)
(3, 2, CURDATE() - INTERVAL 15 DAY, CURDATE() + INTERVAL 5 DAY); -- borrowed 15 days ago and due in 5 days (current date MINUS 15 days ago, due to be returned current date + 5 days)

-- there would need to be some implementation for overdue loans, such as a function to check if the due date has passed and update the status of the game accordingly.

-- to visualise the tables and make sure all the data is correctly populated:
SELECT * FROM Games;
SELECT * FROM Customers;
SELECT * FROM Game_Loans; 
