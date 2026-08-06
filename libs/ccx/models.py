from dataclasses import dataclass


@dataclass
class WalletAddress:
    wallet_addresses: list


@dataclass()
class DecryptData:
    decrypted_data: str
