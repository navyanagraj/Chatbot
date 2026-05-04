import re
import sqlite3
import pandas as pd

DB_PATH = "/tmp/csv_sql_agent.db"

def _sanitize_name(name: str) -> str:
    name = re.sub(r"[^\w]", "_", name.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    if name and name[0].isdigit():
        name = "t_" + name
    return name or "data"

def load_csv_to_sqlite(file):
    df = pd.read_csv(file, low_memory=False)
    df.columns = [_sanitize_name(c) for c in df.columns]
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors="raise")
            continue
        except (ValueError, TypeError):
            pass
        if df[col].dtype == object:
            try:
                converted = pd.to_datetime(df[col], infer_datetime_format=True)
                df[col] = converted.dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
    raw_name = getattr(file, "name", "data")
    table_name = _sanitize_name(raw_name.replace(".csv", "").replace(".CSV", ""))
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    return conn, table_name, df

def get_table_info(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    lines = [f"TABLE: {table_name}", "-" * 40]
    for col in cols:
        cid, name, dtype, notnull, default, pk = col
        pk_marker = " [PK]" if pk else ""
        null_marker = " NOT NULL" if notnull else ""
        lines.append(f"  {name}  {dtype}{pk_marker}{null_marker}")
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    lines.append("-" * 40)
    lines.append(f"  {row_count:,} rows")
    return "\n".join(lines)

def execute_sql(conn, sql):
    return pd.read_sql_query(sql, conn)
