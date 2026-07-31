import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# ------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# ------------------------------------------------------------------
st.set_page_config(
    page_title="On-Chain Analytics & Fraud Detection",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Real-Time On-Chain Analytics & Threat Dashboard")
st.markdown("Streaming Ethereum Mainnet blocks, gas dynamics, and token whale transfers.")

DB_NAME = "blockchain_data.db"

def get_data(query):
    """Utility to query local SQLite database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database query error: {e}")
        return pd.DataFrame()

# ------------------------------------------------------------------
# 2. KEY METRICS CARDS (KPIs)
# ------------------------------------------------------------------
st.subheader("📌 Ecosystem Highlights")

col1, col2, col3, col4 = st.columns(4)

df_eth_count = get_data("SELECT COUNT(*) as count FROM transactions;")
total_eth_txs = df_eth_count['count'].values[0] if not df_eth_count.empty else 0

df_usdt_stats = get_data("SELECT COUNT(*) as count, SUM(amount) as total_vol FROM token_transfers;")
total_usdt_txs = df_usdt_stats['count'].values[0] if not df_usdt_stats.empty else 0
total_usdt_vol = df_usdt_stats['total_vol'].values[0] if not df_usdt_stats.empty and df_usdt_stats['total_vol'].values[0] else 0.0

df_whales_count = get_data("SELECT COUNT(*) as count FROM token_transfers WHERE amount >= 50000;")
total_alerts = df_whales_count['count'].values[0] if not df_whales_count.empty else 0

col1.metric("Total ETH Transactions", f"{total_eth_txs:,}")
col2.metric("Total USDT Transfers", f"{total_usdt_txs:,}")
col3.metric("USDT Volume Streamed", f"${total_usdt_vol:,.2f}")
col4.metric("Whale Alerts (>= $50k)", f"{total_alerts:,}", delta="Real-Time", delta_color="inverse")

st.divider()

# ------------------------------------------------------------------
# 3. CHARTS & VISUALIZATIONS
# ------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Transactions Processed per Block")
    df_block_eth = get_data("""
        SELECT block_number, COUNT(*) as tx_count, AVG(gas_price_gwei) as avg_gas
        FROM transactions 
        GROUP BY block_number 
        ORDER BY block_number DESC LIMIT 20;
    """)
    if not df_block_eth.empty:
        fig_tx = px.bar(
            df_block_eth, 
            x="block_number", 
            y="tx_count", 
            title="ETH Transaction Volume by Block",
            labels={"block_number": "Block Number", "tx_count": "Transactions"},
            color_discrete_sequence=["#00CC96"]
        )
        st.plotly_chart(fig_tx, use_container_width=True)

with col_right:
    st.subheader("⛽ Average Gas Price (Gwei)")
    if not df_block_eth.empty:
        fig_gas = px.line(
            df_block_eth, 
            x="block_number", 
            y="avg_gas", 
            title="Gas Price Trend across Latest Blocks",
            labels={"block_number": "Block Number", "avg_gas": "Gas Price (Gwei)"},
            markers=True
        )
        st.plotly_chart(fig_gas, use_container_width=True)

st.divider()

# ------------------------------------------------------------------
# 4. LIVE WHALE ALERT FEED TABLE
# ------------------------------------------------------------------
st.subheader("🚨 Live Whale & Fraud Detection Log (>= $50,000 USD)")

df_alerts = get_data("""
    SELECT block_number, amount as usdt_amount, from_address, to_address, tx_hash 
    FROM token_transfers 
    WHERE amount >= 50000 
    ORDER BY block_number DESC, amount DESC;
""")

if not df_alerts.empty:
    df_alerts["usdt_amount"] = df_alerts["usdt_amount"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(
        df_alerts, 
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No high-value alerts (>= $50,000 USD) logged in database yet.")