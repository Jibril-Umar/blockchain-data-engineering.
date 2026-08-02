import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from analytics import (
    get_top_usdt_senders, 
    get_top_gas_consumers, 
    profile_wallet, 
    trace_multi_hop_transfers,
    resolve_label
)

st.set_page_config(
    page_title="Institutional On-Chain Intelligence",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Enterprise On-Chain Intelligence & AML Trail Engine")
st.markdown("Real-time blockchain monitoring, address entity resolution, and multi-hop fund flow tracing.")

DB_NAME = "blockchain_data.db"

def get_data(query):
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database query error: {e}")
        return pd.DataFrame()

# ------------------------------------------------------------------
# TAB NAVIGATION
# ------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Ecosystem Overview", 
    "🏷️ Entity & Wallet Profiler", 
    "🕸️ Multi-Hop Money Trail Tracer",
    "🚨 Live Whale Threat Feed"
])

# --- TAB 1: ECOSYSTEM OVERVIEW ---
with tab1:
    st.subheader("📌 System KPI Highlights")
    col1, col2, col3, col4 = st.columns(4)

    df_eth_count = get_data("SELECT COUNT(*) as count FROM transactions;")
    total_eth_txs = df_eth_count['count'].values[0] if not df_eth_count.empty else 0

    df_usdt_stats = get_data("SELECT COUNT(*) as count, SUM(amount) as total_vol FROM token_transfers;")
    total_usdt_txs = df_usdt_stats['count'].values[0] if not df_usdt_stats.empty else 0
    total_usdt_vol = df_usdt_stats['total_vol'].values[0] if not df_usdt_stats.empty and df_usdt_stats['total_vol'].values[0] else 0.0

    df_whales_count = get_data("SELECT COUNT(*) as count FROM token_transfers WHERE amount >= 50000;")
    total_alerts = df_whales_count['count'].values[0] if not df_whales_count.empty else 0

    col1.metric("Total ETH Txs Ingested", f"{total_eth_txs:,}")
    col2.metric("Total USDT Transfers", f"{total_usdt_txs:,}")
    col3.metric("USDT Volume Monitored", f"${total_usdt_vol:,.2f}")
    col4.metric("Whale Alerts (>= $50k)", f"{total_alerts:,}")

    st.divider()

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📈 Transactions per Block")
        df_block_eth = get_data("""
            SELECT block_number, COUNT(*) as tx_count, AVG(gas_price_gwei) as avg_gas
            FROM transactions GROUP BY block_number ORDER BY block_number DESC LIMIT 20;
        """)
        if not df_block_eth.empty:
            fig_tx = px.bar(
                df_block_eth, x="block_number", y="tx_count",
                labels={"block_number": "Block Number", "tx_count": "Transactions"},
                color_discrete_sequence=["#00CC96"]
            )
            st.plotly_chart(fig_tx, use_container_width=True)

    with col_right:
        st.subheader("⛽ Gas Volatility Trend (Gwei)")
        if not df_block_eth.empty:
            fig_gas = px.line(
                df_block_eth, x="block_number", y="avg_gas",
                labels={"block_number": "Block Number", "avg_gas": "Gas Price (Gwei)"},
                markers=True
            )
            st.plotly_chart(fig_gas, use_container_width=True)

# --- TAB 2: ENTITY & WALLET PROFILER ---
with tab2:
    st.subheader("🏷️ Identified Entities & Wallet Profiling")
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.markdown("### 🐋 Top USDT Volume Entities")
        df_top_whales = get_top_usdt_senders(10)
        if not df_top_whales.empty:
            df_top_whales["total_usdt_sent"] = df_top_whales["total_usdt_sent"].apply(lambda x: f"${x:,.2f}")
            df_top_whales["avg_transfer_size"] = df_top_whales["avg_transfer_size"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_top_whales[["entity_label", "total_transfers", "total_usdt_sent", "avg_transfer_size"]], use_container_width=True, hide_index=True)
        else:
            st.info("No token transfers logged.")

    with col_w2:
        st.markdown("### ⛽ Top Gas Consumers")
        df_top_gas = get_top_gas_consumers(10)
        if not df_top_gas.empty:
            df_top_gas["avg_gas_gwei"] = df_top_gas["avg_gas_gwei"].apply(lambda x: f"{x:,.2f} Gwei")
            df_top_gas["max_gas_gwei"] = df_top_gas["max_gas_gwei"].apply(lambda x: f"{x:,.2f} Gwei")
            st.dataframe(df_top_gas[["entity_label", "total_txs", "avg_gas_gwei", "max_gas_gwei"]], use_container_width=True, hide_index=True)
        else:
            st.info("No transaction records found.")

    st.divider()
    
    st.markdown("### 🔍 Direct Address Profile Inspector")
    target_address = st.text_input("Enter Ethereum Address (0x...):", value="", key="prof_input")
    
    if target_address:
        eth_history, usdt_history = profile_wallet(target_address)
        st.write(f"#### 📜 Activity Profile for `{resolve_label(target_address)}`")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"**ETH Transactions ({len(eth_history)})**")
            if not eth_history.empty:
                st.dataframe(eth_history, use_container_width=True, hide_index=True)
            else:
                st.caption("No ETH transactions logged.")
                
        with col_p2:
            st.markdown(f"**USDT Transfers ({len(usdt_history)})**")
            if not usdt_history.empty:
                usdt_history["amount"] = usdt_history["amount"].apply(lambda x: f"${x:,.2f}")
                st.dataframe(usdt_history, use_container_width=True, hide_index=True)
            else:
                st.caption("No USDT transfers logged.")

# --- TAB 3: MULTI-HOP MONEY TRAIL TRACER ---
with tab3:
    st.subheader("🕸️ Multi-Hop Downstream Fund Flow Investigator")
    st.markdown("Trace how money moves from an initial origin address through intermediary wallets to final destinations.")
    
    trace_address = st.text_input("Enter Source Wallet to Trace (0x...):", value="0xAC54D27dD345e13f5a923659C43EAf3464471630", key="trace_input")
    
    if trace_address:
        df_hops = trace_multi_hop_transfers(trace_address)
        if not df_hops.empty:
            st.markdown(f"### 📍 2-Hop Fund Destinations for `{resolve_label(trace_address)}`")
            
            df_hops["hop_1_amount"] = df_hops["hop_1_amount"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "—")
            df_hops["hop_2_amount"] = df_hops["hop_2_amount"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "—")
            
            display_df = df_hops[["source_label", "hop_1_label", "hop_1_amount", "hop_2_label", "hop_2_amount"]].copy()
            display_df.columns = ["Source Entity", "Hop 1 Target", "Hop 1 Vol ($)", "Hop 2 Target", "Hop 2 Vol ($)"]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No downstream multi-hop flows found for this address in current database records.")

# --- TAB 4: LIVE WHALE THREAT FEED ---
with tab4:
    st.subheader("🚨 High-Value Alert Feed (>= $50,000 USD)")
    df_alerts = get_data("""
        SELECT block_number, amount as usdt_amount, from_address, to_address, tx_hash 
        FROM token_transfers WHERE amount >= 50000 
        ORDER BY block_number DESC, amount DESC;
    """)

    if not df_alerts.empty:
        df_alerts["from_entity"] = df_alerts["from_address"].apply(resolve_label)
        df_alerts["to_entity"] = df_alerts["to_address"].apply(resolve_label)
        df_alerts["usdt_amount"] = df_alerts["usdt_amount"].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            df_alerts[["block_number", "usdt_amount", "from_entity", "to_entity", "tx_hash"]], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("No high-value alerts logged yet.")