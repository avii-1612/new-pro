import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# ------------------------------------------------------------------
md("""# E-Commerce Sales & Customer Analytics

Dataset: a synthetic e-commerce transactions dataset (18,000+ orders, 2023-2024) built to look like a real online retail export. I generated it myself for this portfolio project, so it's not real company data, but the patterns (seasonality, category margins, repeat customers) are modeled realistically.

Goal: clean the raw export, dig into sales/profit/customer patterns, and pull out insights I could actually present to a business stakeholder.""")

# ------------------------------------------------------------------
md("## Part 1: Loading the data")
code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 5)
pd.set_option("display.max_columns", None)

RAW_PATH = "../data/raw/ecommerce_raw.csv"
df = pd.read_csv(RAW_PATH)
df.shape""")

code("""df.head()""")

md("Before touching any values I want to check the shape, column types, and a quick statistical summary. Dates and numbers usually get loaded as plain text (`object`), so I need to know that before doing any date math or arithmetic later.")

code("""print("Shape:", df.shape)
print("\\nColumns:", list(df.columns))
print("\\nData types:\\n", df.dtypes)""")

code("""df.describe(include="all").T""")

# ------------------------------------------------------------------
md("## Part 2: Checking data quality")

md("### Missing values")
code("""missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_report = pd.DataFrame({"missing_count": missing, "missing_pct": missing_pct})
missing_report[missing_report.missing_count > 0].sort_values("missing_count", ascending=False)""")

md("### Duplicate records")
code("""dupe_count = df.duplicated().sum()
print(f"Fully duplicate rows: {dupe_count}")

# a single order should only show up once, so check duplicate Order_IDs too
dupe_orders = df.duplicated(subset=["Order_ID"]).sum()
print(f"Duplicate Order_IDs: {dupe_orders}")""")

md("### Invalid values")
code("""print("Rows with non-positive Quantity:", (df.Quantity <= 0).sum())
print("Rows with Unit_Price == 0:", (df.Unit_Price == 0).sum())
print("Distinct Category values (checking for inconsistent casing):")
print(df.Category.unique())""")

# ------------------------------------------------------------------
md("""## Part 3: Cleaning the data

My plan here:
1. Drop exact duplicate rows. These look like double-submitted orders, and keeping them would double-count revenue.
2. Fix inconsistent text casing in `Category` (e.g. `"ELECTRONICS"` and `"Electronics"` should be the same bucket).
3. Drop rows where `Quantity` is 0 or negative, or `Unit_Price` is 0. These are data entry errors, not real sales, and would mess up revenue/profit totals if left in.
4. Fix the malformed date strings, then convert `Order_Date` to an actual datetime.
5. Fill in missing text fields with `"Unknown"` instead of dropping the whole row, since the rest of the row is still valid sales data.
6. Fill missing `Discount` with 0.""")

code("""df_clean = df.copy()

# 1. drop exact duplicate rows
before = len(df_clean)
df_clean = df_clean.drop_duplicates()
print(f"Dropped {before - len(df_clean)} duplicate rows")

# 2. fix category casing
df_clean["Category"] = df_clean["Category"].str.strip().str.title()

# 3. drop invalid quantity / price rows
before = len(df_clean)
df_clean = df_clean[(df_clean["Quantity"] > 0) & (df_clean["Unit_Price"] > 0)]
print(f"Dropped {before - len(df_clean)} rows with invalid Quantity/Unit_Price")

# 4. fix malformed dates, then convert to datetime
df_clean["Order_Date"] = df_clean["Order_Date"].replace("0000-00-00", np.nan)
before = len(df_clean)
df_clean = df_clean.dropna(subset=["Order_Date"])
print(f"Dropped {before - len(df_clean)} rows with malformed/missing Order_Date")
df_clean["Order_Date"] = pd.to_datetime(df_clean["Order_Date"])

# 5 & 6. fill remaining missing values
df_clean["Customer_Name"] = df_clean["Customer_Name"].fillna("Unknown")
df_clean["Payment_Mode"] = df_clean["Payment_Mode"].fillna("Unknown")
df_clean["State"] = df_clean["State"].fillna("Unknown")
df_clean["Discount"] = df_clean["Discount"].fillna(0)

