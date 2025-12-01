# analysis/plots.py

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300

# -------------------------
# Path Configuration
# -------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
csv_path = os.path.join(os.path.dirname(__file__), "metrics_summary.csv")
output_dir = os.path.join(BASE_DIR, "analysis", "plots")

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

def load_and_prepare_data():
    """Load and prepare the metrics data."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"metrics_summary.csv NOT FOUND at:\n{csv_path}")
    
    df = pd.read_csv(csv_path)
    return df

def plot_metrics_by_model(df):
    """Plot various metrics by model."""
    metrics = ['bleu_score', 'rouge1', 'rouge2', 'rougeL', 'accuracy', 'hallucination_rate']
    
    for metric in metrics:
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='model', y=metric, hue='dataset')
        plt.title(f'{metric.upper()} by Model and Dataset')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{metric}_by_model.png'))
        plt.close()

def plot_correlation_heatmap(df):
    """Plot correlation heatmap of metrics."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    corr = df[numeric_cols].corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, fmt='.2f')
    plt.title('Correlation Heatmap of Metrics')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'correlation_heatmap.png'))
    plt.close()

def plot_model_comparison(df):
    """Create a radar chart comparing models across metrics."""
    metrics = ['bleu_score', 'rouge1', 'accuracy']
    models = df['model'].unique()
    
    # Normalize metrics to 0-1 scale for radar chart
    plot_data = df.groupby('model')[metrics].mean()
    plot_data = (plot_data - plot_data.min()) / (plot_data.max() - plot_data.min())
    
    # Number of variables
    categories = list(plot_data.columns)
    N = len(categories)
    
    # Compute angle of each axis
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # Initialize the radar plot
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    # Plot each model
    for idx, model in enumerate(plot_data.index):
        values = plot_data.loc[model].values.flatten().tolist()
        values += values[:1]
        ax.plot(angles, values, linewidth=1, linestyle='solid', label=model)
        ax.fill(angles, values, alpha=0.1)
    
    # Add labels
    plt.xticks(angles[:-1], categories)
    plt.title('Model Comparison (Normalized Metrics)', size=15, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'model_comparison_radar.png'))
    plt.close()

def main():
    try:
        print("Loading data...")
        df = load_and_prepare_data()
        
        print("Generating plots...")
        plot_metrics_by_model(df)
        plot_correlation_heatmap(df)
        plot_model_comparison(df)
        
        print(f"\n✅ All plots successfully generated in: {os.path.abspath(output_dir)}")
        
    except Exception as e:
        print(f"\n❌ Error generating plots: {str(e)}")
        raise

if __name__ == "__main__":
    main()
