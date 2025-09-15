"""
Plotease
--------

High-level auto plotting library for EDA and model evaluation with AI Assistant
"""

__version__ = "0.1.0"
__author__ = "Rayyan Ahmed, Irtat Mobin, Agha Haris"

# Expose EDA and Model Eval as namespaces
from . import eda
#from . import model_eval

def library_structure():
    """Print the full package structure of Plotease."""
    structure = """

Structure of Plotease:
By: Agha Haris, Rayyan Ahmed, Irtat Mobin.

Plotease/
├── __init__.py
│
├── eda/                   # Exploratory Data Analysis Plots
│   ├── __init__.py
│   ├── distribution.py         → plot_histogram(), plot_kde(), plot_rug(), plot_ecdf()
│   ├── scatter_line.py         → plot_scatter(), plot_line(), plot_jointplot(), plot_hexbin()
│   ├── regression.py           → plot_lmplot(), plot_regplot(), plot_residplot()
│   ├── categorical.py          → plot_bar_count(), plot_box(), plot_violin(), plot_strip(), plot_swarm(), plot_point(), plot_catplot()
│   ├── matrix.py               → plot_correlation_heatmap(), plot_heatmap(), plot_clustermap(), plot_pairplot()
│   ├── classic.py              → plot_bar(), plot_barh(), plot_pie(), plot_stem(), plot_step(), plot_fill_between()
│
├── model_eval/            # Model Evaluation Plots
│   ├── __init__.py
│   ├── confusion_matrix.py     → plot_confusion_matrix()
│   ├── roc_curve.py            → plot_roc_curve()
│   ├── pr_curve.py             → plot_pr_curve()
│   ├── feature_importance.py   → plot_feature_importance()
│   ├── learning_curve.py       → plot_learning_curve()
│   ├── regression_metrics.py   → plot_regression_metrics()
│   ├── residuals.py            → plot_residuals()
│
├── auto_viz/              # Smart Auto-Visualization Engine
│   ├── __init__.py
│   ├── auto_viz.py            → auto_viz(df, y=None)
│   ├── auto_scatter.py        → auto_scatter(df)
│   └── auto_summary.py        → summary_report(df)
|
├── plotease_assistant/          # Module for the AI assistant
│   ├── __init__.py
│   ├── bot.py        → main chatbot logic
│   ├── embeddings.py → create/retrieve embeddings
│   ├── utils.py      → helper functions"""

    print(structure)

def library_intro():
    """
    Prints a basic introduction to Plotease library.
    """
    info = r"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Library Name: plotease – The Future of Auto Plotting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎓 Academic Project: Final Year Project 2025 – Dawood University of Engineering & Technology, Karachi, Pakistan.

🔖 Version: 0.1.0 (V1)

👤 Official Account Name: Rayyan Ahmed, Agha Haris & Irtat Mobin  
🆔 Official Account Username: plotease_official   
📅 Date Joined: 14th September, 2025

👨‍💻 Authors:
    1. Rayyan Ahmed
    2. Irtat Mobin
    3. Agha Haris

✨ Features:

▸ EDA Plots
    🔹 Distribution plots   🔹 Scatter & line plots  🔹 Regression plots
    🔹 Categorical plots    🔹 Matrix plots          🔹 Classic plots

▸ Model Evaluation Plots
    🔹 Confusion matrix     🔹 ROC curve             🔹 Precision–Recall curve
    🔹 Feature importance   🔹 Learning curves       🔹 Residual & regression metrics

▸ Auto Visualization
    🔹 Auto Viz, Auto Scatter & Auto Summary
    🔹 Automatically detects data types (numerical, categorical)
    🔹 Generates relevant plots for each column or pair of columns

🤖 Plotease AI Assistant - ploteasebot
    🔹 PloteaseBot: An intelligent, interactive assistant
    🔹 Understands the entire "plotease" library
    🔹 Explains functions, parameters & usage
    🔹 Provides code examples & guides workflows

⚡ Usage:

    import plotease as pe
    pe.library_intro()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(info)
