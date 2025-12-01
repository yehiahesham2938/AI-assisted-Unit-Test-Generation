import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_and_analyze(file_path):
    # Load the data
    df = pd.read_csv(file_path)
    
    # Basic information
    print("\n=== Dataset Information ===")
    print(f"Number of rows: {len(df)}")
    print(f"Number of columns: {len(df.columns)}")
    
    # Display column names and data types
    print("\n=== Column Information ===")
    print(df.dtypes)
    
    # Basic statistics
    print("\n=== Basic Statistics ===")
    print(df.describe(include='all'))
    
    # Check for missing values
    print("\n=== Missing Values ===")
    print(df.isnull().sum())
    
    # Calculate hallucination rates
    if 'hallucination_type' in df.columns:
        print("\n=== Hallucination Type Distribution ===")
        print(df['hallucination_type'].value_counts(normalize=True) * 100)
    
    if 'severity' in df.columns:
        print("\n=== Severity Distribution ===")
        print(df['severity'].value_counts(normalize=True) * 100)
    
    # Calculate error rates
    error_columns = ['contains_factual_error', 'contains_irrelevant_info', 'contains_fabrication']
    if all(col in df.columns for col in error_columns):
        print("\n=== Error Rates ===")
        for col in error_columns:
            print(f"{col}: {df[col].mean()*100:.1f}%")
    
    return df

def visualize_data(df):
    # Set the style for better-looking plots
    sns.set(style="whitegrid")
    
    # Create visualizations for numeric columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    
    # Plot histograms for numeric columns
    if len(numeric_cols) > 0:
        print("\nCreating visualizations...")
        df[numeric_cols].hist(figsize=(12, 8))
        plt.tight_layout()
        plt.savefig('numeric_distributions.png')
        print("Saved numeric distributions as 'numeric_distributions.png'")
        
        # Create correlation heatmap if there are multiple numeric columns
        if len(numeric_cols) > 1:
            plt.figure(figsize=(10, 8))
            sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', center=0)
            plt.title('Correlation Heatmap')
            plt.tight_layout()
            plt.savefig('correlation_heatmap.png')
            print("Saved correlation heatmap as 'correlation_heatmap.png'")
    
    # For categorical columns, create count plots
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        if df[col].nunique() < 20:  # Only plot if not too many categories
            plt.figure(figsize=(10, 6))
            sns.countplot(y=col, data=df, order=df[col].value_counts().index)
            plt.title(f'Distribution of {col}')
            plt.tight_layout()
            plt.savefig(f'{col}_distribution.png')
            print(f"Saved {col} distribution as '{col}_distribution.png'")

def main():
    file_path = 'sample_hallucination_data.csv'
    print(f"Analyzing hallucination data from: {file_path}")
    
    try:
        # Load and analyze the data
        df = load_and_analyze(file_path)
        
        # Generate visualizations
        visualize_data(df)
        
        print("\n=== Analysis Complete ===")
        print("Check the generated plots for insights into the data.")
        
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        print("Please make sure the file exists in the current directory.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
