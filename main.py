from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from mcp_agent import query_mcp_agent
from rag_agent import query_agent
import urllib.parse
import os
import pymysql

# ✅ Load environment variables
load_dotenv()

# ✅ FastAPI app
app = FastAPI()

# ✅ Enable CORS for frontend (React dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MongoDB Client Connection
def get_mongo_client():
    uri = os.getenv(
        "MONGO_URI",
        "mongodb+srv://princek02032004:Snehal%401234@valuefy-cluster.spuzijz.mongodb.net/"
    )
    return MongoClient(uri)

# ✅ MySQL DB Setup
MYSQL_USER = "root"
MYSQL_PASSWORD = urllib.parse.quote("Snehal@123")
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB = "valuefy_transactions"

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

# ===================================================== #
# ===================== ROUTES ======================== #
# ===================================================== #

@app.get("/")
def read_root():
    return {"message": "🚀 Welcome to the Valuefy NLQ Agent API!"}


@app.get("/clients")
def get_clients():
    mongo_client = get_mongo_client()
    db = mongo_client["valuefy"]
    clients = list(db["clients"].find({}, {"_id": 0}))
    return {"clients": clients}


@app.get("/transactions")
def get_transactions():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM transactions"))
        transactions = [dict(row._mapping) for row in result]
    return {"transactions": transactions}


@app.get("/client-summary")
def client_summary():
    mongo_client = get_mongo_client()
    db = mongo_client["valuefy"]
    clients = list(db["clients"].find({}, {"_id": 0}))

    with engine.connect() as conn:
        result = conn.execute(text("SELECT client_name, amount_invested FROM transactions"))
        transactions = [dict(row._mapping) for row in result]

    # Map total investment per client
    investment_map = {}
    for txn in transactions:
        name = txn["client_name"]
        investment_map[name] = investment_map.get(name, 0) + txn["amount_invested"]

    # Add total investment to client profiles
    for client in clients:
        client["total_investment"] = investment_map.get(client["name"], 0)

    return {"clients": clients}


@app.post("/query")
async def ask_question(payload: dict):
    question = payload.get("question")
    if not question:
        return {"error": "❌ Question not provided."}

    try:
        answer = query_agent(question)
        return {"answer": answer}
    except Exception as e:
        print("❌ Error in query_agent:", e)
        return {"error": f"LangChain agent failed: {str(e)}"}


@app.post("/mcp-query")
async def mcp_query(payload: dict):
    question = payload.get("question")
    if not question:
        return {"error": "❌ Question not provided."}

    try:
        answer = query_mcp_agent(question)
        print("🧠 MCP Answer:", answer)  # Debug print
        if not answer:
            return {"answer": "MCP agent returned no output."}
        return {"answer": str(answer)}
    except Exception as e:
        print("❌ Error in query_mcp_agent:", e)
        return {"error": f"MCP agent failed: {str(e)}"}