print("\\nRemaining missing values:", df_clean.isnull().sum().sum())
print("Final shape:", df_clean.shape)""")

md("Now adding a few calculated columns that make the rest of the analysis easier.")
code("""df_clean["Revenue"] = (df_clean["Sales"] * (1 - df_clean["Discount"])).round(2)
df_clean["Profit_Margin"] = (df_clean["Profit"] / df_clean["Revenue"]).round(4)
df_clean["Month"] = df_clean["Order_Date"].dt.to_period("M").astype(str)
df_clean["Quarter"] = df_clean["Order_Date"].dt.to_period("Q").astype(str)
df_clean["Year"] = df_clean["Order_Date"].dt.year

df_clean[["Order_Date","Sales","Discount","Revenue","Cost","Profit","Profit_Margin","Month","Quarter","Year"]].head()""")

md("Quick outlier check using IQR. I'm not deleting anything here though, since a big Revenue value could just be a legit bulk order, not bad data.")
code("""Q1, Q3 = df_clean["Revenue"].quantile([0.25, 0.75])
IQR = Q3 - Q1
lower, upper = Q1 - 1.5*IQR, Q3 + 1.5*IQR
outliers = df_clean[(df_clean["Revenue"] < lower) | (df_clean["Revenue"] > upper)]
print(f"Potential Revenue outliers: {len(outliers)} rows ({len(outliers)/len(df_clean)*100:.2f}% of data)")""")

code("""df_clean.to_csv("../data/cleaned/ecommerce_cleaned.csv", index=False)
print("Saved cleaned dataset:", df_clean.shape)""")

# ------------------------------------------------------------------
md("## Part 4: EDA")

md("### KPIs first")
code("""total_revenue = df_clean["Revenue"].sum()
total_profit = df_clean["Profit"].sum()
total_orders = df_clean["Order_ID"].nunique()
total_customers = df_clean["Customer_ID"].nunique()
avg_order_value = total_revenue / total_orders
overall_margin = total_profit / total_revenue

print(f"Total Revenue      : Rs {total_revenue:,.0f}")
print(f"Total Profit       : Rs {total_profit:,.0f}")
print(f"Total Orders       : {total_orders:,}")
print(f"Total Customers    : {total_customers:,}")
print(f"Avg Order Value    : Rs {avg_order_value:,.2f}")
print(f"Overall Profit Margin: {overall_margin*100:.2f}%")""")

md("### Monthly revenue and profit trend")
code("""monthly = df_clean.groupby("Month")[["Revenue","Profit"]].sum().reset_index()

fig, ax = plt.subplots()
ax.plot(monthly["Month"], monthly["Revenue"], marker="o", label="Revenue")
ax.plot(monthly["Month"], monthly["Profit"], marker="o", label="Profit")
ax.set_title("Monthly Revenue & Profit Trend")
ax.set_xlabel("Month"); ax.set_ylabel("Amount (Rs)")
plt.xticks(rotation=75)
ax.legend()
plt.tight_layout()
plt.show()""")

md("Revenue climbs from October through December, which lines up with festive/holiday season shopping, then dips again around May-June. Makes sense to plan inventory and ad spend around that Q4 spike instead of spreading budget evenly across the year.")

md("### Category and sub-category performance")
code("""cat_perf = df_clean.groupby("Category")[["Revenue","Profit"]].sum().sort_values("Revenue", ascending=False)
cat_perf["Profit_Margin_%"] = (cat_perf["Profit"]/cat_perf["Revenue"]*100).round(2)
cat_perf""")

code("""fig, axes = plt.subplots(1, 2, figsize=(14,5))
cat_perf["Revenue"].plot(kind="bar", ax=axes[0], color="#4C72B0")
axes[0].set_title("Revenue by Category")
axes[0].set_ylabel("Revenue (Rs)")

