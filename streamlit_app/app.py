import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="E-Commerce Sales & Customer Analytics",
    page_icon="📊",
    layout="wide",
)

# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_DIR / "ecommerce_cleaned.csv", parse_dates=["Order_Date"])
    customers = pd.read_csv(DATA_DIR / "customer_segments.csv", parse_dates=["Last_Order_Date"])
    return df, customers

df, customers = load_data()

# ----------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------
st.sidebar.header("Filters")

min_date, max_date = df["Order_Date"].min().date(), df["Order_Date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

regions = st.sidebar.multiselect("Region", sorted(df["Region"].unique()), default=list(df["Region"].unique()))
categories = st.sidebar.multiselect("Category", sorted(df["Category"].unique()), default=list(df["Category"].unique()))
cust_types = st.sidebar.multiselect("Customer Type", sorted(df["Customer_Type"].unique()), default=list(df["Customer_Type"].unique()))

mask = (
    (df["Order_Date"].dt.date >= start_date)
    & (df["Order_Date"].dt.date <= end_date)
    & (df["Region"].isin(regions))
    & (df["Category"].isin(categories))
    & (df["Customer_Type"].isin(cust_types))
)
fdf = df[mask]

st.sidebar.markdown("---")
st.sidebar.caption(f"{len(fdf):,} order lines match the current filters")

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.title("E-Commerce Sales & Customer Analytics")
st.caption("Synthetic transaction data, Jan 2023 to Dec 2024. Use the filters on the left to slice by date, region, category, and customer type.")

if fdf.empty:
    st.warning("No data matches the current filters. Try widening your selection.")
    st.stop()

# ----------------------------------------------------------------------
# KPI cards
# ----------------------------------------------------------------------
total_revenue = fdf["Revenue"].sum()
total_profit = fdf["Profit"].sum()
total_orders = fdf["Order_ID"].nunique()
total_customers = fdf["Customer_ID"].nunique()
aov = total_revenue / total_orders if total_orders else 0
margin = (total_profit / total_revenue * 100) if total_revenue else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Revenue", f"₹{total_revenue/1e7:.2f} Cr")
k2.metric("Total Profit", f"₹{total_profit/1e7:.2f} Cr")
k3.metric("Total Orders", f"{total_orders:,}")
k4.metric("Total Customers", f"{total_customers:,}")
k5.metric("Avg Order Value", f"₹{aov:,.0f}")
k6.metric("Profit Margin", f"{margin:.1f}%")

st.markdown("---")

# ----------------------------------------------------------------------
# Monthly revenue & profit trend
# ----------------------------------------------------------------------
st.subheader("Monthly Revenue & Profit Trend")
monthly = fdf.groupby("Month")[["Revenue", "Profit"]].sum().reset_index().sort_values("Month")
fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Revenue"], mode="lines+markers", name="Revenue"))
fig_trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Profit"], mode="lines+markers", name="Profit"))
fig_trend.update_layout(height=400, xaxis_title="Month", yaxis_title="Amount (₹)", hovermode="x unified")
st.plotly_chart(fig_trend, use_container_width=True)

# ----------------------------------------------------------------------
# Category & Region
# ----------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue & Profit by Category")
    cat_perf = fdf.groupby("Category")[["Revenue", "Profit"]].sum().reset_index().sort_values("Revenue", ascending=False)
    fig_cat = px.bar(cat_perf, x="Category", y=["Revenue", "Profit"], barmode="group")
    fig_cat.update_layout(height=380, yaxis_title="Amount (₹)")
    st.plotly_chart(fig_cat, use_container_width=True)

with col2:
    st.subheader("Revenue by Region")
    region_perf = fdf.groupby("Region")["Revenue"].sum().reset_index().sort_values("Revenue", ascending=False)
    fig_region = px.bar(region_perf, x="Region", y="Revenue", color="Region")
    fig_region.update_layout(height=380, yaxis_title="Revenue (₹)", showlegend=False)
    st.plotly_chart(fig_region, use_container_width=True)

# ----------------------------------------------------------------------
# Top products & customer segments
# ----------------------------------------------------------------------
col3, col4 = st.columns(2)

with col3:
    st.subheader("Top 10 Products by Revenue")
    top10 = (
        fdf.groupby(["Product_ID", "Product_Name"])["Revenue"].sum()
        .reset_index().sort_values("Revenue", ascending=False).head(10)
    )
    fig_top = px.bar(top10, x="Revenue", y="Product_Name", orientation="h")
    fig_top.update_layout(height=420, yaxis={"categoryorder": "total ascending"}, xaxis_title="Revenue (₹)", yaxis_title="")
    st.plotly_chart(fig_top, use_container_width=True)

with col4:
    st.subheader("Customer Segment Distribution")
    seg_ids = fdf["Customer_ID"].unique()
    seg_slice = customers[customers["Customer_ID"].isin(seg_ids)]
    if not seg_slice.empty:
        seg_counts = seg_slice["Segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Customers"]
        fig_seg = px.pie(seg_counts, names="Segment", values="Customers", hole=0.4)
        fig_seg.update_layout(height=420)
        st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.info("No customer segment data for the current filter selection.")

# ----------------------------------------------------------------------
# Discount vs margin
# ----------------------------------------------------------------------
st.subheader("Discount Band vs Average Profit Margin")
fdf = fdf.copy()
fdf["Discount_Band"] = pd.cut(fdf["Discount"], bins=[-0.01, 0, 0.1, 0.2, 0.31], labels=["0%", "1-10%", "11-20%", "21-30%"])
disc = fdf.groupby("Discount_Band", observed=True)["Profit_Margin"].mean().reset_index()
disc["Profit_Margin"] = disc["Profit_Margin"] * 100
fig_disc = px.bar(disc, x="Discount_Band", y="Profit_Margin", color="Discount_Band")
fig_disc.update_layout(height=380, yaxis_title="Avg Profit Margin (%)", showlegend=False)
st.plotly_chart(fig_disc, use_container_width=True)

# ----------------------------------------------------------------------
# Raw data (optional)
# ----------------------------------------------------------------------
with st.expander("View filtered raw data"):
    st.dataframe(fdf.head(500), use_container_width=True)
    st.caption(f"Showing first 500 of {len(fdf):,} filtered rows.")

st.markdown("---")
st.caption("Data is synthetic, generated for portfolio purposes. Built with Streamlit and Plotly.")
