import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

def calculate_comprehensive_risk_metrics(fund_df, bench_df, risk_free=0.06):
    """
    Calculate comprehensive risk metrics for mutual fund analysis
    """
    # Debug: Check data structure
    print(f"Fund data shape: {fund_df.shape}, columns: {fund_df.columns.tolist()}")
    print(f"Benchmark data shape: {bench_df.shape}, columns: {bench_df.columns.tolist()}")
    
    # Ensure both DataFrames have the required columns and proper structure
    if fund_df.empty or bench_df.empty:
        print("Warning: Empty DataFrame provided")
        return get_default_metrics()
    
    # Check for required columns
    if 'date' not in fund_df.columns or 'nav' not in fund_df.columns:
        print("Warning: Fund data missing required columns")
        return get_default_metrics()
    
    if 'date' not in bench_df.columns or 'benchmark' not in bench_df.columns:
        print("Warning: Benchmark data missing required columns")
        return get_default_metrics()
    
    # Ensure date columns are datetime type
    fund_df['date'] = pd.to_datetime(fund_df['date'], errors='coerce')
    bench_df['date'] = pd.to_datetime(bench_df['date'], errors='coerce')
    
    # Merge on date
    df = pd.merge(fund_df, bench_df, on='date', how='inner')
    
    if df.empty:
        print("Warning: No overlapping dates between fund and benchmark data")
        return get_default_metrics()
    
    # Calculate returns
    df['fund_ret'] = np.log(df['nav'] / df['nav'].shift(1))
    df['bench_ret'] = np.log(df['benchmark'] / df['benchmark'].shift(1))
    df.dropna(inplace=True)
    
    if len(df) < 2:
        print("Warning: Insufficient data points for risk calculation")
        return get_default_metrics()

    # Basic risk metrics
    X = df['bench_ret'].values.reshape(-1, 1)
    y = df['fund_ret'].values
    reg = LinearRegression().fit(X, y)
    beta = reg.coef_[0]
    alpha = reg.intercept_ * 252  # annualised
    r2 = reg.score(X, y)

    std_dev = df['fund_ret'].std() * np.sqrt(252)
    mean_return = df['fund_ret'].mean() * 252
    sharpe = (mean_return - risk_free) / std_dev

    # Comprehensive risk analysis
    # Positive/Negative days calculation
    daily_returns = df['fund_ret'].values
    positive_days = len(daily_returns[daily_returns > 0])
    negative_days = len(daily_returns[daily_returns < 0])
    total_days = len(daily_returns)
    
    # Volatility analysis
    monthly_vol = df['fund_ret'].rolling(window=21).std().mean() * np.sqrt(252)
    max_daily_gain = df['fund_ret'].max()
    max_daily_loss = df['fund_ret'].min()
    
    # Downside risk metrics
    downside_returns = daily_returns[daily_returns < 0]
    downside_deviation = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
    
    # Sortino Ratio
    sortino_ratio = (mean_return - risk_free) / downside_deviation if downside_deviation > 0 else 0
    
    # Maximum Drawdown
    cumulative_returns = (1 + df['fund_ret']).cumprod()
    rolling_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    # Value at Risk (VaR) - 95% confidence
    var_95 = np.percentile(daily_returns, 5)
    
    # Conditional Value at Risk (CVaR) - Expected Shortfall
    cvar_95 = daily_returns[daily_returns <= var_95].mean() if len(daily_returns[daily_returns <= var_95]) > 0 else 0
    
    # Tracking Error and Information Ratio
    tracking_error = np.std(df['fund_ret'] - df['bench_ret']) * np.sqrt(252)
    information_ratio = alpha / tracking_error if tracking_error > 0 else 0
    
    # Risk-Adjusted Return Ratios
    calmar_ratio = mean_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # Risk classification
    risk_level = classify_risk_level(std_dev, max_drawdown, sharpe, beta)
    
    # Benchmark comparison
    benchmark_comparison = calculate_benchmark_comparison(df, mean_return, std_dev, sharpe)
    
    # Calculate Total Return % and NAV values
    start_nav = df['nav'].iloc[0] if len(df) > 0 else 0
    end_nav = df['nav'].iloc[-1] if len(df) > 0 else 0
    total_return_pct = ((end_nav - start_nav) / start_nav * 100) if start_nav > 0 else 0
    
    return {
        # Basic Risk Metrics
        "Alpha": round(alpha, 3),
        "Beta": round(beta, 3),
        "R-squared": round(r2, 3),
        "Standard Deviation": round(std_dev, 3),
        "Sharpe Ratio": round(sharpe, 3),
        
        # NAV and Return Metrics (Missing from original)
        "Start NAV": round(start_nav, 2),
        "End NAV": round(end_nav, 2),
        "Total Return %": round(total_return_pct, 2),
        
        # Comprehensive Risk Metrics
        "Positive Days": positive_days,
        "Negative Days": negative_days,
        "Positive Days %": round((positive_days / total_days) * 100, 2),
        "Negative Days %": round((negative_days / total_days) * 100, 2),
        "Total Trading Days": total_days,
        
        # Advanced Risk Metrics - Fixed key names to match template
        "Max Daily Gain %": round(max_daily_gain * 100, 2),
        "Max Daily Loss %": round(max_daily_loss * 100, 2),
        "Daily Volatility %": round(df['fund_ret'].std() * 100, 2),  # Daily volatility (without annualization)
        "Annual Volatility %": round(std_dev * 100, 2),  # Annual volatility (already annualized)
        "Downside Deviation": round(downside_deviation, 3),
        "Sortino Ratio": round(sortino_ratio, 3),
        "Maximum Drawdown %": round(max_drawdown * 100, 2),
        "Value at Risk (95%) %": round(var_95 * 100, 2),
        "Conditional VaR (95%) %": round(cvar_95 * 100, 2),
        "Tracking Error": round(tracking_error, 3),
        "Information Ratio": round(information_ratio, 3),
        "Calmar Ratio": round(calmar_ratio, 3),
        "Monthly Volatility %": round(monthly_vol * 100, 2),
        
        # Risk Assessment
        "Risk Level": risk_level,
        "Risk Score": calculate_risk_score(std_dev, max_drawdown, sharpe, beta),
        
        # Benchmark Comparison
        "Benchmark Comparison": benchmark_comparison,
        "Outperformed Benchmark": mean_return > df['bench_ret'].mean() * 252
    }

