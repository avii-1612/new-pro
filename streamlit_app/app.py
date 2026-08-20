import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="E-Commerce Sales & Customer Analytics", layout="wide", page_icon="📊")

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_FILE = DATA_DIR / "ecommerce_cleaned.csv"
DEFAULT_CUSTOMERS_FILE = DATA_DIR / "customer_segments.csv"


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    h1 {font-weight: 800; letter-spacing: -0.5px;}
    h3 {font-weight: 700; margin-top: 0.5rem;}
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #eef0f2;
        border-radius: 12px;
        padding: 1rem 1.1rem 0.8rem 1.1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricLabel"] {font-size: 0.85rem; color: #6b7280;}
    div[data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 700;}
    .subtitle {color: #6b7280; font-size: 1rem; margin-top: -0.6rem; margin-bottom: 1.2rem;}
    section[data-testid="stSidebar"] {border-right: 1px solid #eef0f2;}
    hr {margin: 1.6rem 0;}
</style>
""", unsafe_allow_html=True)


def fmt_inr(x: float) -> str:
    """Format like the original dashboard: ₹23.15 Cr / ₹4.5 L / ₹12,907."""
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1_00_00_000:
        return f"₹{sign}{x/1_00_00_000:,.2f} Cr"
    if x >= 1_00_000:
        return f"₹{sign}{x/1_00_000:,.2f} L"
    return f"₹{sign}{x:,.0f}"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_default_data():
    df = pd.read_csv(DEFAULT_FILE, parse_dates=["Order_Date"])
    try:
        customers = pd.read_csv(DEFAULT_CUSTOMERS_FILE, parse_dates=["Last_Order_Date"])
    except Exception:
        customers = None
    return df, customers


def try_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str).head(20)
            if len(sample) == 0:
                continue
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
    return df


def find_col(candidates, cols, contains_ok=True):
    """Find the best matching column name from a list of preferred exact names,
    falling back to a substring match, case-insensitively."""
    cols_lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    if contains_ok:
        for cand in candidates:
            for c in cols:
                if cand.lower() in c.lower():
                    return c
    return None


st.sidebar.header("📁 Data")
uploaded_files = st.sidebar.file_uploader(
    "Upload your own sales file(s)", type=["csv", "xlsx", "xls"], accept_multiple_files=True
)

customers = None
source_label = "default dataset"

def read_any(f):
    if f.name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(f)
    return pd.read_csv(f)

if uploaded_files:
    if len(uploaded_files) == 1:
        try:
            df = read_any(uploaded_files[0])
            df = try_parse_dates(df)
            source_label = uploaded_files[0].name
            st.sidebar.success(f"Loaded {len(df):,} rows from **{uploaded_files[0].name}**.")
        except Exception as e:
            st.sidebar.error(f"Couldn't read that file ({e}). Showing default data instead.")
            df, customers = load_default_data()
    else:
        mode = st.sidebar.radio(
            "Multiple files uploaded — how do you want to view them?",
            ["Explore one at a time", "Combine into one dashboard"],
        )

        if mode == "Explore one at a time":
            names = [f.name for f in uploaded_files]
            picked_name = st.sidebar.selectbox("Which file do you want to explore?", names)
            chosen = next(f for f in uploaded_files if f.name == picked_name)
            try:
                df = read_any(chosen)
                df = try_parse_dates(df)
                source_label = chosen.name
                st.sidebar.success(f"Loaded {len(df):,} rows from **{chosen.name}**.")
            except Exception as e:
                st.sidebar.error(f"Couldn't read that file ({e}). Showing default data instead.")
                df, customers = load_default_data()
        else:
            frames = []
            failed = []
            for f in uploaded_files:
                try:
                    fdf_tmp = read_any(f)
                    fdf_tmp["Source_File"] = f.name
                    frames.append(fdf_tmp)
                except Exception:
                    failed.append(f.name)
            if frames:
                df = pd.concat(frames, ignore_index=True, sort=False)
                df = try_parse_dates(df)
                source_label = f"{len(frames)} combined file(s)"
                st.sidebar.success(f"Combined {len(frames)} file(s) into {len(df):,} total rows.")
                if failed:
                    st.sidebar.warning(f"Couldn't read: {', '.join(failed)}")
            else:
                st.sidebar.error("None of the uploaded files could be read. Showing default data instead.")
                df, customers = load_default_data()
else:
    df, customers = load_default_data()

if df.empty:
    st.error("This file has no rows to show.")
    st.stop()

# ---------------------------------------------------------------------------
# Auto-map uploaded columns onto the dashboard's expected fields
# ---------------------------------------------------------------------------
date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
categorical_cols = [c for c in df.columns if c not in date_cols and c not in numeric_cols]

date_col = find_col(["Order_Date", "Date", "Order Date"], date_cols) or (date_cols[0] if date_cols else None)
sales_col = find_col(["Sales", "Revenue", "Amount", "Total"], numeric_cols)
profit_col = find_col(["Profit"], [c for c in numeric_cols if "margin" not in c.lower()])
margin_col = find_col(["Profit_Margin", "Margin"], numeric_cols)
discount_col = find_col(["Discount"], numeric_cols)
region_col = find_col(["Region", "State"], categorical_cols)
category_col = find_col(["Category"], categorical_cols)
customer_type_col = find_col(["Customer_Type", "Segment"], categorical_cols)
order_id_col = find_col(["Order_ID", "Order Id", "OrderID"], df.columns.tolist())
customer_id_col = find_col(["Customer_ID", "Customer Id", "CustomerID"], df.columns.tolist())

if sales_col is None and numeric_cols:
    sales_col = numeric_cols[0]

missing_core = [name for name, val in [("a sales/revenue column", sales_col)] if val is None]
if missing_core:
    st.warning(f"Couldn't find {', '.join(missing_core)} in this file, so some sections below may be skipped.")

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
fdf = df.copy()

if date_col:
    valid_dates = fdf[date_col].dropna()
    if not valid_dates.empty:
        min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
        date_range = st.sidebar.date_input(
            "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = fdf[date_col].dt.date.between(start_date, end_date) | fdf[date_col].isna()
            fdf = fdf[mask]

if region_col:
    options = sorted(fdf[region_col].dropna().unique().tolist())
    selected = st.sidebar.multiselect("Region", options, default=options)
    fdf = fdf[fdf[region_col].isin(selected)]

if category_col:
    options = sorted(fdf[category_col].dropna().unique().tolist())
    selected = st.sidebar.multiselect("Category", options, default=options)
    fdf = fdf[fdf[category_col].isin(selected)]

if customer_type_col:
    options = sorted(fdf[customer_type_col].dropna().unique().tolist())
    selected = st.sidebar.multiselect("Customer Type", options, default=options)
    fdf = fdf[fdf[customer_type_col].isin(selected)]

if "Source_File" in fdf.columns:
    options = sorted(fdf["Source_File"].dropna().unique().tolist())
    selected = st.sidebar.multiselect("Source File", options, default=options)
    fdf = fdf[fdf["Source_File"].isin(selected)]

st.sidebar.caption(f"{len(fdf):,} order lines match the current filters.")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("E-Commerce Sales & Customer Analytics")
st.markdown(
    f"<div class='subtitle'>Showing <b>{source_label}</b> — use the filters on the left to slice the data. "
    f"Upload your own CSV in the sidebar to see these charts rebuilt from your file.</div>",
    unsafe_allow_html=True,
)

if fdf.empty:
    st.warning("No rows match the current filters.")
    st.stop()

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
kpis = []
if sales_col:
    kpis.append(("Total Revenue", fmt_inr(fdf[sales_col].sum())))
if profit_col:
    kpis.append(("Total Profit", fmt_inr(fdf[profit_col].sum())))
elif sales_col and margin_col:
    est_profit = (fdf[sales_col] * fdf[margin_col] / (100 if fdf[margin_col].max() > 1 else 1)).sum()
    kpis.append(("Total Profit (est.)", fmt_inr(est_profit)))
if order_id_col:
    kpis.append(("Total Orders", f"{fdf[order_id_col].nunique():,}"))
else:
    kpis.append(("Total Orders", f"{len(fdf):,}"))
if customer_id_col:
    kpis.append(("Total Customers", f"{fdf[customer_id_col].nunique():,}"))
if sales_col and order_id_col:
    aov = fdf[sales_col].sum() / max(fdf[order_id_col].nunique(), 1)
    kpis.append(("Avg Order Value", fmt_inr(aov)))
if margin_col:
    m = fdf[margin_col].mean()
    m = m * 100 if m <= 1 else m
    kpis.append(("Profit Margin", f"{m:.1f}%"))

if kpis:
    cols = st.columns(len(kpis))
    for (label, value), col in zip(kpis, cols):
        with col:
            st.metric(label=label, value=value)

st.markdown("---")

# ---------------------------------------------------------------------------
# Monthly Revenue & Profit Trend
# ---------------------------------------------------------------------------
if date_col and sales_col:
    st.subheader("Monthly Revenue & Profit Trend")
    trend_df = fdf.dropna(subset=[date_col]).copy()
    trend_df["_month"] = trend_df[date_col].dt.to_period("M").dt.to_timestamp()
    agg = {sales_col: "sum"}
    if profit_col:
        agg[profit_col] = "sum"
    trend = trend_df.groupby("_month").agg(agg).reset_index()

    fig_trend = px.line(trend, x="_month", y=[sales_col] + ([profit_col] if profit_col else []),
                         markers=True, color_discrete_sequence=["#2563eb", "#93c5fd"])
    fig_trend.update_layout(height=380, xaxis_title="Month", yaxis_title="Amount (₹)",
                             plot_bgcolor="white", margin=dict(t=20), legend_title_text="")
    fig_trend.update_xaxes(showgrid=False)
    fig_trend.update_yaxes(gridcolor="#eef0f2")
    st.plotly_chart(fig_trend, use_container_width=True)

# ---------------------------------------------------------------------------
# Revenue & Profit by Category / Revenue by Region
# ---------------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    if category_col and sales_col:
        st.subheader("Revenue & Profit by Category")
        agg = {sales_col: "sum"}
        if profit_col:
            agg[profit_col] = "sum"
        cat = fdf.groupby(category_col, observed=True).agg(agg).reset_index()
        cat = cat.sort_values(sales_col, ascending=False)
        fig_cat = px.bar(cat, x=category_col, y=sales_col, color=category_col,
                          color_discrete_sequence=px.colors.qualitative.Set2)
        fig_cat.update_layout(height=380, showlegend=False, plot_bgcolor="white", margin=dict(t=20))
        fig_cat.update_yaxes(gridcolor="#eef0f2")
        st.plotly_chart(fig_cat, use_container_width=True)

with c2:
    if region_col and sales_col:
        st.subheader("Revenue by Region")
        reg = fdf.groupby(region_col, observed=True)[sales_col].sum().reset_index()
        reg = reg.sort_values(sales_col, ascending=False)
        fig_reg = px.bar(reg, x=region_col, y=sales_col, color=region_col,
                          color_discrete_sequence=px.colors.qualitative.Set3)
        fig_reg.update_layout(height=380, showlegend=False, plot_bgcolor="white", margin=dict(t=20))
        fig_reg.update_yaxes(gridcolor="#eef0f2")
        st.plotly_chart(fig_reg, use_container_width=True)

# ---------------------------------------------------------------------------
# Customer segments
# ---------------------------------------------------------------------------
if customer_type_col and sales_col:
    st.subheader("Customer Segments")
    seg = fdf.groupby(customer_type_col, observed=True)[sales_col].sum().reset_index()
    if not seg.empty:
        fig_seg = px.pie(seg, names=customer_type_col, values=sales_col, hole=0.5,
                          color_discrete_sequence=px.colors.qualitative.Set2)
        fig_seg.update_layout(height=420)
        st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.info("No customer segment data for the current filter selection.")

# ---------------------------------------------------------------------------
# Discount vs margin
# ---------------------------------------------------------------------------
if discount_col and margin_col:
    st.subheader("Discount Band vs Average Profit Margin")
    ddf = fdf.copy()
    disc_vals = ddf[discount_col]
    disc_pct = disc_vals * 100 if disc_vals.max() <= 1 else disc_vals
    ddf["Discount_Band"] = pd.cut(
        disc_pct, bins=[-0.01, 0, 10, 20, 31],
        labels=["0%", "1-10%", "11-20%", "21-30%"]
    )
    m = ddf[margin_col]
    ddf["_margin_pct"] = m * 100 if m.max() <= 1 else m
    disc = ddf.groupby("Discount_Band", observed=True)["_margin_pct"].mean().reset_index()
    fig_disc = px.bar(disc, x="Discount_Band", y="_margin_pct", color="Discount_Band",
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_disc.update_layout(height=380, yaxis_title="Avg Profit Margin (%)", showlegend=False,
                            plot_bgcolor="white", margin=dict(t=20))
    fig_disc.update_yaxes(gridcolor="#eef0f2")
    st.plotly_chart(fig_disc, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Raw data
# ---------------------------------------------------------------------------
with st.expander("View filtered raw data"):
    st.dataframe(fdf.head(500), use_container_width=True)
    st.caption(f"Showing first 500 of {len(fdf):,} filtered rows.")

st.markdown("---")
st.caption("Built with Streamlit and Plotly. Upload your own CSV to see these charts rebuilt from your data.")
