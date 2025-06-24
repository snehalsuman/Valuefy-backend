# Valuefy Backend

This repository contains the backend implementation for the Natural Language Cross-Platform Data Query Agent developed as part of the Valuefy internship assignment. The backend is responsible for processing user queries using LangChain, retrieving data from both MongoDB and MySQL, and returning structured results to the frontend.

## Technologies Used

- FastAPI – for building RESTful APIs
- MongoDB – for storing client profile information
- MySQL – for storing transaction data
- LangChain – for orchestrating multi-tool language model workflows
- OpenRouter – as the LLM provider interface
- SQLAlchemy, PyMySQL, PyMongo – for database operations

## Project Structure

- `main.py`: FastAPI app entry point
- `db/`
  - `mongo.py`: MongoDB connection logic
  - `mysql.py`: MySQL connection logic
- `db_mysql.py`: MySQL query functions
- `test_mongo.py`: MongoDB client testing
- `mcp_agent.py`: LangChain MCP agent for advanced tool use
- `rag_agent.py`: Standard LangChain RAG agent for query resolution
- `.env`: Stores environment variables (excluded from version control)
- `requirements.txt`: Lists all Python dependencies

## Environment Variables

Create a `.env` file with the following keys:

MONGO_URI=mongodb://localhost:27017/
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=valuefy
OPENROUTER_API_KEY=your_openrouter_key


## Installation and Setup

1. Clone the repository:

   git clone https://github.com/snehalsuman/Valuefy-backend.git  
   cd Valuefy-backend

2. Create a virtual environment and install dependencies:

   python3 -m venv env  
   source env/bin/activate  
   pip install -r requirements.txt

3. Start the development server:

   uvicorn main:app --reload

## API Endpoints

| Method | Endpoint        | Description                                  |
|--------|------------------|----------------------------------------------|
| GET    | /clients         | Returns a list of clients from MongoDB       |
| GET    | /transactions    | Returns a list of transactions from MySQL    |
| POST   | /query           | Accepts a natural language query and returns structured data using LangChain agents |

## Capabilities

- Understands natural language financial queries.
- Dynamically uses both MongoDB and MySQL through agent tools.
- Supports structured reasoning using LangChain MCP agents.

## Author

Developed by Snehal Suman for the Valuefy assignment.  
GitHub: https://github.com/snehalsuman