def get_default_metrics():
    """Return default metrics when data is insufficient"""
    return {
        "Alpha": 0.0,
        "Beta": 0.0,
        "R-squared": 0.0,
        "Standard Deviation": 0.0,
        "Sharpe Ratio": 0.0,
        
        # NAV and Return Metrics (Missing from original)
        "Start NAV": 0.0,
        "End NAV": 0.0,
        "Total Return %": 0.0,
        
        "Positive Days": 0,
        "Negative Days": 0,
        "Positive Days %": 0.0,
        "Negative Days %": 0.0,
        "Total Trading Days": 0,
        "Max Daily Gain %": 0.0,
        "Max Daily Loss %": 0.0,
        "Daily Volatility %": 0.0,
        "Annual Volatility %": 0.0,
        "Downside Deviation": 0.0,
        "Sortino Ratio": 0.0,
        "Maximum Drawdown %": 0.0,
        "Value at Risk (95%) %": 0.0,
        "Conditional VaR (95%) %": 0.0,
        "Tracking Error": 0.0,
        "Information Ratio": 0.0,
        "Calmar Ratio": 0.0,
        "Monthly Volatility %": 0.0,
        "Risk Level": "Unknown",
        "Risk Score": 0.0,
        "Benchmark Comparison": {},
        "Outperformed Benchmark": False
    }

def classify_risk_level(std_dev, max_drawdown, sharpe, beta):
    """Classify risk level based on multiple factors"""
    risk_score = 0
    
    # Volatility risk (40% weight)
    if std_dev > 0.25: risk_score += 4
    elif std_dev > 0.18: risk_score += 3
    elif std_dev > 0.12: risk_score += 2
    else: risk_score += 1
    
    # Drawdown risk (30% weight)
    if abs(max_drawdown) > 0.25: risk_score += 3
    elif abs(max_drawdown) > 0.15: risk_score += 2
    else: risk_score += 1
    
    # Sharpe ratio (20% weight)
    if sharpe < 0.5: risk_score += 2
    elif sharpe < 1.0: risk_score += 1
    else: risk_score += 0
    
    # Beta risk (10% weight)
    if beta > 1.2: risk_score += 1
    elif beta < 0.8: risk_score += 1
    
    avg_risk_score = risk_score / 4
    
    if avg_risk_score >= 3: return "High Risk"
    elif avg_risk_score >= 2: return "Medium Risk"
    else: return "Low Risk"

def calculate_risk_score(std_dev, max_drawdown, sharpe, beta):
    """Calculate numerical risk score (1-10 scale)"""
    score = 0
    
    # Volatility component (40%)
    vol_score = min(std_dev * 20, 4)  # Cap at 4
    
    # Drawdown component (30%)
    dd_score = min(abs(max_drawdown) * 12, 3)  # Cap at 3
    
    # Sharpe component (20%)
    sharpe_score = max(2 - sharpe, 0)  # Lower Sharpe = higher risk
    
    # Beta component (10%)
    beta_score = abs(beta - 1) * 2.5  # Deviation from 1
    
    total_score = vol_score + dd_score + sharpe_score + beta_score
    return round(min(total_score, 10), 2)

