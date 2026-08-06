import typing
from dataclasses import dataclass


@dataclass
class VirtualBankAccount:
    uuid: str
    bank: str
    account_number: str
    state: str
    error_code: typing.Optional[str]
