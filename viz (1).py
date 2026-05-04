"""
viz.py
Auto-select and generate a Plotly chart from a result DataFrame.
Heuristics:
  - 1 numeric col                 → histogram
  - 1 categorical + 1 numeric     → bar chart
  - 2 numeric cols                → scatter
  - 1 categorical + 2+ numeric    → grouped bar
  - datetime + numeric            → line chart
  - 1 categorical, counts ≤ 8     → pie chart (use for aggregates)
  - otherwise                     → None (caller shows a table)
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

_DARK = "#0f1117"
_GRID = "#1e293b"
_TEXT = "#94a3b8"

_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=_DARK,
        plot_bgcolor=_DARK,
        font=dict(color=_TEXT, family="sans-serif", size=12),
        xaxis=dict(gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID),
        yaxis=dict(gridcolor=_GRID, linecolor=_GRID, zerolinecolor=_GRID),
        colorway=[
            "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
            "#8b5cf6", "#06b6d4", "#f97316", "#14b8a6",
        ],
        margin=dict(l=40, r=20, t=40, b=40),
    )
)


def _is_datetime_col(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if series.dtype == object:
        try:
            pd.to_datetime(series.head(5), infer_datetime_format=True)
            return True
        except Exception:
            return False
    return False


def auto_chart(df: pd.DataFrame):
    """
    Return a Plotly figure or None if no suitable chart can be inferred.
    """
    if df is None or df.empty or len(df.columns) == 0:
        return None

    # Limit rows to avoid enormous charts
    df = df.head(200)

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()
    dt_cols  = [c for c in cat_cols if _is_datetime_col(df[c])]

    n_num = len(num_cols)
    n_cat = len(cat_cols)
    n_dt  = len(dt_cols)
    n_total = len(df.columns)

    fig = None

    # ── Single numeric column → histogram ────────────────────────────────────
    if n_total == 1 and n_num == 1:
        fig = px.histogram(df, x=num_cols[0], title=f"Distribution of {num_cols[0]}")

    # ── Single categorical column → value counts bar ──────────────────────────
    elif n_total == 1 and n_cat == 1:
        vc = df[cat_cols[0]].value_counts().reset_index()
        vc.columns = [cat_cols[0], "count"]
        fig = px.bar(vc, x=cat_cols[0], y="count", title=f"Counts by {cat_cols[0]}")

    # ── Datetime + numeric → line chart ──────────────────────────────────────
    elif n_dt >= 1 and n_num >= 1:
        dt_col = dt_cols[0]
        y_col  = num_cols[0]
        df_s   = df.sort_values(dt_col)
        fig = px.line(df_s, x=dt_col, y=y_col, title=f"{y_col} over time")

    # ── 1 categorical + 1 numeric → bar chart ────────────────────────────────
    elif n_cat == 1 and n_num == 1:
        x, y = cat_cols[0], num_cols[0]
        # Pie if few categories and looks like a proportion/count
        if df[x].nunique() <= 8 and df[y].min() >= 0:
            fig = px.pie(df, names=x, values=y, title=f"{y} by {x}")
        else:
            df_s = df.sort_values(y, ascending=False)
            fig  = px.bar(df_s, x=x, y=y, title=f"{y} by {x}")

    # ── 1 categorical + multiple numeric → grouped bar ───────────────────────
    elif n_cat == 1 and n_num > 1:
        x = cat_cols[0]
        df_m = df.melt(id_vars=[x], value_vars=num_cols,
                       var_name="metric", value_name="value")
        fig = px.bar(df_m, x=x, y="value", color="metric",
                     barmode="group", title=f"Metrics by {x}")

    # ── 2 numeric columns → scatter ──────────────────────────────────────────
    elif n_num == 2 and n_cat == 0:
        x, y = num_cols[0], num_cols[1]
        fig = px.scatter(df, x=x, y=y, title=f"{y} vs {x}",
                         trendline="ols" if len(df) > 5 else None)

    # ── 2 numeric + 1 categorical → colored scatter ───────────────────────────
    elif n_num == 2 and n_cat == 1:
        x, y, c = num_cols[0], num_cols[1], cat_cols[0]
        fig = px.scatter(df, x=x, y=y, color=c, title=f"{y} vs {x} by {c}")

    # ── Many numerics, no categoricals → correlation heatmap ─────────────────
    elif n_num >= 3 and n_cat == 0:
        corr = df[num_cols].corr()
        fig = px.imshow(
            corr, text_auto=".2f", aspect="auto",
            title="Correlation matrix",
            color_continuous_scale="RdBu_r",
        )

    if fig is None:
        return None

    # Apply dark theme
    fig.update_layout(template=_TEMPLATE)
    return fig