cat_perf["Profit"].plot(kind="bar", ax=axes[1], color="#DD8452")
axes[1].set_title("Profit by Category")
axes[1].set_ylabel("Profit (Rs)")
plt.tight_layout()
plt.show()""")

md("The category bringing in the most revenue isn't automatically the most profitable one. Worth checking `Profit_Margin_%` alongside `Revenue` here, since a high-revenue/low-margin category is a candidate for pricing review, and a high-margin one is worth pushing harder in marketing.")

md("### Top and bottom 10 products")
code("""product_perf = df_clean.groupby(["Product_ID","Product_Name"])[["Revenue","Profit","Quantity"]].sum()

top10 = product_perf.sort_values("Revenue", ascending=False).head(10)
bottom10 = product_perf[product_perf["Quantity"]>0].sort_values("Revenue", ascending=True).head(10)

print("Top 10 products by revenue"); display(top10)
print("\\nBottom 10 products by revenue"); display(bottom10)""")

md("### Regional performance")
code("""region_perf = df_clean.groupby("Region")[["Revenue","Profit"]].sum().sort_values("Revenue", ascending=False)
region_perf["Profit_Margin_%"] = (region_perf["Profit"]/region_perf["Revenue"]*100).round(2)

region_perf["Revenue"].plot(kind="bar", color="#55A868", title="Revenue by Region")
plt.ylabel("Revenue (Rs)")
plt.tight_layout()
plt.show()
region_perf""")

md("Whichever region tops this list is carrying a bigger share of revenue than the rest. If one region is clearly behind, that's a signal to look at marketing spend or delivery/logistics issues there.")

md("### New vs returning customers")
code("""cust_type_perf = df_clean.groupby("Customer_Type")[["Revenue","Profit"]].sum()
order_counts = df_clean.groupby("Customer_Type")["Order_ID"].nunique()
cust_type_perf["Orders"] = order_counts
cust_type_perf["AOV"] = (cust_type_perf["Revenue"]/cust_type_perf["Orders"]).round(2)
cust_type_perf""")

md("### Discount vs profit\nDoes discounting harder actually hurt margin?")
code("""df_clean["Discount_Band"] = pd.cut(df_clean["Discount"], bins=[-0.01,0,0.1,0.2,0.31],
                                     labels=["0%","1-10%","11-20%","21-30%"])
disc_profit = df_clean.groupby("Discount_Band")["Profit_Margin"].mean().reset_index()

fig, ax = plt.subplots()
ax.bar(disc_profit["Discount_Band"].astype(str), disc_profit["Profit_Margin"]*100, color="#C44E52")
ax.set_title("Average Profit Margin by Discount Band")
ax.set_ylabel("Avg Profit Margin (%)")
ax.set_xlabel("Discount Band")
plt.tight_layout()
plt.show()""")

md("Yes, pretty clearly. Margin drops as the discount band goes up, and it's steepest in the 21-30% band. So deep discounts should probably be used sparingly, on slow-moving stock, not as a default sales tactic.")

md("### Quantity vs revenue")
code("""fig, ax = plt.subplots()
sample = df_clean.sample(min(3000, len(df_clean)), random_state=1)
ax.scatter(sample["Quantity"], sample["Revenue"], alpha=0.3)
ax.set_title("Quantity vs Revenue (sampled orders)")
ax.set_xlabel("Quantity"); ax.set_ylabel("Revenue (Rs)")
plt.tight_layout()
plt.show()""")

md("### Repeat vs new customers, share of revenue")
code("""rev_share = df_clean.groupby("Customer_Type")["Revenue"].sum()
rev_share_pct = (rev_share / rev_share.sum() * 100).round(2)

fig, ax = plt.subplots()
ax.pie(rev_share_pct, labels=rev_share_pct.index, autopct="%1.1f%%", colors=["#4C72B0","#DD8452"])
ax.set_title("Revenue Share: New vs Returning Customers")
plt.tight_layout()
plt.show()
rev_share_pct""")

md("Returning customers punch above their weight here, contributing more revenue share than you'd expect from their numbers alone. Points toward retention being a better investment than pure acquisition for this business.")

# ------------------------------------------------------------------
md("""## Part 5: Customer-level analysis and RFM segmentation

Keeping the methodology simple here since this needs to be explainable in an interview:
- Recency: days since the customer's last order (lower is better, means more recently active)
- Frequency: number of distinct orders
- Monetary: total revenue from that customer

