import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime

def create_charts(df, metrics):
    """Create charts for the PDF report"""
    charts = {}
    
    # NAV Chart
    fig, ax = plt.subplots(figsize=(10, 4))
    if not df.empty and 'nav' in df.columns:
        dates = df.index if hasattr(df.index, 'date') else range(len(df))
        ax.plot(dates, df['nav'], color='#667eea', linewidth=2, marker='o', markersize=3)
        ax.set_title('NAV Performance', fontsize=14, fontweight='bold', color='#2d3748')
        ax.set_ylabel('NAV (₹)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Save to bytes
        nav_buffer = BytesIO()
        plt.savefig(nav_buffer, format='png', bbox_inches='tight', dpi=150)
        nav_buffer.seek(0)
        charts['nav'] = nav_buffer
    plt.close()
    
    # Volatility Chart
    fig, ax = plt.subplots(figsize=(6, 4))
    volatilities = ['Daily Vol', 'Annual Vol']
    values = [metrics.get('Daily Volatility %', 0), metrics.get('Annual Volatility %', 0)]
    colors_bar = ['#10b981', '#f59e0b']
    
    bars = ax.bar(volatilities, values, color=colors_bar, alpha=0.8)
    ax.set_title('Volatility Analysis', fontsize=14, fontweight='bold', color='#2d3748')
    ax.set_ylabel('Volatility (%)', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{value:.2f}%', ha='center', va='bottom', fontweight='bold')
    
    vol_buffer = BytesIO()
    plt.savefig(vol_buffer, format='png', bbox_inches='tight', dpi=150)
    vol_buffer.seek(0)
    charts['volatility'] = vol_buffer
    plt.close()
    
    # Days Pie Chart
    fig, ax = plt.subplots(figsize=(6, 6))
    positive_days = metrics.get('Positive Days', 0)
    negative_days = metrics.get('Negative Days', 0)
    
    if positive_days + negative_days > 0:
        sizes = [positive_days, negative_days]
        labels = [f'Positive\n{positive_days} days', f'Negative\n{negative_days} days']
        colors_pie = ['#10b981', '#ef4444']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_pie, 
                                         autopct='%1.1f%%', startangle=90)
        ax.set_title('Good Days vs Bad Days', fontsize=14, fontweight='bold', color='#2d3748')
        
        # Style the text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    pie_buffer = BytesIO()
    plt.savefig(pie_buffer, format='png', bbox_inches='tight', dpi=150)
    pie_buffer.seek(0)
    charts['pie'] = pie_buffer
    plt.close()
    
    return charts

def create_metric_card(title, value, subtitle=None, color='#2d3748'):
    """Create a styled metric card"""
    card_content = f"""
    <para align="center" fontSize="10" textColor="#4a5568" fontName="Helvetica-Bold">
        {title}
    </para>
    <para align="center" fontSize="16" textColor="{color}" fontName="Helvetica-Bold">
        {value}
    </para>
    """
    if subtitle:
        card_content += f'<para align="center" fontSize="8" textColor="#666666">{subtitle}</para>'
    
    return card_content

def generate_pdf_report(buffer, scheme_code, metrics, df):
    """Generate a comprehensive PDF report matching dashboard appearance"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Custom styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor='#2d3748',
        alignment=TA_CENTER,
        spaceAfter=30,
        fontName='Helvetica-Bold'
    )
    
    # Header style
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#2d3748',
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    # Normal text
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#4a5568',
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    story = []
    
    # Header Section
    story.append(Paragraph("Mutual Fund Risk Analysis Report", title_style))
    
    # Fund Information Card (matching dashboard style)
    scheme_name = metrics.get('scheme_name', scheme_code)
    start_date = metrics.get('start_date', 'N/A')
    end_date = metrics.get('end_date', 'N/A')
    
    # Create fund info with separate paragraphs
    story.append(Paragraph(f"<para align='center' fontSize='14' textColor='#2d3748' fontName='Helvetica-Bold'>{scheme_name}</para>", normal_style))
    story.append(Paragraph(f"<para align='center' fontSize='10' textColor='#4a5568'>Scheme Code: {scheme_code}</para>", normal_style))
    story.append(Paragraph(f"<para align='center' fontSize='12' textColor='#2d3748' fontName='Helvetica-Bold'>Analysis Period: {start_date} to {end_date}</para>", normal_style))
    story.append(Paragraph(f"<para align='center' fontSize='10' textColor='#4a5568'>Analyzing {metrics.get('Total Trading Days', 0)} trading days</para>", normal_style))
    story.append(Spacer(1, 20))
    
    # Key Metrics Summary
    story.append(Paragraph("Analysis Summary", header_style))
    
    # Create summary table (matching dashboard cards)
    summary_data = [
        ['Total Return', f"{metrics.get('Total Return %', 0)}%", 'NAV Change', f"₹{metrics.get('Start NAV', 0)} → ₹{metrics.get('End NAV', 0)}"],
        ['Trading Days', f"{metrics.get('Total Trading Days', 0)} days", 'Positive Days', f"{metrics.get('Positive Days', 0)} ({metrics.get('Positive Days %', 0)}%)"]
    ]
    
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4a5568')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROUNDEDCORNERS', [6, 6, 6, 6])
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Risk Ratios Section
    story.append(Paragraph("Industry Standard Risk Ratios", header_style))
    
    # Risk ratios in a grid (matching dashboard cards)
    risk_data = [
        ['Sharpe Ratio', f"{metrics.get('Sharpe Ratio', 0):.2f}", 'Sortino Ratio', f"{metrics.get('Sortino Ratio', 0):.2f}"],
        ['Beta', f"{metrics.get('Beta', 0):.2f}", 'Alpha', f"{metrics.get('Alpha', 0):.2f}%"],
        ['Information Ratio', f"{metrics.get('Information Ratio', 0):.2f}", 'Calmar Ratio', f"{metrics.get('Calmar Ratio', 0):.2f}"]
    ]
    
    risk_table = Table(risk_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROUNDEDCORNERS', [6, 6, 6, 6])
    ]))
    
    story.append(risk_table)
    story.append(Spacer(1, 20))
    
    # Volatility Analysis
    story.append(Paragraph("Volatility Analysis", header_style))
    
    vol_data = [
        ['Daily Volatility', f"{metrics.get('Daily Volatility %', 0)}%", 'Annual Volatility', f"{metrics.get('Annual Volatility %', 0)}%"],
        ['Best Day', f"+{metrics.get('Max Daily Gain %', 0)}%", 'Worst Day', f"{metrics.get('Max Daily Loss %', 0)}%"]
    ]
    
    vol_table = Table(vol_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    vol_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4a5568')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROUNDEDCORNERS', [6, 6, 6, 6])
    ]))
    
    story.append(vol_table)
    story.append(Spacer(1, 20))
    
    # Risk Assessment
    vol_level = metrics.get('Annual Volatility %', 0)
    if vol_level < 12:
        risk_color = '#10b981'
        risk_text = 'Low Risk: Stable fund with predictable returns. Suitable for conservative investors.'
    elif vol_level < 18:
        risk_color = '#f59e0b'
        risk_text = 'Medium Risk: Moderate price swings. Good for balanced portfolios.'
    else:
        risk_color = '#ef4444'
        risk_text = 'High Risk: Significant price fluctuations. For aggressive investors only.'
    
    story.append(Paragraph(f"<para align='center' fontSize='12' textColor='{risk_color}' fontName='Helvetica-Bold'>Risk Assessment</para>", normal_style))
    story.append(Paragraph(f"<para align='center' fontSize='10' textColor='#4a5568'>{risk_text}</para>", normal_style))
    story.append(Spacer(1, 30))
    
    # Add charts if data is available
    if not df.empty:
        story.append(PageBreak())
        story.append(Paragraph("Charts & Visualizations", header_style))
        story.append(Spacer(1, 20))
        
        charts = create_charts(df, metrics)
        
        # Add NAV Chart
        if 'nav' in charts:
            story.append(Paragraph("NAV Performance", header_style))
            story.append(Image(charts['nav'], width=6*inch, height=2.4*inch))
            story.append(Spacer(1, 20))
        
        # Add Volatility Chart
        if 'volatility' in charts:
            story.append(Paragraph("Volatility Analysis", header_style))
            story.append(Image(charts['volatility'], width=3.6*inch, height=2.4*inch))
            story.append(Spacer(1, 20))
        
        # Add Pie Chart
        if 'pie' in charts:
            story.append(Paragraph("Good Days vs Bad Days", header_style))
            story.append(Image(charts['pie'], width=3.6*inch, height=3.6*inch))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("<para align='center' fontSize='8' textColor='#718096'>This report is generated for informational purposes only and should not be considered as investment advice.</para>", normal_style))
    story.append(Paragraph("<para align='center' fontSize='8' textColor='#718096'>Please consult with a financial advisor before making investment decisions.</para>", normal_style))
    
    doc.build(story)
