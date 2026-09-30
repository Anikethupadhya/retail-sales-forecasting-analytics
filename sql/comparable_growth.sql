-- Matched January-November periods: 2010 versus 2011. Partial December excluded.
WITH totals AS (
    SELECT YEAR(c.date) AS year, COUNT(DISTINCT c.month_start) AS covered_months,
           BOOL_AND(c.complete_month) AS complete_period, SUM(d.units) AS positive_units,
           SUM(d.positive_sales_gbp) AS positive_sales_gbp
    FROM calendar c JOIN daily_totals d USING (date)
    WHERE MONTH(c.date) BETWEEN 1 AND 11
    GROUP BY YEAR(c.date)
), complete AS (
    SELECT * FROM totals WHERE covered_months = 11 AND complete_period
), previous AS (
    SELECT *, LAG(year) OVER (ORDER BY year) AS previous_year,
           LAG(positive_sales_gbp) OVER (ORDER BY year) AS previous_value,
           LAG(positive_units) OVER (ORDER BY year) AS previous_units
    FROM complete
)
SELECT *, CASE WHEN year=previous_year+1 THEN 100*(positive_sales_gbp-previous_value)/NULLIF(previous_value,0) END AS value_growth_pct,
          CASE WHEN year=previous_year+1 THEN 100*(positive_units-previous_units)/NULLIF(previous_units,0) END AS units_growth_pct
FROM previous ORDER BY year;
