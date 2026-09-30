-- Scope: all cleaned merchandise, all covered dates. Positive-sales value is GBP.
WITH totals AS (
    SELECT product_id, SUM(units) AS positive_units, SUM(positive_sales_gbp) AS positive_sales_gbp,
           SUM(transaction_lines) AS retained_lines, COUNT(*) AS active_calendar_days
    FROM sales GROUP BY product_id
)
SELECT t.*, p.description,
       DENSE_RANK() OVER (ORDER BY positive_units DESC) AS units_rank,
       DENSE_RANK() OVER (ORDER BY positive_sales_gbp DESC) AS value_rank,
       100 * positive_sales_gbp / SUM(positive_sales_gbp) OVER () AS value_share_pct
FROM totals t JOIN product_metadata p USING (product_id)
ORDER BY units_rank, product_id;
