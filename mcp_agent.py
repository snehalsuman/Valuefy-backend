import torch
from langchain_core.runnables import RunnableLambda
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline

from pymongo import MongoClient
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import urllib.parse


hf_pipeline = pipeline(
    "text-generation",
    model="sshleifer/tiny-gpt2", 
    max_new_tokens=64
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


toolkit = SQLDatabaseToolkit(db=db, llm=llm)
sql_agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True)
sql_tool = RunnableLambda(lambda q: sql_agent_executor.invoke({"input": q})["output"])

mongo_client = MongoClient("mongodb+srv://princek02032004:Snehal%401234@valuefy-cluster.spuzijz.mongodb.net/")
client_collection = mongo_client["valuefy"]["clients"]


def mongo_query_tool(input: str) -> str:
    input_lower = input.lower()
    # More flexible profile queries
    if any(k in input_lower for k in ["high risk", "low risk", "medium risk"]):
        risk = None
        if "high risk" in input_lower:
            risk = "High"
        elif "low risk" in input_lower:
            risk = "Low"
        elif "medium risk" in input_lower:
            risk = "Medium"
        if risk:
            clients = client_collection.find({"risk_appetite": risk}, {"_id": 0, "name": 1, "investment_preferences": 1})
            return "\n".join([f"{c['name']}: {', '.join(c['investment_preferences'])}" for c in clients])
    elif any(k in input_lower for k in ["clients", "profile", "name", "address", "rm", "relationship manager"]):
        clients = client_collection.find({}, {"_id": 0})
        return "\n".join([str(c) for c in clients])
    else:
        return "MongoDB tool only supports client profile queries (risk, name, preferences, address, RM)."

mongo_tool = RunnableLambda(mongo_query_tool)


def top_rm_tool(_: str) -> str:
    query = """
    SELECT relationship_manager, SUM(amount_invested) AS total_investment
    FROM transactions
    GROUP BY relationship_manager
    ORDER BY total_investment DESC
    LIMIT 1
    """
    return db.run(query)

rm_tool = RunnableLambda(top_rm_tool)

def top_client_tool(_: str) -> str:
    query = """
    SELECT client_name, SUM(amount_invested) AS total_investment
    FROM transactions
    GROUP BY client_name
    ORDER BY total_investment DESC
    LIMIT 1
    """
    return db.run(query)

top_client = RunnableLambda(top_client_tool)


def query_mcp_agent(question: str) -> str:
    q = question.lower()

    # Profile-related queries
    if any(k in q for k in ["risk", "preference", "profile", "client detail", "name", "address", "rm", "relationship manager"]):
        return mongo_tool.invoke(question)

    # Top RM queries
    elif any(k in q for k in ["top relationship manager", "most investment", "rm with most investment", "top rm"]):
        return rm_tool.invoke(question)

    # Top client queries
    elif any(k in q for k in ["top client", "client invested most", "most invested client", "highest holder", "top holders"]):
        return top_client.invoke(question)

    # Asset/portfolio queries
    elif any(k in q for k in ["portfolio", "asset", "stock", "equity", "crypto", "mutual fund", "breakup", "summary"]):
        return sql_tool.invoke(question)

    # Fallback to SQL for anything else
    else:
        return sql_tool.invoke(question)
