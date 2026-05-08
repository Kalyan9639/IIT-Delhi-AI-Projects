import sqlite3

def fetch_transactions():
    """Fetches all transactions from the SQLite database."""
    try:
        conn = sqlite3.connect("financial_audit.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()
        conn.close()
        return transactions
    except Exception as e:
        print(f"Database error: {e}")
        return []
if __name__ == "__main__":
    transactions = fetch_transactions()
    for tx in transactions:
        with open("transactions_output.txt", "a") as f:
            f.write(str(tx) + "\n")