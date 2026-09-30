-- Complete means all calendar days lie within observed extract coverage.
WITH monthly AS (
    SELECT c.month_start, COUNT(*) AS covered_calendar_days, BOOL_AND(c.complete_month) AS complete_month,
           SUM(d.units) AS positive_units, SUM(d.positive_sales_gbp) AS positive_sales_gbp
    FROM calendar c JOIN daily_totals d USING (date) GROUP BY c.month_start
), previous AS (
    SELECT *, LAG(month_start) OVER (ORDER BY month_start) AS previous_month,
           LAG(complete_month) OVER (ORDER BY month_start) AS previous_complete,
           LAG(positive_sales_gbp) OVER (ORDER BY month_start) AS previous_value
    FROM monthly
)
SELECT *, CASE WHEN complete_month AND previous_complete AND DATE_DIFF('month', previous_month, month_start)=1
               THEN 100 * (positive_sales_gbp - previous_value) / NULLIF(previous_value, 0)
          END AS comparable_monthly_growth_pct
FROM previous ORDER BY month_start;
