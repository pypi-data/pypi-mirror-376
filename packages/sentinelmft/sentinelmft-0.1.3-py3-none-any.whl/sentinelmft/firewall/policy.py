from typing import List

def ip_allowed(ip: str, allowlist: List[str] | None) -> bool:
    if not allowlist:
        return True
    return ip in allowlist

