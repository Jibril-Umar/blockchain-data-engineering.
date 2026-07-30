import sqlite3
import pandas as pd

# Connect to SQLite Database
conn = sqlite3.connect("blockchain_data.db")

print("\n==================================================")
print("📊 MULTI-ASSET ON-CHAIN ANALYTICS DASHBOARD")
print("==================================================\n")

# 1. Native ETH Transactions Summary
try:
    total_eth_txs = pd.read_sql_query("SELECT COUNT(*) as count FROM transactions;", conn)
    print(f"📈 Total ETH Transactions Stored: {total_eth_txs['count'].values[0]:,}")
except Exception as e:
    print(f"⚠️ Could not query transactions table: {e}")

# 2. USDT Token Transfers Summary
try:
    total_usdt_txs = pd.read_sql_query("SELECT COUNT(*) as count, ROUND(SUM(amount), 2) as total_volume FROM token_transfers;", conn)
    print(f"💵 Total USDT Transfers Stored: {total_usdt_txs['count'].values[0]:,}")
    print(f"💰 Total USDT Volume Streamed: ${total_usdt_txs['total_volume'].values[0]:,.2f}\n")
except Exception as e:
    print(f"⚠️ Could not query token_transfers table: {e}")

print("-" * 50)

# 3. Top 5 Largest USDT Transfers (Whale Activity)
try:
    query_whales = """
    SELECT block_number, tx_hash, from_address, to_address, ROUND(amount, 2) as usdt_amount
    FROM token_transfers
    ORDER BY amount DESC
    LIMIT 5;
    """
    df_whales = pd.read_sql_query(query_whales, conn)
    print("\n🐳 TOP 5 USDT WHALE TRANSFERS:")
    print(df_whales.to_string(index=False))
except Exception as e:
    print(f"⚠️ Could not fetch USDT whales: {e}")

print("\n==================================================\n")

conn.close()