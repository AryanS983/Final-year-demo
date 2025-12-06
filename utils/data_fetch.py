import pandas as pd
from mftool import Mftool
import yfinance as yf

mf = Mftool()

def search_funds(query: str):
    """Return (scheme_code, scheme_name) pairs matching the query."""
    all_funds = mf.get_scheme_codes()
    return [(code, name) for code, name in all_funds.items()
            if query.lower() in name.lower()]

def get_nav_data(scheme_code, start_date, end_date):
    try:
        # Convert date strings to datetime objects for proper filtering
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        print(f"Fetching NAV data for scheme {scheme_code} from {start_date} to {end_date}")
        
        data = mf.get_scheme_historical_nav(scheme_code, start_date, end_date)
        
        # Handle different data formats that might be returned
        if isinstance(data, dict):
            # If data is a dict with 'data' key containing the actual records
            if 'data' in data and isinstance(data['data'], list):
                records = data['data']
            else:
                # Convert dict to list of records
                records = list(data.values()) if data else []
        elif isinstance(data, list):
            records = data
        else:
            records = []
        
        # Ensure we have valid records
        if not records:
            print(f"No data returned for scheme {scheme_code}")
            return pd.DataFrame(columns=['date', 'nav'])
        
        # Create DataFrame from records
        df = pd.DataFrame(records)
        
        # Ensure required columns exist
        if 'date' not in df.columns or 'nav' not in df.columns:
            print(f"Missing required columns in data for scheme {scheme_code}. Available columns: {df.columns.tolist()}")
            return pd.DataFrame(columns=['date', 'nav'])
        
        # Convert data types
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
        
        # Remove rows with invalid dates or nav values
        df = df.dropna(subset=['date', 'nav'])
        
        # Ensure data is within the requested date range
        df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
        
        print(f"Successfully retrieved {len(df)} records for scheme {scheme_code} within date range")
        return df.sort_values('date')
        
    except Exception as e:
        print(f"Error fetching NAV data for scheme {scheme_code}: {str(e)}")
        return pd.DataFrame(columns=['date', 'nav'])

def get_benchmark_data(start_date, end_date):
    try:
        # Nifty 50 TRI via Yahoo Finance
        idx = yf.download("^NSEI", start=start_date, end=end_date)
        
        # Handle multi-level columns that yfinance might return
        if isinstance(idx.columns, pd.MultiIndex):
            # Flatten multi-level columns
            idx.columns = idx.columns.droplevel(1) if len(idx.columns.levels) > 1 else idx.columns.get_level_values(0)
        
        # Handle different column names that might be returned
        if 'Adj Close' in idx.columns:
            idx = idx[['Adj Close']].rename(columns={'Adj Close': 'benchmark'})
        elif 'Close' in idx.columns:
            idx = idx[['Close']].rename(columns={'Close': 'benchmark'})
        else:
            # If neither Adj Close nor Close is available, use the first numeric column
            numeric_cols = idx.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                idx = idx[[numeric_cols[0]]].rename(columns={numeric_cols[0]: 'benchmark'})
            else:
                print("No price data available in benchmark data")
                return pd.DataFrame(columns=['date', 'benchmark'])
        
        idx.reset_index(inplace=True)
        idx.rename(columns={'Date': 'date'}, inplace=True)
        
        print(f"Successfully retrieved {len(idx)} benchmark records")
        return idx
        
    except Exception as e:
        print(f"Error fetching benchmark data: {str(e)}")
        return pd.DataFrame(columns=['date', 'benchmark'])
