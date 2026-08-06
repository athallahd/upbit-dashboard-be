from libs.cuma.client import Client
from libs.cuma.model import VirtualBankAccount

cuma_client = Client()

__all__ = ['cuma_client', 'VirtualBankAccount']
