# 🪙 Blockchain Data Engineering & Intelligence Dashboard

An end-to-end data pipeline and interactive analytics dashboard that ingests live Ethereum blockchain data, stores structured transaction records in a SQLite database, and performs analytical modeling to track gas fee distributions, whale activity, and multi-hop transaction trails.

---

## 📌 Features & Key Capabilities

* **Data Extraction & Pipeline (`extract_data.py`):** Automatically ingests block data and transactions via web3/Etherscan APIs.
* **Relational Storage (`blockchain_data.db`):** Stores structured block numbers, transaction hashes, sender/receiver addresses, values, and gas metrics.
* **SQL Analytics Engine (`query_data.py`, `analytics.py`):** Executes aggregate SQL queries to extract gas trends and high-value wallet transfers.
* **Interactive Streamlit App (`app.py`):** Provides real-time UI filtering, multi-hop fund tracing, and visual analytics.
* **Fraud & Anomaly Detection:** Flags suspicious transaction flows and early fraud signals across transaction networks.

---

## 🏗️ System Architecture

```text
[ Ethereum Blockchain Network ]
              │
              ▼
    🐍 Python Ingestion (extract_data.py)
              │
              ▼
    🛢️ SQLite Relational DB (blockchain_data.db)
              │
              ├──► 📊 SQL Analytics & Aggregations (query_data.py)
              │
              ▼
    🎈 Streamlit Web Dashboard (app.py)
