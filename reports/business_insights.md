# Business Insights

Numbers below come straight from `data/cleaned/ecommerce_cleaned.csv` (17,935 clean order lines, 4,147 customers, Jan 2023 to Dec 2024). Part 6 of the notebook prints out the exact figures used here, so nothing here is made up.

## Headline numbers
- Total Revenue: Rs 23,14,83,433
- Total Profit: Rs 4,37,20,668
- Overall Profit Margin: 18.89%
- Total Orders: 17,935
- Total Customers: 4,147
- Average Order Value: Rs 12,906.80
- Repeat Purchase Rate: 93.47%

## What stood out

**Electronics brings in the most revenue but has the weakest margin.** It's about 63% of total revenue (Rs 14.5 Cr) and the biggest profit contributor in absolute terms (Rs 1.74 Cr), but its margin sits at just 12%, the lowest of any category. High price tags, thin per-unit profit.

**Beauty and Fashion make more money per rupee sold.** Beauty runs at a 45% margin and Fashion at 39%, well above Electronics, even though both bring in far less total revenue. If the goal is profit efficiency rather than raw volume, these two are worth more attention.

**Regions are pretty balanced.** North (Rs 6.07 Cr), South (Rs 5.85 Cr), West (Rs 5.66 Cr), and East (Rs 5.57 Cr) are all within about 9% of each other, and margin is roughly 19% everywhere. There isn't really a weak region to fix here, growth is more about total demand than regional gaps.

**Sales peak in Q4.** December 2024 was the single best month (Rs 1.54 Cr), with October and November 2023 close behind, which tracks with festive season shopping. There's a consistent dip around May-June every year.

**Discounts hurt margin, and it's not subtle.** Average margin goes from 35.4% at no discount, down to 30.8% (1-10% discount), 22.6% (11-20%), and just 12.3% once discounts hit 21-30%. This is probably the single biggest lever affecting profitability in this dataset.

**Returning customers carry the business.** They make up 58% of revenue (Rs 13.51 Cr) versus 42% from new customers (Rs 9.64 Cr), even though the two groups aren't wildly different in size. Retention is clearly doing a lot of work here.

**93.47% repeat purchase rate.** Most customers who buy once come back. That's a strong signal and worth protecting through some kind of loyalty program rather than taking it for granted.

**Top products are all Electronics.** Every one of the top 10 products by revenue is a phone, smartwatch, or tablet. "Smartphone Classic 11" alone did over Rs 1.05 Cr.

**Lowest-revenue products cluster in Beauty and Books.** Things like "Lipstick Basic 8" barely move the revenue needle, though a few of them still hold decent margins, so it's not that they're unprofitable, they're just low volume.

**A small group of customers accounts for a lot of value.** The RFM segmentation in the notebook (Part 5) shows the High Value segment is a minority of customers but responsible for a disproportionate share of total spend, the usual 80/20 pattern.

## Data cleaning summary
150 duplicate order rows and 40 rows with invalid quantity/price were dropped. 25 rows had broken date values and got removed. Category text casing was standardized ("ELECTRONICS" vs "Electronics"). Ended up with 17,935 clean rows from 18,150 raw, zero missing values left.
