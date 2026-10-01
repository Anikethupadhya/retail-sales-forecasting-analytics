# Business findings

<!-- generated:business-findings:start -->
## Matched Growth

January–November 2011 positive-sales value changed by +2.90% versus the same months in 2010; units changed by -6.00%.

Population: All cleaned positive merchandise sales; all countries; 2009-12-01 through 2011-12-08.

Calculation: 100 × (current / previous − 1), calculated separately for value and units. Numerator: {'value': 'positive_sales_gbp − previous_value', 'units': 'positive_units − previous_units'}; denominator: {'value': 'previous_value', 'units': 'previous_units'}.

Full-precision inputs/results:

| Field | Value |
| --- | ---: |
| positive_sales_gbp | 8877678.989999998 |
| previous_value | 8627810.529999996 |
| positive_units | 4904971.0 |
| previous_units | 5217965.0 |
| value_growth_pct | 2.896081910134423 |
| units_growth_pct | -5.998392093469389 |

Units: {'positive_sales_gbp': 'GBP', 'positive_units': 'units', 'growth': '%'}. Display: {'GBP_decimals': 2, 'percentage_decimals': 2, 'count_decimals': 0}. Comparison periods: {'current': '2011-01-01 through 2011-11-30', 'previous': '2010-01-01 through 2010-11-30'}.

[SQL](../sql/comparable_growth.sql); [output](../outputs/sales/comparable_growth.csv), row `year=2011`, fields `positive_sales_gbp, previous_value, positive_units, previous_units, value_growth_pct, units_growth_pct`.

Limitation: Matched complete January–November periods; value and unit changes do not establish price, mix, or causal explanations.

## Value Leader

22423 (REGENCY CAKESTAND 3 TIER) led positive-sales value at £330,757.09, accounting for 1.70% of the all-merchandise total.

Population: All cleaned positive merchandise sales; all countries; 2009-12-01 through 2011-12-08.

Calculation: sum(transaction Quantity × Price); share = 100 × product value / all-merchandise value. Numerator: Product positive_sales_gbp; denominator: All-merchandise positive_sales_gbp.

Full-precision inputs/results:

| Field | Value |
| --- | ---: |
| positive_sales_gbp | 330757.09000000043 |
| all_merchandise_positive_sales_gbp | 19501670.71 |
| value_share_pct | 1.6960448923506632 |

Units: {'positive_sales_gbp': 'GBP', 'value_share_pct': '%'}. Display: {'GBP_decimals': 2, 'percentage_decimals': 2, 'count_decimals': 0}. Comparison periods: entire analysed extract.

[SQL](../sql/product_rankings.sql); [output](../outputs/sales/product_rankings.csv), row `product_id=22423`, fields `positive_sales_gbp, value_share_pct`.

Limitation: Ranking is by observed positive-sales value across the extract, not profit, net revenue, or customer preference.

## Weekday Pattern

Thursday had the highest average daily positive-sales value: £37,923.16 over 106 covered calendar days, including zero-sales dates.

Population: All cleaned positive merchandise sales; all countries; 2009-12-01 through 2011-12-08.

Calculation: weekday positive_sales_gbp / covered_calendar_days, including zero-sale dates. Numerator: weekday positive_sales_gbp; denominator: covered_calendar_days.

Full-precision inputs/results:

| Field | Value |
| --- | ---: |
| positive_sales_gbp | 4019854.759999999 |
| covered_calendar_days | 106 |
| average_daily_sales_gbp | 37923.15811320754 |

Units: {'positive_sales_gbp': 'GBP', 'covered_calendar_days': 'days', 'average_daily_sales_gbp': 'GBP/calendar day'}. Display: {'GBP_decimals': 2, 'percentage_decimals': 2, 'count_decimals': 0}. Comparison periods: entire analysed extract.

[SQL](../sql/weekday_seasonality.sql); [output](../outputs/sales/weekday_seasonality.csv), row `weekday=Thursday`, fields `positive_sales_gbp, covered_calendar_days, average_daily_sales_gbp`.

Limitation: Covered calendar days include zeros; zero observations cannot distinguish closure, missing records, or stock-outs.
<!-- generated:business-findings:end -->
