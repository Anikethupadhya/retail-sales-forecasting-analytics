import pandas as pd
import pytest
from src.common import OUT
from src.analytics import build_sales_database


@pytest.fixture
def saved_sales_database(tmp_path):
    """Committed customer-free aggregates are inputs; the database is always fresh."""
    sales = pd.read_parquet(OUT/'sales/product_daily_sales.parquet')
    metadata = pd.read_csv(OUT/'sales/product_metadata.csv',dtype={'product_id':str})
    calendar = pd.read_csv(OUT/'sales/calendar.csv',parse_dates=['date','month_start'])
    database = tmp_path/'sales.duckdb'
    build_sales_database(sales,metadata,calendar,database_path=database,output_dir=tmp_path/'sql-results')
    return database
