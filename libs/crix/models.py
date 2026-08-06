import typing
from dataclasses import dataclass


@dataclass
class MarketPrice:
    code: str
    tradePrice: float
    timestamp: int
    error_code: typing.Optional[str]
