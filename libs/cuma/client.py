import requests
from dacite import from_dict
from django.conf import settings

from libs.cuma.model import VirtualBankAccount


class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'upbitit/reporter ({settings.GIT_REV})',
            'X-Api-Key': settings.CUMA_API_KEY,
        })
        self.base_url = settings.CUMA_API_URL

    def callback_thb_generate_vba(self, tx_id: str) -> VirtualBankAccount:
        r = self.session.post(
            f'{self.base_url}/api/v1/callbacks/thb/gen_virtual_bank_account',
            json=dict(tx_id=tx_id),
        )
        r.raise_for_status()

        # todo: logging to db?

        return from_dict(VirtualBankAccount, data=r.json())

    def get(self):
        ...
