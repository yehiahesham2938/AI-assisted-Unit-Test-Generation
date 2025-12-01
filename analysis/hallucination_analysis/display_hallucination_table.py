import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import os

def load_hallucination_data():
    """Load the hallucination data from CSV."""
    file_path = os.path.join(os.path.dirname(__file__), "Hallucination&Plots", "hallucination_table.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Hallucination table not found at: {file_path}")
    return pd.read_csv(file_path)

def display_basic_info(df):
    """Display basic information about the dataset."""
    print("\n" + "="*50)
    print("HALLUCINATION TABLE ANALYSIS")
    print("="*50)
    print(f"\n📊 Dataset Overview:")
    print(f"   • Total entries: {len(df)}")
    print(f"   • Number of features: {len(df.columns)}")
    print("\n🔍 Data Types:")
    print(df.dtypes.to_string())
    
    # Display basic statistics
    print("\n📈 Basic Statistics:")
    print(df.describe().to_string())

def display_formatted_table(df):
    """Display the table in a formatted way."""
    print("\n" + "="*80)
    print("HALLUCINATION TABLE".center(80))
    print("="*80)
    
    # Display first 10 rows with nice formatting
    print(tabulate(df.head(10), headers='keys', tablefmt='grid', showindex=False))
    
    # Save to HTML for better viewing
    html_output = df.to_html(classes='table table-striped', index=False, border=0)
    html_output = f"""
    <html>
    <head>
        <title>Hallucination Table</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            .table {{ 
                width: 100%; 
                border-collapse: collapse;
                margin: 25px 0;
                font-size: 0.9em;
                min-width: 400px;
                border-radius: 5px 5px 0 0;
                overflow: hidden;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
            }}
            .table thead tr {{
                background-color: #3498db;
                color: #ffffff;
                text-align: left;
                font-weight: bold;
            }}
            .table th,
            .table td {{
                padding: 12px 15px;
            }}
            .table tbody tr {{
                border-bottom: 1px solid #dddddd;
            }}
            .table tbody tr:nth-of-type(even) {{
                background-color: #f3f3f3;
            }}
            .table tbody tr:last-of-type {{
                border-bottom: 2px solid #3498db;
            }}
        </style>
    </head>
    <body>
        <h1>Hallucination Table</h1>
        {html_output}
    </body>
    </html>
    """
    
    output_path = os.path.join(os.path.dirname(__file__), "hallucination_table.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"\n💾 Table saved as HTML: {output_path}")

def analyze_hallucination_patterns(df):
    """Analyze and visualize hallucination patterns."""
    print("\n🔍 Analyzing Hallucination Patterns...")
    
    # Create output directory for visualizations
    output_dir = os.path.join(os.path.dirname(__file__), "hallucination_analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Hallucination Type Distribution
    if 'hallucination_type' in df.columns:
        plt.figure(figsize=(10, 6))
        type_counts = df['hallucination_type'].value_counts()
        plt.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', startangle=90)
        plt.title('Distribution of Hallucination Types')
        type_chart_path = os.path.join(output_dir, 'hallucination_types.png')
        plt.savefig(type_chart_path)
        print(f"✅ Saved hallucination type distribution to: {type_chart_path}")
        plt.close()
    
    # 2. Severity Analysis
    if 'severity' in df.columns:
        plt.figure(figsize=(10, 6))
        severity_order = ['Low', 'Medium', 'High']
        sns.countplot(data=df, x='severity', order=severity_order)
        plt.title('Distribution of Hallucination Severity')
        severity_chart_path = os.path.join(output_dir, 'severity_distribution.png')
        plt.savefig(severity_chart_path)
        print(f"✅ Saved severity distribution to: {severity_chart_path}")
        plt.close()

def main():
    try:
        # Load the data
        df = load_hallucination_data()
        
        # Display basic information
        display_basic_info(df)
        
        # Display formatted table
        display_formatted_table(df)
        
        # Analyze and visualize patterns
        analyze_hallucination_patterns(df)
        
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE".center(50))
        print("="*50)
        print("\n📋 Summary:")
        print(f"1. View the complete table in: hallucination_table.html")
        print(f"2. Check visualizations in: hallucination_analysis/")
        print("\n✨ All done!")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        if 'hallucination_table' in str(e):
            print("Please ensure the hallucination table exists in the Hallucination&Plots directory.")

if __name__ == "__main__":
    main()