Each customer gets scored 1-4 (quartiles) on each of the three, and I average the scores to bucket people into High/Medium/Low value segments.""")

code("""snapshot_date = df_clean["Order_Date"].max() + pd.Timedelta(days=1)

customer_agg = df_clean.groupby("Customer_ID").agg(
    Customer_Name=("Customer_Name","first"),
    Last_Order_Date=("Order_Date","max"),
    Frequency=("Order_ID","nunique"),
    Monetary=("Revenue","sum"),
).reset_index()

customer_agg["Recency"] = (snapshot_date - customer_agg["Last_Order_Date"]).dt.days
customer_agg["AOV"] = (customer_agg["Monetary"] / customer_agg["Frequency"]).round(2)

customer_agg.sort_values("Monetary", ascending=False).head(10)""")

code("""# RFM scoring, 1 = worst, 4 = best
customer_agg["R_Score"] = pd.qcut(customer_agg["Recency"], 4, labels=[4,3,2,1]).astype(int)
customer_agg["F_Score"] = pd.qcut(customer_agg["Frequency"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)
customer_agg["M_Score"] = pd.qcut(customer_agg["Monetary"], 4, labels=[1,2,3,4]).astype(int)
customer_agg["RFM_Score"] = (customer_agg["R_Score"] + customer_agg["F_Score"] + customer_agg["M_Score"]) / 3

def segment(score):
    if score >= 3:
        return "High Value"
    elif score >= 2:
        return "Medium Value"
    else:
        return "Low Value"

customer_agg["Segment"] = customer_agg["RFM_Score"].apply(segment)
customer_agg["Segment"].value_counts()""")

code("""seg_summary = customer_agg.groupby("Segment").agg(
    Customers=("Customer_ID","count"),
    Avg_Monetary=("Monetary","mean"),
    Avg_Frequency=("Frequency","mean"),
).round(2).sort_values("Avg_Monetary", ascending=False)
seg_summary""")

code("""fig, ax = plt.subplots()
customer_agg["Segment"].value_counts().plot(kind="bar", color=["#55A868","#DD8452","#C44E52"], ax=ax)
ax.set_title("Customer Segment Distribution")
ax.set_ylabel("Number of Customers")
plt.tight_layout()
plt.show()""")

md("### Repeat purchase rate")
code("""repeat_customers = (customer_agg["Frequency"] > 1).sum()
repeat_rate = repeat_customers / len(customer_agg) * 100
print(f"Repeat purchase rate: {repeat_rate:.2f}% ({repeat_customers} of {len(customer_agg)} customers)")

customer_agg.to_csv("../data/cleaned/customer_segments.csv", index=False)""")

# ------------------------------------------------------------------
md("""## Part 6: Pulling the final numbers together

Just printing out the specific numbers I reference in `reports/business_insights.md`, so every claim in that report traces back to something computed here.""")

code("""best_cat_revenue = cat_perf["Revenue"].idxmax()
best_cat_profit = cat_perf["Profit"].idxmax()
best_cat_margin = cat_perf["Profit_Margin_%"].idxmax()
worst_cat_margin = cat_perf["Profit_Margin_%"].idxmin()
best_region = region_perf["Revenue"].idxmax()
worst_region = region_perf["Revenue"].idxmin()
best_month = monthly.sort_values("Revenue", ascending=False).iloc[0]["Month"]
top_product_name = top10.reset_index().iloc[0]["Product_Name"]

print("Best category by revenue:", best_cat_revenue)
print("Best category by profit:", best_cat_profit)
print("Best category by margin:", best_cat_margin)
print("Worst category by margin:", worst_cat_margin)
print("Best region:", best_region)
print("Weakest region:", worst_region)
print("Best month:", best_month)
print("Top product:", top_product_name)
print("Repeat purchase rate: %.2f%%" % repeat_rate)
print("Overall profit margin: %.2f%%" % (overall_margin*100))""")

nb["cells"] = cells
nbf.write(nb, "/home/claude/ecommerce-sales-analytics/notebooks/ecommerce_analysis.ipynb")
print("Notebook written.")
