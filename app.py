from flask import Flask, render_template, request, jsonify, send_file
from utils.data_fetch import get_nav_data, get_benchmark_data, search_funds
from utils.risk_metrics import calculate_risk_metrics, calculate_comprehensive_risk_metrics, calculate_simple_metrics
from utils.pdf_report import generate_pdf_report
import io

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def fund_search():
    q = request.args.get('q', '')
    return jsonify(search_funds(q))

@app.route('/dashboard', methods=['POST'])
def dashboard():
    scheme_code = request.form['scheme_code']
    start = request.form['start_date']
    end = request.form['end_date']

    # Get scheme name from the mftool
    from utils.data_fetch import mf
    try:
        scheme_name = mf.get_scheme_details(scheme_code)['scheme_name']
    except:
        scheme_name = scheme_code  # Fallback to scheme code if name not found

    fund_df = get_nav_data(scheme_code, start, end)
    bench_df = get_benchmark_data(start, end)
    metrics = calculate_comprehensive_risk_metrics(fund_df, bench_df)

    # Debug: Print data info
    print(f"Debug - scheme_code: {scheme_code}")
    print(f"Debug - date range: {start} to {end}")
    print(f"Debug - fund_df shape: {fund_df.shape}")
    print(f"Debug - fund_df columns: {fund_df.columns.tolist() if not fund_df.empty else 'Empty'}")
    print(f"Debug - first few rows: {fund_df.head() if not fund_df.empty else 'Empty'}")
    print(f"Debug - metrics: {metrics}")

    # Ensure we have valid data for the template
    if fund_df.empty:
        nav_json_data = '[]'
    else:
        # Ensure proper column names for the frontend
        fund_df_reset = fund_df.reset_index()
        if 'date' in fund_df_reset.columns and 'nav' in fund_df_reset.columns:
            nav_json_data = fund_df_reset[['date', 'nav']].to_json(orient="records", date_format="iso")
        else:
            # Try to map existing columns
            date_col = fund_df_reset.columns[0] if len(fund_df_reset.columns) > 0 else 'date'
            nav_col = fund_df_reset.columns[1] if len(fund_df_reset.columns) > 1 else 'nav'
            fund_df_mapped = fund_df_reset.rename(columns={date_col: 'date', nav_col: 'nav'})
            nav_json_data = fund_df_mapped[['date', 'nav']].to_json(orient="records", date_format="iso")
            print(f"Debug - Mapped columns: {date_col} -> date, {nav_col} -> nav")

    return render_template(
        'dashboard_simple.html',
        scheme_code=scheme_code,
        scheme_name=scheme_name,
        metrics=metrics,
        nav_json=nav_json_data,
        start=start,
        end=end
    )

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    scheme_code = request.form['scheme_code']
    start = request.form['start_date']
    end = request.form['end_date']

    # Get scheme name for the PDF
    from utils.data_fetch import mf
    try:
        scheme_name = mf.get_scheme_details(scheme_code)['scheme_name']
    except:
        scheme_name = scheme_code  # Fallback to scheme code if name not found

    fund_df = get_nav_data(scheme_code, start, end)
    bench_df = get_benchmark_data(start, end)
    metrics = calculate_comprehensive_risk_metrics(fund_df, bench_df)
    
    # Add additional metadata to metrics for PDF
    metrics['scheme_name'] = scheme_name
    metrics['start_date'] = start
    metrics['end_date'] = end

    buffer = io.BytesIO()
    generate_pdf_report(buffer, scheme_code, metrics, fund_df)
    buffer.seek(0)
    return send_file(buffer,
                     as_attachment=True,
                     download_name=f"{scheme_code}_analysis.pdf",
                     mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
