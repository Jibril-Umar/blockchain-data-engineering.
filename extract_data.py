import time
import sqlite3
import pandas as pd
from web3 import Web3

# ------------------------------------------------------------------
# 1. RPC CONNECTION & CONFIGURATION
# ------------------------------------------------------------------
RPC_URLS = [
    "https://1rpc.io/eth",
    "https://rpc.ankr.com/eth",
    "https://ethereum-rpc.publicnode.com"
]

def get_web3_connection():
    for url in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                print(f"Connected to RPC: {url}")
                return w3
        except Exception:
            continue
    raise ConnectionError("Could not connect to any RPC node.")

w3 = get_web3_connection()
DB_NAME = "blockchain_data.db"

# USDT Contract Address & Transfer Event Signature Topic
USDT_CONTRACT = w3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# EARLY FRAUD DETECTION / WHALE ALERT THRESHOLD ($50,000 USD)
ALERT_THRESHOLD_USD = 50_000.0


# ------------------------------------------------------------------
# 2. ALERT NOTIFICATION SYSTEM
# ------------------------------------------------------------------
def trigger_alert(block_num, tx_hash, sender, receiver, amount):
    """Triggers real-time alerts for high-value or potential fraud transfers."""
    print("\n" + "🚨" * 22)
    print(" 🚨 EARLY FRAUD / WHALE ALERT DETECTED 🚨")
    print("🚨" * 22)
    print(f"📦 Block Number : #{block_num:,}")
    print(f"💰 Amount       : ${amount:,.2f} USDT")
    print(f"📤 From Address : {sender}")
    print(f"📥 To Address   : {receiver}")
    print(f"🔗 Tx Hash      : https://etherscan.io/tx/{tx_hash}")
    print("🚨" * 22 + "\n")


# ------------------------------------------------------------------
# 3. BLOCK PARSER & DATA TRANSFORMER
# ------------------------------------------------------------------
def process_block(block_number):
    try:
        # Fetch block with all transaction details
        block = w3.eth.get_block(block_number, full_transactions=True)
        
        # A. Parse Base-Layer ETH Transactions
        eth_tx_data = []
        for tx in block.transactions:
            eth_tx_data.append({
                "block_number": block.number,
                "tx_hash": tx["hash"].hex(),
                "from_address": tx["from"],
                "to_address": tx["to"],
                "value_eth": float(w3.from_wei(tx["value"], "ether")),
                "gas_price_gwei": float(w3.from_wei(tx["gasPrice"], "gwei"))
            })

        df_eth = pd.DataFrame(eth_tx_data)

        # B. Parse & Decode USDT Smart Contract Logs
        token_tx_data = []
        try:
            logs = w3.eth.get_logs({
                "fromBlock": block_number,
                "toBlock": block_number,
                "address": USDT_CONTRACT,
                "topics": [TRANSFER_TOPIC]
            })

            for log in logs:
                if len(log["topics"]) == 3:
                    from_addr = w3.to_checksum_address("0x" + log["topics"][1].hex()[-40:])
                    to_addr = w3.to_checksum_address("0x" + log["topics"][2].hex()[-40:])
                    
                    # Decoded amount (USDT uses 6 decimal places)
                    raw_amount = int(log["data"].hex(), 16)
                    amount_usdt = raw_amount / (10 ** 6)
                    tx_hash_hex = log["transactionHash"].hex()

                    # Trigger alert if transaction meets or exceeds $50,000 USD
                    if amount_usdt >= ALERT_THRESHOLD_USD:
                        trigger_alert(block_number, tx_hash_hex, from_addr, to_addr, amount_usdt)

                    token_tx_data.append({
                        "block_number": block_number,
                        "tx_hash": tx_hash_hex,
                        "token_symbol": "USDT",
                        "from_address": from_addr,
                        "to_address": to_addr,
                        "amount": amount_usdt
                    })
        except Exception as log_err:
            # Fallback if log endpoint rate-limits on a specific block
            token_tx_data = []

        df_tokens = pd.DataFrame(token_tx_data)

        # C. Save Streamed Data to SQLite
        conn = sqlite3.connect(DB_NAME)
        if not df_eth.empty:
            df_eth.to_sql("transactions", conn, if_exists="append", index=False)
        if not df_tokens.empty:
            df_tokens.to_sql("token_transfers", conn, if_exists="append", index=False)
        conn.close()

        print(f"✅ [Block #{block.number:,}] Saved {len(df_eth)} ETH Txs & {len(df_tokens)} USDT Transfers")

    except Exception as e:
        print(f"⚠️ Error processing block #{block_number}: {e}")


# ------------------------------------------------------------------
# 4. CONTINUOUS BLOCK LISTENER
# ------------------------------------------------------------------
def start_continuous_ingestion():
    print("\n==================================================")
    print("⚡ EARLY FRAUD DETECTION & ON-CHAIN ENGINE")
    print("==================================================")
    print(f"Streaming Mainnet Blocks | Alert Threshold: >= ${ALERT_THRESHOLD_USD:,.2f}\n")

    last_processed_block = 0

    while True:
        try:
            current_block = w3.eth.block_number
            if current_block > last_processed_block:
                if last_processed_block == 0:
                    last_processed_block = current_block - 1
                last_processed_block += 1
                process_block(last_processed_block)
            else:
                time.sleep(12)
        except KeyboardInterrupt:
            print("\n🛑 Pipeline stopped by user.")
            break
        except Exception as e:
            print(f"⚠️ Connection dropped, retrying... ({e})")
            time.sleep(5)

if __name__ == "__main__":
    start_continuous_ingestion()