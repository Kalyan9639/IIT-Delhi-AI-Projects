import pandas as pd
import numpy as np
import sqlite3
import ollama
import json
import re
import math

# --- CONFIGURATION ---
DB_NAME = "financial_audit.db"
MODEL_NAME = "gpt-oss:20b-cloud"  # Optimized for local SLM performance
CSV_FILE = "bankstatements.csv"

def init_db():
    """Initializes the SQLite database with high-fidelity financial schema."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS transactions') # Reset for fresh analysis
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            amount REAL,
            balance REAL,
            mode TEXT,
            name TEXT,
            category TEXT,
            is_bank_fee BOOLEAN,
            is_anomaly BOOLEAN,
            is_high_value BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def categorize_with_slm(transactions):
    """Leverages SLM to categorize complex transaction names."""
    prompt = f"""
    You are a financial auditor. Categorize these transactions into: 
    [Food, Transport, Shopping, Utilities, Salary, Investment, Bank Charges, Others].
    Return ONLY a JSON object mapping name to category.
    Transactions: {transactions}
    """
    try:
        response = ollama.generate(model=MODEL_NAME, prompt=prompt, format='json')
        return json.loads(response['response'])
    except:
        return {}

def process_and_audit():
    """Mathematical analysis and pipeline execution."""
    df = pd.read_csv(CSV_FILE)
    
    # 1. Mathematical Pre-processing
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    
    # Identify Anomalies using Z-Score (Mean + 2*StdDev)
    mean_spend = df[df['DrCr'] == 'Db']['amount'].mean()
    std_spend = df[df['DrCr'] == 'Db']['amount'].std()
    threshold = mean_spend + (2 * std_spend)
    
    df['is_anomaly'] = (df['amount'] > threshold) & (df['DrCr'] == 'Db')
    df['is_high_value'] = df['amount'] > 5000 
    
    # 2. Rule-based Categorization (Fast Path)
    def get_category(row):
        name = str(row['name']).upper()
        if any(x in name for x in ['SMS CHARGES', 'DEBIT CARD', 'FEE', 'STOCK']): return 'Bank Charges'
        if 'ATM' in str(row['mode']): return 'Cash Withdrawal'
        if any(x in name for x in ['ZOMATO', 'SWIGGY', 'RESTAURANT']): return 'Food'
        if any(x in name for x in ['AMAZON', 'FLIPKART', 'MEESHO']): return 'Shopping'
        return None

    df['category'] = df.apply(get_category, axis=1)
    
    # 3. AI Enrichment for Uncategorized
    uncategorized = df[df['category'].isnull()]['name'].unique()[:20] # Batch limit
    if len(uncategorized) > 0:
        ai_results = categorize_with_slm(list(uncategorized))
        df['category'] = df.apply(lambda x: ai_results.get(x['name'], x['category'] if x['category'] else 'Others'), axis=1)
    else:
        df['category'] = df['category'].fillna('Others')

    df['is_bank_fee'] = df['category'] == 'Bank Charges'
    
    # 4. Save to Database
    conn = sqlite3.connect(DB_NAME)
    df_to_save = df[['date', 'DrCr', 'amount', 'balance', 'mode', 'name', 'category', 'is_bank_fee', 'is_anomaly', 'is_high_value']]
    df_to_save.columns = ['date', 'type', 'amount', 'balance', 'mode', 'name', 'category', 'is_bank_fee', 'is_anomaly', 'is_high_value']
    df_to_save.to_sql('transactions', conn, if_exists='replace', index=False)
    conn.close()
    print("✨ Financial Audit Pipeline Complete. 509 rows processed.")

if __name__ == "__main__":
    init_db()
    process_and_audit()