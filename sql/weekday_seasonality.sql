-- Calendar-day denominator includes zero-sale days; totals alone weight weekdays unequally.
SELECT c.weekday_number, c.weekday, COUNT(*) AS covered_calendar_days,
       SUM(d.units) AS positive_units, AVG(d.units) AS average_daily_units,
       SUM(d.positive_sales_gbp) AS positive_sales_gbp,
       AVG(d.positive_sales_gbp) AS average_daily_sales_gbp
FROM calendar c JOIN daily_totals d USING (date)
GROUP BY c.weekday_number, c.weekday ORDER BY c.weekday_number;
