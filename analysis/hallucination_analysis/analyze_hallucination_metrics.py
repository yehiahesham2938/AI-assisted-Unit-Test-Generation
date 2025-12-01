import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Set style for visualizations
plt.style.use('seaborn')
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica', 'sans-serif']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'

def load_data():
    """Load the hallucination data."""
    file_path = os.path.join("Hallucination&Plots", "hallucination_data.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Hallucination table not found at: {file_path}")
    
    # Check if the file contains actual data or code
    with open(file_path, 'r') as f:
        first_line = f.readline().strip()
    
    if 'import pandas' in first_line:
        print("⚠ The file appears to contain Python code. Please ensure you're using the correct data file.")
        print("The file should contain tabular data, not Python code.")
        return None
    
    return pd.read_csv(file_path)

def generate_report(df):
    """Generate a comprehensive analysis report."""
    # Create output directory
    output_dir = "hallucination_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # Start HTML report with simplified styling
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Hallucination Metrics Analysis</title>
        <style>
            body { 
                font-family: Arial, Helvetica, sans-serif; 
                line-height: 1.6; 
                margin: 20px;
                color: #333;
            }
            h1, h2, h3 { color: #2c3e50; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { 
                background: #fff; 
                border-radius: 5px; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
                padding: 20px; 
                margin-bottom: 20px;
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 15px 0;
            }
            th, td { 
                padding: 10px; 
                text-align: left; 
                border-bottom: 1px solid #ddd;
            }
            th { 
                background-color: #f4f4f4; 
                font-weight: bold;
            }
            .warning { color: #e74c3c; font-weight: bold; }
            .success { color: #27ae60; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hallucination Metrics Analysis</h1>
            <p>Report generated on: {date}</p>
    """.format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 1. Dataset Overview
    html_content += """
    <div class="card">
        <h2>1. Dataset Overview</h2>
        <p>Total Rows: {rows:,}</p>
        <p>Total Columns: {cols}</p>
        <p>Columns: {columns}</p>
    </div>
    """.format(
        rows=len(df),
        cols=len(df.columns),
        columns=", ".join([f'<code>{col}</code>' for col in df.columns])
    )
    
    # 2. Data Types
    html_content += """
    <div class="card">
        <h2>2. Data Types</h2>
        <table>
            <tr><th>Column</th><th>Data Type</th><th>Non-Null Count</th></tr>
    """
    
    for col in df.columns:
        html_content += f"""
        <tr>
            <td><code>{col}</code></td>
            <td>{df[col].dtype}</td>
            <td>{df[col].count():,} ({(df[col].count()/len(df)*100):.1f}%)</td>
        </tr>
        """
    html_content += "</table></div>"
    
    # 3. Basic Statistics
    html_content += """
    <div class="card">
        <h2>3. Basic Statistics</h2>
        <h3>Numeric Columns</h3>
        {numeric_stats}
        <h3>Categorical Columns</h3>
        {categorical_stats}
    </div>
    """.format(
        numeric_stats=df.describe().to_html(classes='dataframe', border=0) if not df.select_dtypes(include=['number']).empty else "<p>No numeric columns found.</p>",
        categorical_stats=df.describe(include=['object']).to_html(classes='dataframe', border=0) if not df.select_dtypes(include=['object']).empty else "<p>No categorical columns found.</p>"
    )
    
    # 4. Missing Values
    missing = df.isnull().sum()
    html_content += f"""
    <div class="card">
        <h2>4. Data Quality Check</h2>
        <h3>Missing Values</h3>
        <table>
            <tr><th>Column</th><th>Missing Values</th><th>% Missing</th></tr>
    """
    
    for col in df.columns:
        missing_pct = (missing[col] / len(df)) * 100
        missing_class = 'warning' if missing_pct > 0 else 'success'
        html_content += f"""
        <tr>
            <td><code>{col}</code></td>
            <td class="{missing_class}">{missing[col]:,}</td>
            <td class="{missing_class}">{missing_pct:.1f}%</td>
        </tr>
        """
    html_content += "</table>"
    
    # 5. Unique Values
    html_content += """
        <h3>Unique Values</h3>
        <table>
            <tr><th>Column</th><th>Unique Values</th><th>% Unique</th></tr>
    """
    
    for col in df.columns:
        unique_pct = (df[col].nunique() / len(df)) * 100
        html_content += f"""
        <tr>
            <td><code>{col}</code></td>
            <td>{df[col].nunique():,}</td>
            <td>{unique_pct:.1f}%</td>
        </tr>
        """
    html_content += "</table></div>"
    
    # 6. Visualizations
    if not df.select_dtypes(include=['number']).empty:
        # Set a clean style for visualizations
        plt.style.use('seaborn')
        
        # Numeric columns distribution
        num_cols = df.select_dtypes(include=['number']).columns
        for col in num_cols:
            try:
                plt.figure(figsize=(10, 6))
                sns.histplot(data=df, x=col, kde=True)
                plt.title(f'Distribution of {col}')
                plot_path = os.path.join(output_dir, f'dist_{col}.png')
                plt.tight_layout()
                plt.savefig(plot_path, bbox_inches='tight')
                plt.close()
                html_content += f"""
                <div class="card">
                    <h3>Distribution of {col}</h3>
                    <img src="{plot_path}" alt="Distribution of {col}" style="max-width: 100%;">
                </div>
                """
            except Exception as e:
                print(f"⚠ Could not create plot for {col}: {str(e)}")
        
        # Create correlation heatmap
        try:
            plt.figure(figsize=(12, 8))
            corr = df.select_dtypes(include=['number']).corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, fmt='.2f')
            plt.title('Correlation Heatmap')
            heatmap_path = os.path.join(output_dir, 'correlation_heatmap.png')
            plt.tight_layout()
            plt.savefig(heatmap_path, bbox_inches='tight')
            plt.close()
            
            html_content += f"""
            <div class="card">
                <h3>Correlation Heatmap</h3>
                <img src="{heatmap_path}" alt="Correlation Heatmap" style="max-width: 100%;">
            </div>
            """
        except Exception as e:
            print(f"⚠ Could not create correlation heatmap: {str(e)}")
            
        # Categorical analysis
        if 'hallucination_type' in df.columns:
            try:
                plt.figure(figsize=(10, 6))
                sns.countplot(data=df, y='hallucination_type', order=df['hallucination_type'].value_counts().index)
                plt.title('Hallucination Type Distribution')
                type_path = os.path.join(output_dir, 'hallucination_types.png')
                plt.tight_layout()
                plt.savefig(type_path, bbox_inches='tight')
                plt.close()
                
                html_content += f"""
                <div class="card">
                    <h3>Hallucination Type Distribution</h3>
                    <img src="{type_path}" alt="Hallucination Type Distribution" style="max-width: 100%;">
                </div>
                """
            except Exception as e:
                print(f"⚠ Could not create hallucination type plot: {str(e)}")
    
    # Close HTML
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # Save HTML report
    report_path = os.path.join(output_dir, 'hallucination_analysis_report.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return report_path

def main():
    print("🔍 Starting hallucination metrics analysis...")
    
    try:
        # Load data
        print("📊 Loading data...")
        df = load_data()
        
        if df is not None:
            # Generate report
            print("📈 Analyzing data...")
            report_path = generate_report(df)
            
            print("\n✅ Analysis complete!")
            print(f"📄 Report generated at: {os.path.abspath(report_path)}")
            
            # Open the report in the default web browser
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(report_path)}')
    
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        if 'No such file or directory' in str(e):
            print("Please ensure the data file exists in the correct location.")
        elif 'utf-8' in str(e).lower():
            print("There might be an encoding issue with the file. Try saving it as UTF-8.")

if __name__ == "__main__":
    main()
