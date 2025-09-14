from icmplib import ping


def can_send_icmp(host: str, count: int, timeout: int) -> bool:
    return ping(host, count=count, timeout=timeout).is_alive
