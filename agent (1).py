import re
import traceback
import pandas as pd
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from db_utils import DB_PATH

_SQL_RE = re.compile(r"```(?:sql)?\s*(SELECT[\s\S]+?)```", re.IGNORECASE)

def _extract_sql(text):
    m = _SQL_RE.search(text)
    if m:
        return m.group(1).strip()
    lower = text.lower()
    idx = lower.find("select")
    if idx != -1:
        candidate = text[idx:]
        end = candidate.find("\n\n")
        return candidate[:end].strip() if end != -1 else candidate.strip()
    return ""

def _extract_sql_from_steps(steps):
    if not steps:
        return ""
    for action, observation in steps:
        tool_input = getattr(action, "tool_input", "") or ""
        if isinstance(tool_input, dict):
            tool_input = tool_input.get("query", "")
        if "select" in tool_input.lower():
            return tool_input.strip()
    return ""

def build_agent(conn, model="llama-3.3-70b-versatile"):
    llm = ChatGroq(model=model, temperature=0, max_tokens=2048)
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        agent_type="zero-shot-react-description",
        handle_parsing_errors=True,
        return_intermediate_steps=True,
        max_iterations=10,
        early_stopping_method="generate",
    )
    return agent

def run_agent(agent, conn, question):
    try:
        response = agent.invoke({"input": question})
    except Exception as exc:
        return {"answer": f"Agent error: {exc}", "sql": "", "result_df": None, "error": traceback.format_exc()}
    answer = response.get("output") or response.get("answer") or str(response)
    steps = response.get("intermediate_steps", [])
    sql = _extract_sql_from_steps(steps)
    if not sql:
        sql = _extract_sql(answer)
    result_df = None
    if sql:
        try:
            result_df = pd.read_sql_query(sql, conn)
        except Exception:
            result_df = None
    return {"answer": answer, "sql": sql, "result_df": result_df, "error": ""}
