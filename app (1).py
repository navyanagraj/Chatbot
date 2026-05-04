import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from db_utils import load_csv_to_sqlite, get_table_info
from agent import build_agent, run_agent
from viz import auto_chart

load_dotenv()

st.set_page_config(page_title="AI SQL Analyst", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.stApp { background: #0f1117; }
div[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1e293b; }
.stButton > button { background: #3b82f6; color: white; border: none; border-radius: 8px; width: 100%; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

if "conn"         not in st.session_state: st.session_state.conn         = None
if "agent"        not in st.session_state: st.session_state.agent        = None
if "df_preview"   not in st.session_state: st.session_state.df_preview   = None
if "table_name"   not in st.session_state: st.session_state.table_name   = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "table_info"   not in st.session_state: st.session_state.table_info   = ""

with st.sidebar:
    st.markdown("### 🧠 AI SQL Analyst")
    st.markdown("---")
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...", value=os.getenv("GROQ_API_KEY", ""))
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    st.markdown("---")
    model_choice = st.selectbox("Model", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ])
    st.markdown("---")
    st.markdown("**Upload CSV**")
    uploaded_file = st.file_uploader("Drop a CSV file", type=["csv"], label_visibility="collapsed")
    if uploaded_file and api_key:
        if st.button("🚀 Load & Analyze", use_container_width=True):
            with st.spinner("Loading CSV into SQLite..."):
                conn, table_name, df = load_csv_to_sqlite(uploaded_file)
                agent = build_agent(conn, model_choice)
                table_info = get_table_info(conn, table_name)
                st.session_state.conn         = conn
                st.session_state.agent        = agent
                st.session_state.df_preview   = df
                st.session_state.table_name   = table_name
                st.session_state.table_info   = table_info
                st.session_state.chat_history = []
            st.success(f"✅ Loaded `{table_name}` — {len(df):,} rows")
    if st.session_state.table_info:
        st.markdown("---")
        st.markdown("**Schema**")
        st.code(st.session_state.table_info, language="sql")
    if st.session_state.conn is not None:
        st.markdown("---")
        st.markdown("**Example questions**")
        examples = ["How many rows are there?","Show me the top 5 rows","What are the column names?","Give me summary statistics","Which rows have the highest values?"]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state["pending_question"] = ex
    if st.session_state.chat_history:
        st.markdown("---")
        if st.button("🗑 Clear chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

st.markdown("## 🧠 AI SQL Data Analyst")
st.markdown("Upload a CSV → ask questions in plain English → get SQL + answers + charts")

if st.session_state.conn is None:
    st.info("👈 Upload a CSV file and enter your Groq API key in the sidebar to get started.")
    st.stop()

df = st.session_state.df_preview
with st.expander(f"📋 Data preview — `{st.session_state.table_name}` ({len(df):,} rows × {len(df.columns)} cols)", expanded=False):
    st.dataframe(df.head(20), use_container_width=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Columns", len(df.columns))
    c3.metric("Numeric cols", len(df.select_dtypes(include="number").columns))
    c4.metric("Null cells", int(df.isnull().sum().sum()))

st.markdown("---")

for item in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        st.write(item["answer"])
        col_sql, col_chart = st.columns([1, 1])
        with col_sql:
            if item.get("sql"):
                st.code(item["sql"], language="sql")
        with col_chart:
            if item.get("result_df") is not None and not item["result_df"].empty:
                fig = auto_chart(item["result_df"])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(item["result_df"], use_container_width=True)

pending = st.session_state.pop("pending_question", None)
user_input = st.chat_input("Ask anything about your data...")
question = pending or user_input

if question:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = run_agent(st.session_state.agent, st.session_state.conn, question)
        answer    = result.get("answer", "No answer returned.")
        sql       = result.get("sql", "")
        result_df = result.get("result_df")
        error     = result.get("error", "")
        if error:
            st.error(f"Error: {error}")
        else:
            st.write(answer)
            col_sql, col_chart = st.columns([1, 1])
            with col_sql:
                if sql:
                    st.code(sql, language="sql")
            with col_chart:
                if result_df is not None and not result_df.empty:
                    fig = auto_chart(result_df)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(result_df, use_container_width=True)
        st.session_state.chat_history.append({"question": question, "answer": answer, "sql": sql, "result_df": result_df})
