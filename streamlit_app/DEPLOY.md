# Deploying the Dashboard

This folder (`streamlit_app/`) is self-contained: the app plus a copy of the cleaned data it needs. That's on purpose, so you can push just this folder (or the whole repo) to GitHub and deploy straight from there.

## Fastest option: Streamlit Community Cloud (free)

1. Push this project to a GitHub repo (public or private, both work).
2. Go to https://share.streamlit.io and sign in with your GitHub account.
3. Click "New app", pick your repo, and set:
   - Branch: `main`
   - Main file path: `streamlit_app/app.py`
4. Click Deploy. First build takes a minute or two, then you get a live URL like `https://your-app-name.streamlit.app`.
5. Any time you push new commits to that branch, the app redeploys automatically.

That's it, no server to manage, and it's free for public repos.

## If you'd rather run it locally first

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

This opens the dashboard at `http://localhost:8501`. Good for checking it looks right before deploying.

## Alternative: Hugging Face Spaces
Also free, works the same way. Create a new Space, choose "Streamlit" as the SDK, and upload `app.py`, `requirements.txt`, and the `data/` folder. It'll build and give you a live URL under `huggingface.co/spaces/your-username/your-space`.

## What's in this folder
```
streamlit_app/
├── app.py              # the dashboard itself
├── requirements.txt    # streamlit, pandas, plotly
└── data/
    ├── ecommerce_cleaned.csv
    └── customer_segments.csv
```

## What the dashboard has
- KPI cards: Total Revenue, Total Profit, Total Orders, Total Customers, Average Order Value, Profit Margin
- Sidebar filters: date range, region, category, customer type, all charts update live
- Monthly revenue and profit trend line chart
- Revenue and profit by category, side by side
- Revenue by region
- Top 10 products by revenue
- Customer segment breakdown (High/Medium/Low value)
- Discount band vs average profit margin
- Expandable raw data table for the current filter selection

## If you want to change something
`app.py` is one file, roughly 130 lines, no callbacks or complicated state beyond the sidebar filters. The filter logic is a single `mask` built near the top; every chart below just reads from `fdf` (the filtered dataframe). Easiest place to add a new chart: copy one of the existing `st.subheader(...)` + `px.bar(...)` / `px.pie(...)` blocks and adjust the groupby.
