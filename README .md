# 🧠 AI SQL Data Analyst Agent

> Upload any CSV → ask questions in plain English → get SQL + answers + charts

Built with **Streamlit** · **LangChain** · **Groq (Llama 3)** · **SQLite** · **Plotly**

---

## 🚀 Quick Start

### 1. Clone / unzip the project

```bash
cd csv_sql_agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

```bash
cp .env.example .env
# then edit .env and paste your key:
# GROQ_API_KEY=gsk_...
```

Get a **free** Groq API key at → https://console.groq.com

### 5. Run the app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 📁 Project Structure

```
csv_sql_agent/
├── app.py            ← Streamlit UI (main entry point)
├── db_utils.py       ← CSV → SQLite loader + schema inspector
├── agent.py          ← LangChain SQL agent (Groq / Llama 3)
├── viz.py            ← Auto chart generation (Plotly)
├── requirements.txt
├── .env.example      ← API key template
└── sample_data.csv   ← Test dataset (sales orders)
```

---

## 🧩 Architecture

```
User (CSV + Question)
      ↓
db_utils.py  →  pandas reads CSV  →  SQLite in-memory DB
      ↓
agent.py     →  LangChain SQLAgent  →  Groq (Llama 3)
      ↓
SQL Query generated  →  executed on SQLite  →  result DataFrame
      ↓
app.py       →  Answer + SQL block + Plotly chart
```

---

## 💬 Example Questions

Once you load `sample_data.csv`, try:

| Question | What it does |
|----------|--------------|
| `How many orders per region?` | GROUP BY + COUNT |
| `What is the total revenue by category?` | GROUP BY + SUM |
| `Show me the top 5 products by revenue` | ORDER BY + LIMIT |
| `Which orders are still Processing?` | WHERE filter |
| `What is the average order value?` | AVG aggregate |
| `Show monthly revenue trend` | GROUP BY date |

---

## ⚙️ Configuration

| Setting | Where | Default |
|---------|-------|---------|
| Groq API key | Sidebar / `.env` | — |
| LLM model | Sidebar dropdown | `llama3-70b-8192` |
| Max rows in chart | `viz.py` line 60 | 200 |
| Agent max iterations | `agent.py` | 10 |

### Available models

| Model | Speed | Quality |
|-------|-------|---------|
| `llama3-70b-8192` | Fast | Best |
| `llama3-8b-8192` | Fastest | Good |
| `mixtral-8x7b-32768` | Fast | Good, longer context |

---

## 📊 Chart Auto-Selection Logic

`viz.py` picks the chart type based on the result shape:

| Result shape | Chart |
|---|---|
| 1 numeric column | Histogram |
| 1 categorical column | Value-count bar |
| 1 categorical + 1 numeric | Bar or Pie (≤8 categories) |
| 1 categorical + multiple numeric | Grouped bar |
| datetime + numeric | Line chart |
| 2 numeric columns | Scatter + trendline |
| 3+ numeric columns | Correlation heatmap |
| Anything else | Table fallback |

---

## 🛠 Troubleshooting

**`ModuleNotFoundError: langchain_groq`**
```bash
pip install langchain-groq
```

**`AuthenticationError` from Groq**
- Check your API key is correct in `.env` or the sidebar input.

**Agent returns wrong SQL**
- Try rephrasing the question to be more specific.
- Switch to `llama3-70b-8192` for best SQL quality.

**Chart not showing**
- The result may be a single value (no chart needed).
- The table fallback will show instead.

---

## 📝 License

MIT — use freely for learning, portfolio, or production.
