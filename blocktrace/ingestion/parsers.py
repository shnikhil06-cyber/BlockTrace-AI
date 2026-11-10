"""
Data Ingestion Parsers for Bitcoin Blockchain and Network Observation Logs.
Supports CSV and JSON formats, robust error handling, and type normalization.
"""

from typing import Union, BinaryIO, TextIO
import json
import io
import pandas as pd
import numpy as np


def parse_transactions(
    source: Union[str, BinaryIO, TextIO],
    file_type: str = "auto"
) -> pd.DataFrame:
    """
    Parses Bitcoin transaction records from CSV or JSON source.
    
    Standardized columns returned:
    - tx_id: str (transaction hash)
    - timestamp: pd.Timestamp (UTC)
    - block_height: int
    - sender_addresses: list[str]
    - receiver_addresses: list[str]
    - amount_btc: float
    - fee_btc: float
    - fee_rate_sat_vb: float
    - size_vbytes: int
    - is_rbf: bool
    - input_count: int
    - output_count: int
    - locktime: int
    """
    if file_type == "auto":
        if isinstance(source, str):
            if source.endswith(".json"):
                file_type = "json"
            else:
                file_type = "csv"
        else:
            name = getattr(source, "name", "").lower()
            file_type = "json" if name.endswith(".json") else "csv"

    if file_type == "json":
        if isinstance(source, str):
            with open(source, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        else:
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            raw_data = json.loads(content)
        
        if isinstance(raw_data, dict) and "transactions" in raw_data:
            raw_data = raw_data["transactions"]
        df = pd.DataFrame(raw_data)
    else:
        df = pd.read_csv(source)

    # Column name normalization (lowercase, stripped)
    df.columns = [c.strip().lower() for c in df.columns]

    # Map possible alternative names
    rename_map = {
        "txid": "tx_id",
        "hash": "tx_id",
        "transaction_id": "tx_id",
        "time": "timestamp",
        "date": "timestamp",
        "block": "block_height",
        "height": "block_height",
        "senders": "sender_addresses",
        "inputs": "sender_addresses",
        "from_addresses": "sender_addresses",
        "receivers": "receiver_addresses",
        "outputs": "receiver_addresses",
        "to_addresses": "receiver_addresses",
        "value_btc": "amount_btc",
        "amount": "amount_btc",
        "total_btc": "amount_btc",
        "fee": "fee_btc",
        "fee_rate": "fee_rate_sat_vb",
        "vsize": "size_vbytes",
        "size": "size_vbytes",
        "rbf": "is_rbf",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Validate essential column: tx_id
    if "tx_id" not in df.columns:
        raise ValueError("Transaction dataset is missing mandatory column: 'tx_id'")

    # Ensure tx_id is clean string
    df["tx_id"] = df["tx_id"].astype(str).str.strip()

    # Parse timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["timestamp"] = df["timestamp"].fillna(pd.Timestamp.now(tz="UTC"))
    else:
        df["timestamp"] = pd.Timestamp.now(tz="UTC")

    # Numeric fields
    if "block_height" in df.columns:
        df["block_height"] = pd.to_numeric(df["block_height"], errors="coerce").fillna(0).astype(int)
    else:
        df["block_height"] = 800000

    if "amount_btc" in df.columns:
        df["amount_btc"] = pd.to_numeric(df["amount_btc"], errors="coerce").fillna(0.0)
    else:
        df["amount_btc"] = 1.0

    if "fee_btc" in df.columns:
        df["fee_btc"] = pd.to_numeric(df["fee_btc"], errors="coerce").fillna(0.0001)
    else:
        df["fee_btc"] = 0.0001

    if "size_vbytes" in df.columns:
        df["size_vbytes"] = pd.to_numeric(df["size_vbytes"], errors="coerce").fillna(220).astype(int)
    else:
        df["size_vbytes"] = 220

    if "fee_rate_sat_vb" in df.columns:
        df["fee_rate_sat_vb"] = pd.to_numeric(df["fee_rate_sat_vb"], errors="coerce")
    else:
        # compute sat/vB: (fee_btc * 1e8) / size_vbytes
        df["fee_rate_sat_vb"] = (df["fee_btc"] * 1e8) / np.maximum(df["size_vbytes"], 1)

    df["fee_rate_sat_vb"] = df["fee_rate_sat_vb"].fillna((df["fee_btc"] * 1e8) / np.maximum(df["size_vbytes"], 1))

    # Parse address lists (could be strings like 'addr1;addr2', '["addr1","addr2"]', or already lists)
    def clean_address_list(val, default_prefix="addr_"):
        if isinstance(val, (list, tuple)):
            return [str(x).strip() for x in val if str(x).strip()]
        if pd.isna(val) or val is None or str(val).strip() == "":
            return []
        s = str(val).strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s.replace("'", '"'))
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        # Try delimiter splitting
        for delim in [";", "|", ",", " "]:
            if delim in s:
                parts = [p.strip() for p in s.split(delim) if p.strip()]
                if len(parts) > 1:
                    return parts
        return [s]

    if "sender_addresses" in df.columns:
        df["sender_addresses"] = df["sender_addresses"].apply(lambda v: clean_address_list(v, "sender_"))
    else:
        df["sender_addresses"] = df["tx_id"].apply(lambda tid: [f"bc1q_{tid[:8]}_in"])

    if "receiver_addresses" in df.columns:
        df["receiver_addresses"] = df["receiver_addresses"].apply(lambda v: clean_address_list(v, "recv_"))
    else:
        df["receiver_addresses"] = df["tx_id"].apply(lambda tid: [f"bc1q_{tid[-8:]}_out"])

    # Counts
    if "input_count" in df.columns:
        df["input_count"] = pd.to_numeric(df["input_count"], errors="coerce").fillna(
            df["sender_addresses"].apply(len)
        ).astype(int)
    else:
        df["input_count"] = df["sender_addresses"].apply(lambda x: max(len(x), 1))

    if "output_count" in df.columns:
        df["output_count"] = pd.to_numeric(df["output_count"], errors="coerce").fillna(
            df["receiver_addresses"].apply(len)
        ).astype(int)
    else:
        df["output_count"] = df["receiver_addresses"].apply(lambda x: max(len(x), 1))

    if "is_rbf" in df.columns:
        df["is_rbf"] = df["is_rbf"].astype(str).str.lower().isin(["true", "1", "yes", "t"])
    else:
        df["is_rbf"] = False

    if "locktime" in df.columns:
        df["locktime"] = pd.to_numeric(df["locktime"], errors="coerce").fillna(0).astype(int)
    else:
        df["locktime"] = 0

    return df


def parse_network_logs(
    source: Union[str, BinaryIO, TextIO],
    file_type: str = "auto"
) -> pd.DataFrame:
    """
    Parses Bitcoin P2P network observation logs from CSV or JSON source.
    
    Standardized columns returned:
    - log_id: str
    - tx_id: str
    - timestamp_observed: pd.Timestamp (UTC)
    - node_id: str
    - ip_address: str
    - port: int
    - event_type: str ('inv_broadcast', 'mempool_accept', 'peer_relay', 'tx_getdata')
    - latency_ms: float
    - country: str
    - asn: str
    - user_agent: str
    """
    if file_type == "auto":
        if isinstance(source, str):
            if source.endswith(".json"):
                file_type = "json"
            else:
                file_type = "csv"
        else:
            name = getattr(source, "name", "").lower()
            file_type = "json" if name.endswith(".json") else "csv"

    if file_type == "json":
        if isinstance(source, str):
            with open(source, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        else:
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            raw_data = json.loads(content)
            
        if isinstance(raw_data, dict) and "network_logs" in raw_data:
            raw_data = raw_data["network_logs"]
        df = pd.DataFrame(raw_data)
    else:
        df = pd.read_csv(source)

    df.columns = [c.strip().lower() for c in df.columns]

    rename_map = {
        "txid": "tx_id",
        "transaction_id": "tx_id",
        "hash": "tx_id",
        "time": "timestamp_observed",
        "timestamp": "timestamp_observed",
        "observed_at": "timestamp_observed",
        "node": "node_id",
        "peer_id": "node_id",
        "ip": "ip_address",
        "peer_ip": "ip_address",
        "event": "event_type",
        "action": "event_type",
        "delay_ms": "latency_ms",
        "latency": "latency_ms",
        "geo": "country",
        "location": "country",
        "as_number": "asn",
        "client": "user_agent",
        "version": "user_agent",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "tx_id" not in df.columns:
        raise ValueError("Network logs dataset is missing mandatory column: 'tx_id'")

    df["tx_id"] = df["tx_id"].astype(str).str.strip()

    if "log_id" not in df.columns:
        df["log_id"] = [f"net_log_{i:06d}" for i in range(len(df))]
    else:
        df["log_id"] = df["log_id"].astype(str)

    if "timestamp_observed" in df.columns:
        df["timestamp_observed"] = pd.to_datetime(df["timestamp_observed"], utc=True, errors="coerce")
        df["timestamp_observed"] = df["timestamp_observed"].fillna(pd.Timestamp.now(tz="UTC"))
    else:
        df["timestamp_observed"] = pd.Timestamp.now(tz="UTC")

    if "node_id" not in df.columns:
        df["node_id"] = [f"node_{i % 30:03d}" for i in range(len(df))]
    else:
        df["node_id"] = df["node_id"].astype(str)

    if "ip_address" not in df.columns:
        df["ip_address"] = "127.0.0.1"
    else:
        df["ip_address"] = df["ip_address"].astype(str).str.strip()

    if "port" in df.columns:
        df["port"] = pd.to_numeric(df["port"], errors="coerce").fillna(8333).astype(int)
    else:
        df["port"] = 8333

    if "event_type" not in df.columns:
        df["event_type"] = "peer_relay"
    else:
        df["event_type"] = df["event_type"].astype(str).str.strip().str.lower()

    if "latency_ms" in df.columns:
        df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce").fillna(45.0)
    else:
        df["latency_ms"] = 45.0

    if "country" not in df.columns:
        df["country"] = "US"
    else:
        df["country"] = df["country"].astype(str).str.strip().str.upper()

    if "asn" not in df.columns:
        df["asn"] = "AS15169"
    else:
        df["asn"] = df["asn"].astype(str).str.strip().str.upper()

    if "user_agent" not in df.columns:
        df["user_agent"] = "/Satoshi:25.0.0/"
    else:
        df["user_agent"] = df["user_agent"].astype(str).str.strip()

    return df

