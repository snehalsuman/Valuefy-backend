from langchain_core.runnables import RunnableLambda
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

from pymongo import MongoClient
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_BASE_URL,
    default_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
)


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
    if "high risk" in input_lower:
        clients = client_collection.find({"risk_appetite": "High"}, {"_id": 0, "name": 1, "investment_preferences": 1})
        return "\n".join([f"{c['name']}: {', '.join(c['investment_preferences'])}" for c in clients])
    elif "clients" in input_lower:
        clients = client_collection.find({}, {"_id": 0})
        return "\n".join([str(c) for c in clients])
    else:
        return "MongoDB tool only supports simple client profile queries (risk, name, preferences)."

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

    if any(k in q for k in ["risk", "preference", "profile", "client detail"]):
        return mongo_tool.invoke(question)

    elif any(k in q for k in ["top relationship manager", "most investment", "rm with most investment"]):
        return rm_tool.invoke(question)

    elif any(k in q for k in ["top client", "client invested most", "most invested client"]):
        return top_client.invoke(question)

    else:
        return sql_tool.invoke(question)