def calculate_benchmark_comparison(df, fund_return, fund_vol, fund_sharpe):
    """Compare fund performance with benchmark"""
    bench_return = df['bench_ret'].mean() * 252
    bench_vol = df['bench_ret'].std() * np.sqrt(252)
    bench_sharpe = (bench_return - 0.06) / bench_vol if bench_vol > 0 else 0
    
    return {
        "Fund Return %": round(fund_return * 100, 2),
        "Benchmark Return %": round(bench_return * 100, 2),
        "Return Difference %": round((fund_return - bench_return) * 100, 2),
        "Fund Volatility %": round(fund_vol * 100, 2),
        "Benchmark Volatility %": round(bench_vol * 100, 2),
        "Volatility Difference %": round((fund_vol - bench_vol) * 100, 2),
        "Fund Sharpe": round(fund_sharpe, 3),
        "Benchmark Sharpe": round(bench_sharpe, 3),
        "Sharpe Difference": round(fund_sharpe - bench_sharpe, 3)
    }

# Keep the original function for backward compatibility
def calculate_risk_metrics(fund_df, bench_df, risk_free=0.06):
    """Original function for backward compatibility"""
    metrics = calculate_comprehensive_risk_metrics(fund_df, bench_df, risk_free)
    
    # Return only the basic metrics for compatibility
    return {
        "Alpha": metrics["Alpha"],
        "Beta": metrics["Beta"],
        "R-squared": metrics["R-squared"],
        "Standard Deviation": metrics["Standard Deviation"],
        "Sharpe Ratio": metrics["Sharpe Ratio"]
    }

def calculate_simple_metrics(fund_df, bench_df=None):
    """
    Calculate simple, industry-standard metrics for basic analysis
    No complex risk calculations - just basic statistics
    """
    if fund_df.empty or 'date' not in fund_df.columns or 'nav' not in fund_df.columns:
        return get_simple_default_metrics()
    
    # Ensure date is datetime
    fund_df['date'] = pd.to_datetime(fund_df['date'], errors='coerce')
    fund_df = fund_df.dropna()
    
    if len(fund_df) < 2:
        return get_simple_default_metrics()
    
    # Sort by date
    fund_df = fund_df.sort_values('date')
    
    # Calculate daily returns
    fund_df['daily_return'] = fund_df['nav'].pct_change()
    fund_df = fund_df.dropna()
    
    if len(fund_df) < 2:
        return get_simple_default_metrics()
    
    # Basic calculations
    start_nav = fund_df['nav'].iloc[0]
    end_nav = fund_df['nav'].iloc[-1]
    total_return = ((end_nav - start_nav) / start_nav) * 100
    
    # Positive/Negative days
    positive_days = len(fund_df[fund_df['daily_return'] > 0])
    negative_days = len(fund_df[fund_df['daily_return'] < 0])
    total_days = len(fund_df)
    
    # Volatility (simple standard deviation of daily returns)
    daily_volatility = fund_df['daily_return'].std() * 100
    annualized_volatility = daily_volatility * np.sqrt(252)  # 252 trading days in a year
    
    # Basic risk metrics
    max_daily_gain = fund_df['daily_return'].max() * 100
    max_daily_loss = fund_df['daily_return'].min() * 100
    
    # Investment period
    days_period = (fund_df['date'].iloc[-1] - fund_df['date'].iloc[0]).days
    
    return {
        "Total Return %": round(total_return, 2),
        "Positive Days": positive_days,
        "Negative Days": negative_days,
        "Positive Days %": round((positive_days / total_days) * 100, 2),
        "Negative Days %": round((negative_days / total_days) * 100, 2),
        "Daily Volatility %": round(daily_volatility, 2),
        "Annual Volatility %": round(annualized_volatility, 2),
        "Max Daily Gain %": round(max_daily_gain, 2),
        "Max Daily Loss %": round(max_daily_loss, 2),
        "Start NAV": round(start_nav, 2),
        "End NAV": round(end_nav, 2),
        "Trading Days": total_days,
        "Period (Days)": days_period,
        "Data Quality": "Good" if total_days > 20 else "Limited"
    }

def get_simple_default_metrics():
    """Return simple default metrics when data is insufficient"""
    return {
        "Total Return %": 0.0,
        "Positive Days": 0,
        "Negative Days": 0,
        "Positive Days %": 0.0,
        "Negative Days %": 0.0,
        "Daily Volatility %": 0.0,
        "Annual Volatility %": 0.0,
        "Max Daily Gain %": 0.0,
        "Max Daily Loss %": 0.0,
        "Start NAV": 0.0,
        "End NAV": 0.0,
        "Trading Days": 0,
        "Period (Days)": 0,
        "Data Quality": "No Data"
    }
