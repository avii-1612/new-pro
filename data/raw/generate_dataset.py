"""
generate_dataset.py
--------------------
Generates a SYNTHETIC e-commerce transactions dataset for the
E-Commerce Sales & Customer Analytics portfolio project.

This dataset is NOT real. It is created using controlled randomness
(numpy/pandas) so that the statistical patterns (seasonality, category
profit margins, discount effects, repeat customers) are realistic
enough to produce meaningful analysis, while every value is generated,
not scraped or copied from a real company.

Intentional "messiness" is injected on purpose (missing values,
duplicate rows, a few invalid quantities/prices) so the cleaning
notebook has real problems to solve.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

N_ROWS = 18000  # within the 10,000-50,000 requirement

# ---- Reference lists -------------------------------------------------
categories = {
    "Electronics": ["Headphones", "Smartphone", "Laptop", "Smartwatch", "Tablet", "Camera"],
    "Fashion": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Handbag", "Sunglasses"],
    "Home & Kitchen": ["Mixer Grinder", "Cookware Set", "Air Purifier", "Vacuum Cleaner", "Bedsheet Set"],
    "Sports": ["Yoga Mat", "Cricket Bat", "Dumbbell Set", "Running Shoes", "Cycling Helmet"],
    "Beauty": ["Face Cream", "Perfume", "Hair Dryer", "Lipstick", "Sunscreen"],
    "Books": ["Fiction Novel", "Self-Help Book", "Comic Book", "Textbook", "Cookbook"],
}

regions_states = {
    "North": ["Delhi", "Uttar Pradesh", "Punjab", "Haryana"],
    "South": ["Karnataka", "Tamil Nadu", "Kerala", "Telangana"],
    "East": ["West Bengal", "Odisha", "Bihar", "Jharkhand"],
    "West": ["Maharashtra", "Gujarat", "Rajasthan", "Goa"],
}

payment_modes = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery"]
customer_types = ["New", "Returning"]

# Base unit price range & typical margin per category (used to build realistic Cost/Profit)
category_price_range = {
    "Electronics": (1500, 60000),
    "Fashion": (400, 5000),
    "Home & Kitchen": (800, 15000),
    "Sports": (500, 8000),
    "Beauty": (150, 3000),
    "Books": (150, 1200),
}
category_margin = {  # avg cost as % of unit price (lower = higher margin)
    "Electronics": 0.80,
    "Fashion": 0.55,
    "Home & Kitchen": 0.68,
    "Sports": 0.62,
    "Beauty": 0.50,
    "Books": 0.70,
}

n_customers = 4200
customer_ids = [f"CUST{str(i).zfill(5)}" for i in range(1, n_customers + 1)]
first_names = ["Aarav","Vivaan","Aditya","Vihaan","Arjun","Sai","Reyansh","Ayaan","Krishna","Ishaan",
               "Ananya","Diya","Saanvi","Aadhya","Kiara","Myra","Anika","Navya","Riya","Isha"]
last_names = ["Sharma","Verma","Gupta","Singh","Kumar","Patel","Reddy","Nair","Iyer","Mehta",
              "Chopra","Bose","Das","Rao","Malhotra","Kapoor","Joshi","Agarwal","Pillai","Menon"]
customer_name_map = {cid: f"{np.random.choice(first_names)} {np.random.choice(last_names)}" for cid in customer_ids}
customer_type_map = {cid: np.random.choice(customer_types, p=[0.42, 0.58]) for cid in customer_ids}

n_products_per_cat = 30
product_catalog = []
for cat, subs in categories.items():
    lo, hi = category_price_range[cat]
    for i in range(n_products_per_cat):
        sub = np.random.choice(subs)
        pid = f"PRD-{cat[:3].upper()}-{i+1:03d}"
        pname = f"{sub} {np.random.choice(['Pro','Max','Lite','Plus','Classic','Air','Elite','Basic'])} {i+1}"
        price = round(np.random.uniform(lo, hi), 2)
        product_catalog.append((pid, pname, cat, sub, price))
product_df = pd.DataFrame(product_catalog, columns=["Product_ID", "Product_Name", "Category", "Sub_Category", "Base_Price"])

# ---- Date range with seasonality (higher sales Oct-Jan, lower May-Jun) ----
date_range = pd.date_range("2023-01-01", "2024-12-31", freq="D")
month_weight = {1:1.1,2:0.9,3:0.9,4:0.85,5:0.7,6:0.75,7:0.85,8:0.9,9:1.0,10:1.3,11:1.5,12:1.6}
day_weights = np.array([month_weight[d.month] for d in date_range])
day_probs = day_weights / day_weights.sum()

rows = []
order_counter = 100000

for _ in range(N_ROWS):
    order_date = np.random.choice(date_range, p=day_probs)
    order_date = pd.Timestamp(order_date)

    prod = product_df.sample(1).iloc[0]
    cat = prod["Category"]
    sub_cat = prod["Sub_Category"]
    base_price = prod["Base_Price"]

    # small price fluctuation (sales/promo pricing)
    unit_price = round(base_price * np.random.uniform(0.9, 1.05), 2)

    quantity = np.random.choice([1, 2, 3, 4, 5], p=[0.55, 0.22, 0.13, 0.06, 0.04])

    cust_id = np.random.choice(customer_ids)
    region = np.random.choice(list(regions_states.keys()))
    state = np.random.choice(regions_states[region])

    discount_pct = np.random.choice([0, 5, 10, 15, 20, 25, 30], p=[0.30,0.20,0.18,0.14,0.10,0.05,0.03]) / 100

    cost_ratio = category_margin[cat] * np.random.uniform(0.95, 1.05)
    unit_cost = round(unit_price * cost_ratio, 2)

    sales = round(unit_price * quantity, 2)
    discount_amount = round(sales * discount_pct, 2)
    revenue = round(sales - discount_amount, 2)
    total_cost = round(unit_cost * quantity, 2)
    profit = round(revenue - total_cost, 2)

    order_counter += 1
    rows.append({
        "Order_ID": f"ORD{order_counter}",
        "Order_Date": order_date.strftime("%Y-%m-%d"),
        "Customer_ID": cust_id,
        "Customer_Name": customer_name_map[cust_id],
        "Product_ID": prod["Product_ID"],
        "Product_Name": prod["Product_Name"],
        "Category": cat,
        "Sub_Category": sub_cat,
        "Region": region,
        "State": state,
        "Quantity": quantity,
        "Unit_Price": unit_price,
        "Sales": sales,
        "Discount": discount_pct,
        "Cost": total_cost,
        "Profit": profit,
        "Payment_Mode": np.random.choice(payment_modes, p=[0.25,0.2,0.35,0.12,0.08]),
        "Customer_Type": customer_type_map[cust_id],
    })

df = pd.DataFrame(rows)

# ---------------------------------------------------------------------
# Inject realistic messiness ON PURPOSE so the cleaning notebook has
# genuine problems to fix (this mirrors real-world messy exports).
# ---------------------------------------------------------------------
rng = np.random.default_rng(7)

# 1. Missing values in a few columns
for col, frac in [("Customer_Name", 0.01), ("Discount", 0.02), ("Payment_Mode", 0.015), ("State", 0.01)]:
    idx = rng.choice(df.index, size=int(len(df) * frac), replace=False)
    df.loc[idx, col] = np.nan

# 2. Some duplicate rows (simulating double-submitted orders)
dupe_idx = rng.choice(df.index, size=150, replace=False)
df = pd.concat([df, df.loc[dupe_idx]], ignore_index=True)

# 3. A few invalid/negative quantities and zero unit prices (data entry errors)
bad_idx = rng.choice(df.index, size=40, replace=False)
df.loc[bad_idx[:20], "Quantity"] = -1
df.loc[bad_idx[20:], "Unit_Price"] = 0

# 4. Inconsistent text casing in a few Category values (real-world mess)
case_idx = rng.choice(df.index, size=60, replace=False)
df.loc[case_idx, "Category"] = df.loc[case_idx, "Category"].str.upper()

# 5. A few malformed date strings
date_idx = rng.choice(df.index, size=25, replace=False)
df.loc[date_idx, "Order_Date"] = "0000-00-00"

# Shuffle rows so duplicates aren't all at the bottom
df = df.sample(frac=1, random_state=1).reset_index(drop=True)

df.to_csv("/home/claude/ecommerce-sales-analytics/data/raw/ecommerce_raw.csv", index=False)
print("Saved raw dataset:", df.shape)
print(df.head())
