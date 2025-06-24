from langchain_core.runnables import RunnableLambda
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.tools.sql_database.tool import QuerySQLDataBaseTool
from pymongo import MongoClient
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os, urllib.parse

# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_BASE_URL
)

# ✅ MySQL setup
MYSQL_USER = "root"
MYSQL_PASSWORD = urllib.parse.quote("Snehal@123")
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB = "valuefy_transactions"

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)
db = SQLDatabase(engine)

# ✅ MongoDB setup
mongo_client = MongoClient("mongodb+srv://princek02032004:Snehal%401234@valuefy-cluster.spuzijz.mongodb.net/")
client_collection = mongo_client["valuefy"]["clients"]

# ✅ Tool functions
def mongo_query_tool(input: str) -> str:
    if "high risk" in input.lower():
        clients = client_collection.find({"risk_appetite": "High"}, {"_id": 0, "name": 1, "investment_preferences": 1})
        return "\n".join([f"{c['name']}: {', '.join(c['investment_preferences'])}" for c in clients])
    elif "clients" in input.lower():
        clients = client_collection.find({}, {"_id": 0})
        return "\n".join([str(c) for c in clients])
    else:
        return "MongoDB tool only supports simple client profile queries (risk, name, preferences)."

def top_rm_tool(_: str) -> str:
    query = """
    SELECT relationship_manager, SUM(amount_invested) AS total_investment
    FROM transactions
    GROUP BY relationship_manager
    ORDER BY total_investment DESC
    LIMIT 1
    """
    return db.run(query)

# ✅ Runnable wrappers
sql_tool = RunnableLambda(lambda q: QuerySQLDataBaseTool(db=db).run(q))
mongo_tool = RunnableLambda(mongo_query_tool)
rm_tool = RunnableLambda(top_rm_tool)

# ✅ Final main function — Simple router
def query_mcp_agent(question: str) -> str:
    input_data = {"question": question}
    q = question.lower()

    if "risk" in q or "preference" in q or "profile" in q:
        return mongo_tool.invoke(question)
    elif "top relationship manager" in q or "most investment" in q:
        return rm_tool.invoke(question)
    else:
        return sql_tool.invoke(question)
