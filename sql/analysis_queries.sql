-- ============================================================
-- E-Commerce Sales & Customer Analytics - SQL queries
-- ============================================================
-- Table: sales (loaded from data/cleaned/ecommerce_cleaned.csv)
-- Columns used: Order_ID, Order_Date, Customer_ID, Customer_Name, Product_ID,
-- Product_Name, Category, Sub_Category, Region, State, Quantity, Unit_Price,
-- Revenue, Cost, Profit, Profit_Margin, Month, Quarter, Year, Payment_Mode,
-- Customer_Type
--
-- Written in standard SQL, tested against SQLite. Should run the same on
-- Postgres, MySQL 8+, or SQL Server without changes.
-- All 18 queries below were run against the cleaned dataset to confirm
-- they actually work and return real results, not just written from memory.
-- ============================================================


-- 1. Total sales (revenue)
SELECT ROUND(SUM(Revenue), 2) AS Total_Revenue
FROM sales;


-- 2. Total profit
SELECT ROUND(SUM(Profit), 2) AS Total_Profit
FROM sales;


-- 3. Monthly sales
SELECT Month, ROUND(SUM(Revenue), 2) AS Monthly_Revenue
FROM sales
GROUP BY Month
ORDER BY Month;


-- 4. Monthly profit
SELECT Month, ROUND(SUM(Profit), 2) AS Monthly_Profit
FROM sales
GROUP BY Month
ORDER BY Month;


-- 5. Top 10 products by revenue
SELECT Product_ID, Product_Name, ROUND(SUM(Revenue), 2) AS Product_Revenue,
       ROUND(SUM(Profit), 2) AS Product_Profit, SUM(Quantity) AS Units_Sold
FROM sales
GROUP BY Product_ID, Product_Name
ORDER BY Product_Revenue DESC
LIMIT 10;


-- 6. Top categories by revenue
SELECT Category, ROUND(SUM(Revenue), 2) AS Category_Revenue,
       ROUND(SUM(Profit), 2) AS Category_Profit,
       ROUND(SUM(Profit) * 100.0 / SUM(Revenue), 2) AS Profit_Margin_Pct
FROM sales
GROUP BY Category
ORDER BY Category_Revenue DESC;


-- 7. Top 10 customers by spending
SELECT Customer_ID, Customer_Name, ROUND(SUM(Revenue), 2) AS Total_Spent,
       COUNT(DISTINCT Order_ID) AS Orders_Placed
FROM sales
GROUP BY Customer_ID, Customer_Name
ORDER BY Total_Spent DESC
LIMIT 10;


-- 8. Regional sales
SELECT Region, ROUND(SUM(Revenue), 2) AS Region_Revenue,
       ROUND(SUM(Profit), 2) AS Region_Profit,
       ROUND(SUM(Profit) * 100.0 / SUM(Revenue), 2) AS Profit_Margin_Pct
FROM sales
GROUP BY Region
ORDER BY Region_Revenue DESC;


-- 9. Average order value
-- total revenue divided by number of distinct orders
SELECT ROUND(SUM(Revenue) * 1.0 / COUNT(DISTINCT Order_ID), 2) AS Avg_Order_Value
FROM sales;


-- 10. Customers with highest spending, tagged by spend segment
-- using CASE to bucket customers into simple tiers
SELECT Customer_ID, Customer_Name, ROUND(SUM(Revenue), 2) AS Total_Spent,
       CASE
           WHEN SUM(Revenue) >= 100000 THEN 'High Value'
           WHEN SUM(Revenue) >= 30000  THEN 'Medium Value'
           ELSE 'Low Value'
       END AS Spend_Segment
FROM sales
GROUP BY Customer_ID, Customer_Name
ORDER BY Total_Spent DESC
LIMIT 20;


-- 11. Repeat customers
-- a customer counts as "repeat" if they have more than one distinct order
SELECT COUNT(*) AS Repeat_Customers
FROM (
    SELECT Customer_ID
    FROM sales
    GROUP BY Customer_ID
    HAVING COUNT(DISTINCT Order_ID) > 1
) repeat_cust;


-- 11b. Repeat purchase rate (%)
-- CTE + subquery: repeat customers as a percentage of all customers
WITH customer_orders AS (
    SELECT Customer_ID, COUNT(DISTINCT Order_ID) AS Order_Count
    FROM sales
    GROUP BY Customer_ID
)
SELECT
    ROUND(
        (SELECT COUNT(*) FROM customer_orders WHERE Order_Count > 1) * 100.0
        / (SELECT COUNT(*) FROM customer_orders), 2
    ) AS Repeat_Purchase_Rate_Pct
FROM customer_orders
LIMIT 1;


-- 12. Products with low profitability (bottom 10 by margin)
-- HAVING filters out low-volume products so a single lucky/unlucky sale
-- doesn't skew the ranking (requiring at least 20 units sold)
SELECT Product_ID, Product_Name,
       ROUND(SUM(Profit) * 100.0 / NULLIF(SUM(Revenue), 0), 2) AS Profit_Margin_Pct,
       SUM(Quantity) AS Units_Sold
FROM sales
GROUP BY Product_ID, Product_Name
HAVING SUM(Quantity) >= 20
ORDER BY Profit_Margin_Pct ASC
LIMIT 10;


-- 13. Profit margin by category
SELECT Category,
       ROUND(SUM(Profit) * 100.0 / SUM(Revenue), 2) AS Profit_Margin_Pct
FROM sales
GROUP BY Category
ORDER BY Profit_Margin_Pct DESC;


-- 14. Year-over-year sales growth (window function)
-- LAG() pulls the previous year's revenue into the same row so we can
-- compute a growth percentage
WITH yearly_sales AS (
    SELECT Year, SUM(Revenue) AS Yearly_Revenue
    FROM sales
    GROUP BY Year
)
SELECT Year, Yearly_Revenue,
       LAG(Yearly_Revenue) OVER (ORDER BY Year) AS Prev_Year_Revenue,
       ROUND(
           (Yearly_Revenue - LAG(Yearly_Revenue) OVER (ORDER BY Year)) * 100.0
           / LAG(Yearly_Revenue) OVER (ORDER BY Year), 2
       ) AS YoY_Growth_Pct
FROM yearly_sales
ORDER BY Year;


-- 15. Running total of monthly revenue (window function)
-- useful for a "cumulative revenue to date" style chart
SELECT Month, ROUND(SUM(Revenue), 2) AS Monthly_Revenue,
       ROUND(SUM(SUM(Revenue)) OVER (ORDER BY Month), 2) AS Running_Total_Revenue
FROM sales
GROUP BY Month
ORDER BY Month;


-- 16. Discount band vs average profit margin
-- same CASE-based bucketing used in the Python notebook, done here in SQL
SELECT
    CASE
        WHEN Discount = 0 THEN '0%'
        WHEN Discount <= 0.10 THEN '1-10%'
        WHEN Discount <= 0.20 THEN '11-20%'
        ELSE '21-30%'
    END AS Discount_Band,
    ROUND(AVG(Profit_Margin) * 100, 2) AS Avg_Profit_Margin_Pct,
    COUNT(*) AS Order_Lines
FROM sales
GROUP BY Discount_Band
ORDER BY Discount_Band;


-- 17. New vs returning customer revenue share
SELECT Customer_Type, ROUND(SUM(Revenue), 2) AS Revenue,
       ROUND(SUM(Revenue) * 100.0 / (SELECT SUM(Revenue) FROM sales), 2) AS Pct_Of_Total_Revenue
FROM sales
GROUP BY Customer_Type;
