"""
Data Ingestion Parsers for Bitcoin Blockchain and Network Observation Logs.
Supports CSV and JSON formats, robust error handling, and type normalization.
"""

import re
from typing import Union, BinaryIO, TextIO, Any
import json
import io
import pandas as pd
import numpy as np


def _clean_column_name(col: Any) -> str:
    """Normalizes column names by replacing punctuation and spaces with single underscores."""
    s = str(col).strip().lower()
    s = re.sub(r'[^a-z0-9]+', '_', s).strip('_')
    return s


def normalize_tx_id(val: Any) -> str:
    """Standardizes transaction IDs (strips whitespace, quotes, 0x prefix, trailing .0, lowercases)."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip().strip("'\"").strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    if (s.startswith("0x") or s.startswith("0X")) and len(s) > 2:
        s = s[2:]
    return s.lower()


def _load_dataframe(
    source: Union[str, BinaryIO, TextIO],
    file_type: str,
    wrapper_keys: tuple
) -> pd.DataFrame:
    """Loads a DataFrame from CSV or JSON (supporting wrapper keys, dict records, or NDJSON)."""
    if file_type == "auto":
        if isinstance(source, str):
            file_type = "json" if source.lower().endswith(".json") else "csv"
        else:
            name = getattr(source, "name", "").lower()
            file_type = "json" if name.endswith(".json") else "csv"

    if hasattr(source, "seek"):
        try:
            source.seek(0)
        except Exception:
            pass

    if file_type == "json":
        if isinstance(source, str):
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")

        content_stripped = content.strip()
        if not content_stripped:
            return pd.DataFrame()

        try:
            raw_data = json.loads(content_stripped)
        except json.JSONDecodeError:
            # Fallback to JSON Lines (NDJSON)
            raw_data = [json.loads(line) for line in content_stripped.splitlines() if line.strip()]

        if isinstance(raw_data, dict):
            unwrapped = None
            for key in wrapper_keys:
                if key in raw_data and isinstance(raw_data[key], list):
                    unwrapped = raw_data[key]
                    break
            raw_data = unwrapped if unwrapped is not None else [raw_data]

        return pd.DataFrame(raw_data)

    return pd.read_csv(source)


def _parse_timestamp_series(series: pd.Series) -> pd.Series:
    """Parses ISO strings or numeric Unix timestamps (seconds / ms / us) into UTC Timestamps."""
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == len(series.dropna()) and numeric.notna().any():
        median_val = float(numeric.dropna().median())
        if median_val > 1e14:
            unit = "us"
        elif median_val > 1e11:
            unit = "ms"
        else:
            unit = "s"
        parsed = pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")
    else:
        parsed = pd.to_datetime(series, utc=True, errors="coerce")
    return parsed.fillna(pd.Timestamp.now(tz="UTC"))


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
    df = _load_dataframe(source, file_type, wrapper_keys=("transactions", "txs", "data", "records", "items"))
    if df.empty:
        raise ValueError("Transaction dataset is empty.")

    # Column name normalization (lowercase, stripped, special characters to underscores)
    df.columns = [_clean_column_name(c) for c in df.columns]

    # Map possible alternative names
    rename_map = {
        "txid": "tx_id",
        "tx_id": "tx_id",
        "tx_hash": "tx_id",
        "transaction_hash": "tx_id",
        "hash": "tx_id",
        "transaction_id": "tx_id",
        "transactionid": "tx_id",
        "tx": "tx_id",
        "tx_hex": "tx_id",
        "hash_id": "tx_id",
        "time": "timestamp",
        "date": "timestamp",
        "timestamp_utc": "timestamp",
        "datetime": "timestamp",
        "date_time": "timestamp",
        "block": "block_height",
        "height": "block_height",
        "block_no": "block_height",
        "senders": "sender_addresses",
        "inputs": "sender_addresses",
        "from_addresses": "sender_addresses",
        "from_address": "sender_addresses",
        "source_address": "sender_addresses",
        "receivers": "receiver_addresses",
        "outputs": "receiver_addresses",
        "to_addresses": "receiver_addresses",
        "to_address": "receiver_addresses",
        "target_address": "receiver_addresses",
        "value_btc": "amount_btc",
        "amount": "amount_btc",
        "total_btc": "amount_btc",
        "value": "amount_btc",
        "fee": "fee_btc",
        "fee_rate": "fee_rate_sat_vb",
        "fee_rate_sat": "fee_rate_sat_vb",
        "vsize": "size_vbytes",
        "size": "size_vbytes",
        "vbytes": "size_vbytes",
        "rbf": "is_rbf",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns and v not in df.columns})

    # Validate essential column: tx_id
    if "tx_id" not in df.columns:
        # Fallback: scan for any column that looks like tx / hash / id
        for candidate in ["transaction", "txid", "hash", "id"]:
            matching_cols = [c for c in df.columns if candidate in c]
            if matching_cols:
                df = df.rename(columns={matching_cols[0]: "tx_id"})
                break

    if "tx_id" not in df.columns:
        raise ValueError("Transaction dataset is missing mandatory column: 'tx_id' (or 'hash', 'tx_hash', 'transaction_id')")

    # Ensure tx_id is clean normalized string
    df = df.dropna(subset=["tx_id"]).copy()
    df["tx_id"] = df["tx_id"].apply(normalize_tx_id)
    df = df[df["tx_id"] != ""].copy()

    # Parse timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = _parse_timestamp_series(df["timestamp"])
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
    df = _load_dataframe(
        source,
        file_type,
        wrapper_keys=("network_logs", "network_observations", "observations", "logs", "data", "records", "items")
    )
    if df.empty:
        raise ValueError("Network logs dataset is empty.")

    df.columns = [_clean_column_name(c) for c in df.columns]

    rename_map = {
        # Tx ID
        "txid": "tx_id",
        "tx_id": "tx_id",
        "tx_hash": "tx_id",
        "txhash": "tx_id",
        "transaction_hash": "tx_id",
        "transactionhash": "tx_id",
        "transaction_id": "tx_id",
        "transactionid": "tx_id",
        "hash": "tx_id",
        "tx": "tx_id",
        "tx_hex": "tx_id",
        "hash_id": "tx_id",
        "transaction": "tx_id",
        # Timestamp
        "time": "timestamp_observed",
        "timestamp": "timestamp_observed",
        "observed_at": "timestamp_observed",
        "observed_time": "timestamp_observed",
        "timestamp_observed": "timestamp_observed",
        "seen_at": "timestamp_observed",
        "first_seen": "timestamp_observed",
        "first_observed": "timestamp_observed",
        "datetime": "timestamp_observed",
        "date_time": "timestamp_observed",
        "date": "timestamp_observed",
        "ts": "timestamp_observed",
        # IP
        "ip": "ip_address",
        "ip_address": "ip_address",
        "ipaddress": "ip_address",
        "peer_ip": "ip_address",
        "peer_address": "ip_address",
        "src_ip": "ip_address",
        "source_ip": "ip_address",
        "origin_ip": "ip_address",
        "host": "ip_address",
        "remote_ip": "ip_address",
        "node_ip": "ip_address",
        "address": "ip_address",
        # Node
        "node": "node_id",
        "node_id": "node_id",
        "peer": "node_id",
        "peer_id": "node_id",
        "client_id": "node_id",
        # Port
        "port": "port",
        "peer_port": "port",
        # Event
        "event": "event_type",
        "event_type": "event_type",
        "action": "event_type",
        "type": "event_type",
        "message": "event_type",
        "msg_type": "event_type",
        # Latency
        "delay_ms": "latency_ms",
        "latency": "latency_ms",
        "latency_ms": "latency_ms",
        "delay": "latency_ms",
        "rtt": "latency_ms",
        "rtt_ms": "latency_ms",
        "ping": "latency_ms",
        "ping_ms": "latency_ms",
        # Country
        "geo": "country",
        "location": "country",
        "loc": "country",
        "country": "country",
        "country_code": "country",
        "country_name": "country",
        "cc": "country",
        # ASN
        "as_number": "asn",
        "asn": "asn",
        "asn_number": "asn",
        "as": "asn",
        "autonomous_system": "asn",
        # User Agent
        "client": "user_agent",
        "version": "user_agent",
        "user_agent": "user_agent",
        "useragent": "user_agent",
        "agent": "user_agent",
        "subver": "user_agent",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns and v not in df.columns})

    if "tx_id" not in df.columns:
        # Fuzzy column scan for transaction identifier
        for candidate in ["tx", "hash", "transaction", "id"]:
            matching_cols = [c for c in df.columns if candidate in c]
            if matching_cols:
                df = df.rename(columns={matching_cols[0]: "tx_id"})
                break

    if "tx_id" not in df.columns:
        # Check if the first column has hex/hash-like values
        first_col = df.columns[0]
        sample_val = str(df[first_col].iloc[0]).strip()
        if len(sample_val) >= 8 and not sample_val.replace(".", "").isdigit():
            df = df.rename(columns={first_col: "tx_id"})
        else:
            raise ValueError(
                f"Network logs dataset is missing mandatory transaction identifier column. "
                f"Found columns: {list(df.columns)}. Expected 'tx_id', 'tx_hash', 'hash', etc."
            )

    df = df.dropna(subset=["tx_id"]).copy()
    df["tx_id"] = df["tx_id"].apply(normalize_tx_id)
    df = df[df["tx_id"] != ""].copy()

    if "log_id" not in df.columns:
        df["log_id"] = [f"net_log_{i:06d}" for i in range(len(df))]
    else:
        df["log_id"] = df["log_id"].fillna("").astype(str).str.strip()
        empty_mask = df["log_id"] == ""
        if empty_mask.any():
            df.loc[empty_mask, "log_id"] = [f"net_log_{i:06d}" for i in range(int(empty_mask.sum()))]

    if "timestamp_observed" in df.columns:
        df["timestamp_observed"] = _parse_timestamp_series(df["timestamp_observed"])
    else:
        df["timestamp_observed"] = pd.Timestamp.now(tz="UTC")

    if "node_id" not in df.columns:
        df["node_id"] = [f"node_{i % 30:03d}" for i in range(len(df))]
    else:
        df["node_id"] = df["node_id"].fillna("node_unknown").astype(str).str.strip()

    if "ip_address" not in df.columns:
        df["ip_address"] = "127.0.0.1"
    else:
        df["ip_address"] = df["ip_address"].fillna("127.0.0.1").astype(str).str.strip()

    if "port" in df.columns:
        df["port"] = pd.to_numeric(df["port"], errors="coerce").fillna(8333).astype(int)
    else:
        df["port"] = 8333

    if "event_type" not in df.columns:
        df["event_type"] = "peer_relay"
    else:
        df["event_type"] = df["event_type"].fillna("peer_relay").astype(str).str.strip().str.lower()

    if "latency_ms" in df.columns:
        df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce").fillna(45.0)
    else:
        df["latency_ms"] = 45.0

    if "country" not in df.columns:
        df["country"] = "UNKNOWN"
    else:
        df["country"] = df["country"].fillna("UNKNOWN").astype(str).str.strip().str.upper()

    if "asn" not in df.columns:
        df["asn"] = "UNKNOWN"
    else:
        df["asn"] = df["asn"].fillna("UNKNOWN").astype(str).str.strip().str.upper()

    if "user_agent" not in df.columns:
        df["user_agent"] = "/Satoshi:25.0.0/"
    else:
        df["user_agent"] = df["user_agent"].fillna("/Satoshi:25.0.0/").astype(str).str.strip()

    return df

