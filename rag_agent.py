import torch
from langchain_community.llms import HuggingFacePipeline
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDataBaseTool
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.tools.sql_database.tool import InfoSQLDatabaseTool
from pymongo import MongoClient
from sqlalchemy import create_engine
from dotenv import load_dotenv
import urllib.parse
import os
from transformers import pipeline


hf_pipeline = pipeline(
    "text2text-generation",
    model="google/flan-t5-small",
    max_new_tokens=128
)
llm = HuggingFacePipeline(pipeline=hf_pipeline)


MYSQL_USER = "root"
MYSQL_PASSWORD = urllib.parse.quote("Snehal@123")
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB = "valuefy_transactions"

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)
db = SQLDatabase(engine)


mongo_client = MongoClient("mongodb+srv://princek02032004:Snehal%401234@valuefy-cluster.spuzijz.mongodb.net/")
mongo_db = mongo_client["valuefy"]
client_collection = mongo_db["clients"]


def mongo_query_tool(query: str) -> str:
    q = query.lower()
    
    if any(k in q for k in ["high risk", "low risk", "medium risk"]):
        risk = None
        if "high risk" in q:
            risk = "High"
        elif "low risk" in q:
            risk = "Low"
        elif "medium risk" in q:
            risk = "Medium"
        if risk:
            clients = client_collection.find({"risk_appetite": risk}, {"_id": 0, "name": 1, "investment_preferences": 1})
            return "\n".join([f"{c['name']}: {', '.join(c['investment_preferences'])}" for c in clients])
    
    elif "risk" in q or "at risk" in q or "at risks" in q:
        clients = client_collection.find({}, {"_id": 0, "name": 1, "risk_appetite": 1, "investment_preferences": 1})
        return "\n".join([f"{c['name']} (Risk: {c.get('risk_appetite', 'N/A')}): {', '.join(c.get('investment_preferences', []))}" for c in clients])
    elif any(k in q for k in ["clients", "profile", "name", "address", "rm", "relationship manager"]):
        clients = client_collection.find({}, {"_id": 0})
        return "\n".join([str(c) for c in clients])
    else:
        return "MongoDB tool only supports client profile queries (risk, name, preferences, address, RM)."

def top_rm_tool(_: str) -> str:
    query = """
    SELECT relationship_manager, SUM(amount_invested) AS total_investment
    FROM transactions
    GROUP BY relationship_manager
    ORDER BY total_investment DESC
    LIMIT 1
    """
    return db.run(query)


tools = [
    Tool(
        name="MongoDBClientProfiles",
        func=mongo_query_tool,
        description="Use this tool ONLY to answer questions about client profiles such as their name, address, risk appetite, investment preferences, or RM. The data is in MongoDB."
    ),
    QuerySQLDataBaseTool(db=db),
    Tool(
        name="TopRMInvestment",
        func=top_rm_tool,
        description="Use this to find the RM (relationship manager) with the highest total investment managed."
    )
]


agent_executor = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

def query_agent(question: str) -> str:
    q = question.lower()

    # 1. Top five portfolios of wealth members
    if "top five portfolios" in q or ("top 5" in q and "portfolio" in q):
        query = (
            "SELECT client_name, SUM(amount_invested) AS portfolio_value "
            "FROM transactions GROUP BY client_name ORDER BY portfolio_value DESC LIMIT 5;"
        )
        return db.run(query)

    # 2. Breakup of portfolio values per relationship manager
    if (
        ("breakup" in q or "portfolio" in q) and
        ("relationship manager" in q or "rm" in q)
    ):
        query = (
            "SELECT relationship_manager, SUM(amount_invested) AS total_portfolio_value "
            "FROM transactions GROUP BY relationship_manager;"
        )
        return db.run(query)

    # 3. Top relationship managers in the firm
    if "top relationship manager" in q or ("top" in q and "relationship manager" in q):
        query = (
            "SELECT relationship_manager, SUM(amount_invested) AS total_investment "
            "FROM transactions GROUP BY relationship_manager ORDER BY total_investment DESC LIMIT 5;"
        )
        return db.run(query)

    # 4. Clients who are the highest holders of a specific stock
    if "highest holder" in q or ("top" in q and "holder" in q and "stock" in q):
        # Try to extract the stock name
        import re
        match = re.search(r"holder[s]? of ([\w\s]+)", q)
        stock = match.group(1).strip() if match else None
        if stock:
            query = (
                f"SELECT client_name, SUM(amount_invested) AS total_investment "
                f"FROM transactions WHERE asset_name LIKE '%{stock}%' "
                f"GROUP BY client_name ORDER BY total_investment DESC LIMIT 5;"
            )
            return db.run(query)
        else:
            return "Please specify the stock name."

    # Portfolio/transaction-related queries
    elif any(k in q for k in ["portfolio", "asset", "stock", "equity", "crypto", "mutual fund", "breakup", "summary", "amount", "transaction", "value"]):
        return db.run(question)

    # Profile-related queries
    elif any(k in q for k in ["risk", "preference", "profile", "client detail", "name", "address", "rm", "relationship manager"]):
        return mongo_query_tool(question)

    # Top RM queries
    elif any(k in q for k in ["top relationship manager", "most investment", "rm with most investment", "top rm"]):
        return top_rm_tool(question)

    # Fallback to SQL for anything else
    else:
        return db.run(question)
