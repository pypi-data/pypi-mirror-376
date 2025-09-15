from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import yaml, json, os

@dataclass
class GCSConfig:
    project: Optional[str] = None
    bucket: Optional[str] = None

@dataclass
class SecurityConfig:
    keyfile: Optional[str] = None  # path to AES key (32 bytes)
    allow_ips: Optional[List[str]] = None

@dataclass
class AppConfig:
    gcs: GCSConfig
    security: SecurityConfig
    extras: Dict[str, Any]

def load_config(path: str) -> AppConfig:
    with open(path, "r") as f:
        data = yaml.safe_load(f) if path.endswith((".yml",".yaml")) else json.load(f)
    gcs = GCSConfig(**data.get("gcs", {}))
    sec = SecurityConfig(**data.get("security", {}))
    extras = data.get("extras", {})
    return AppConfig(gcs=gcs, security=sec, extras=extras)

def load_key(keyfile: str) -> bytes:
    with open(keyfile, "rb") as f:
        key = f.read().strip()
    if len(key) != 32:
        raise ValueError("AES-256 key must be 32 bytes.")
    return key
