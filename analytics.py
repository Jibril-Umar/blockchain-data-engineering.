import sqlite3
import pandas as pd

DB_NAME = "blockchain_data.db"

# ------------------------------------------------------------------
# KNOWN ENTITY REGISTRY (ENTITIES & PROTOCOLS)
# ------------------------------------------------------------------
KNOWN_ENTITIES = {
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "Tether: USDT Contract",
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2: Router",
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3: Router",
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance: Hot Wallet 14",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance: Hot Wallet 1",
    "0xdfd5293d8e347dfee59e53615b0057b1a12965b3": "Binance: Deposit Wallet",
    "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43": "Coinbase: Prime",
    "0xac54d27dd345e13f5a923659c43eaf3464471630": "Whale / Market Maker Alpha"
}

def resolve_label(address):
    """Maps hex addresses to human-readable labels if known."""
    if not address or pd.isna(address):
        return "No Outbound Transfer Logged"
    clean_addr = address.lower().strip()
    return KNOWN_ENTITIES.get(clean_addr, address)

def run_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_top_usdt_senders(limit=10):
    query = """
        SELECT 
            from_address AS wallet_address,
            COUNT(*) AS total_transfers,
            SUM(amount) AS total_usdt_sent,
            AVG(amount) AS avg_transfer_size
        FROM token_transfers
        GROUP BY from_address
        ORDER BY total_usdt_sent DESC
        LIMIT ?;
    """
    df = run_query(query, params=(limit,))
    if not df.empty:
        df["entity_label"] = df["wallet_address"].apply(resolve_label)
    return df

def get_top_gas_consumers(limit=10):
    query = """
        SELECT 
            from_address AS wallet_address,
            COUNT(*) AS total_txs,
            AVG(gas_price_gwei) AS avg_gas_gwei,
            MAX(gas_price_gwei) AS max_gas_gwei
        FROM transactions
        GROUP BY from_address
        ORDER BY avg_gas_gwei DESC
        LIMIT ?;
    """
    df = run_query(query, params=(limit,))
    if not df.empty:
        df["entity_label"] = df["wallet_address"].apply(resolve_label)
    return df

def trace_multi_hop_transfers(start_address):
    """
    Traces 2-hop downstream fund flows:
    Hop 1: Start Address -> Direct Recipient (Hop 1 Address)
    Hop 2: Hop 1 Address -> Downstream Recipient (Hop 2 Address)
    """
    addr = start_address.strip()
    query = """
        SELECT 
            t1.from_address AS source_wallet,
            t1.to_address AS hop_1_recipient,
            t1.amount AS hop_1_amount,
            t2.to_address AS hop_2_recipient,
            t2.amount AS hop_2_amount
        FROM token_transfers t1
        LEFT JOIN token_transfers t2 
            ON LOWER(t1.to_address) = LOWER(t2.from_address)
        WHERE LOWER(t1.from_address) = LOWER(?)
        ORDER BY t1.amount DESC
        LIMIT 20;
    """
    df = run_query(query, params=(addr,))
    if not df.empty:
        df["source_label"] = df["source_wallet"].apply(resolve_label)
        df["hop_1_label"] = df["hop_1_recipient"].apply(resolve_label)
        df["hop_2_label"] = df["hop_2_recipient"].apply(resolve_label)
    return df

def profile_wallet(address):
    address_checksum = address.strip()
    
    eth_sent = run_query("""
        SELECT block_number, tx_hash, to_address, value_eth, gas_price_gwei 
        FROM transactions WHERE LOWER(from_address) = LOWER(?)
        ORDER BY block_number DESC;
    """, (address_checksum,))
    
    usdt_transfers = run_query("""
        SELECT block_number, tx_hash, from_address, to_address, amount 
        FROM token_transfers 
        WHERE LOWER(from_address) = LOWER(?) OR LOWER(to_address) = LOWER(?)
        ORDER BY block_number DESC;
    """, (address_checksum, address_checksum))
    
    if not eth_sent.empty:
        eth_sent["to_label"] = eth_sent["to_address"].apply(resolve_label)
    if not usdt_transfers.empty:
        usdt_transfers["from_label"] = usdt_transfers["from_address"].apply(resolve_label)
        usdt_transfers["to_label"] = usdt_transfers["to_address"].apply(resolve_label)
        
    return eth_sent, usdt_transfers