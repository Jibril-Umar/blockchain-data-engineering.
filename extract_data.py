import time
import sqlite3
import pandas as pd
from web3 import Web3

# 1. Connect to Public RPC Node
RPC_URL = "https://ethereum-rpc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
DB_NAME = "blockchain_data.db"

# Format USDT contract and Transfer Topic Hash strictly as lowercase hex strings
USDT_CONTRACT = w3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
TRANSFER_TOPIC = w3.to_hex(w3.keccak(text="Transfer(address,address,uint256)"))

def process_block(block_number):
    """Parses native ETH transactions AND decodes USDT ERC-20 token transfer events."""
    try:
        block = w3.eth.get_block(block_number, full_transactions=True)
        
        # 1. Parse Native ETH Transactions
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

        # 2. Extract USDT ERC-20 Event Logs with explicit Hex Block numbers
        block_hex = w3.to_hex(block_number)
        
        token_tx_data = []
        try:
            logs = w3.eth.get_logs({
                "fromBlock": block_hex,
                "toBlock": block_hex,
                "address": USDT_CONTRACT,
                "topics": [TRANSFER_TOPIC]
            })

            for log in logs:
                if len(log["topics"]) == 3:
                    # Decode From & To addresses
                    from_addr = "0x" + log["topics"][1].hex()[-40:]
                    to_addr = "0x" + log["topics"][2].hex()[-40:]
                    
                    # Decode amount (USDT uses 6 decimal places)
                    raw_val = int(log["data"].hex(), 16)
                    amount_usdt = raw_val / (10 ** 6)

                    token_tx_data.append({
                        "block_number": block_number,
                        "tx_hash": log["transactionHash"].hex(),
                        "token_symbol": "USDT",
                        "from_address": w3.to_checksum_address(from_addr),
                        "to_address": w3.to_checksum_address(to_addr),
                        "amount": amount_usdt
                    })
        except Exception as log_err:
            print(f"⚠️ Log query skipped for block #{block_number}: {log_err}")

        df_tokens = pd.DataFrame(token_tx_data)

        # 3. Stream to SQLite Database
        conn = sqlite3.connect(DB_NAME)
        df_eth.to_sql("transactions", conn, if_exists="append", index=False)
        
        if not df_tokens.empty:
            df_tokens.to_sql("token_transfers", conn, if_exists="append", index=False)
            
        conn.close()

        print(f"✅ [Block #{block.number:,}] Saved {len(df_eth)} ETH Txs & {len(df_tokens)} USDT Transfers!")

    except Exception as e:
        print(f"⚠️ Error processing block #{block_number}: {e}")

def start_continuous_ingestion():
    if not w3.is_connected():
        print("❌ Error: Web3 connection failed.")
        return

    print("\n==================================================")
    print("⚡ MULTI-ASSET ON-CHAIN INGESTION ENGINE")
    print("==================================================")
    print("Streaming Live Ethereum Blocks + USDT Transfers to SQL...\n")

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
            print("\n🛑 Ingestion pipeline stopped.")
            break
        except Exception as e:
            print(f"⚠️ Connection loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_continuous_ingestion()