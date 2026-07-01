from dataclasses import dataclass


@dataclass
class RedisCmd:
    cmd: str
    args: list[str]