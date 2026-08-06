import requests
from dacite import from_dict
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from libs.ccx.models import DecryptData, WalletAddress


class Client:
    def __init__(self):
        self.session = requests.Session()

        retries = Retry(total=5,
                        backoff_factor=5,
                        status_forcelist=[500, 502, 503, 504])

        self.session.mount('http://', HTTPAdapter(max_retries=retries))

        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Api-Key': settings.EXCHANGE_API_KEY,
        })
        self.base_url = settings.EXCHANGE_API_URL

        conn_timeout = 3
        read_timeout = 20

        self.timeouts = (conn_timeout, read_timeout)


    def currency_hot_wallet_address(self, currency):
        # try:
        #     r = self.session.get(
        #         f'{self.base_url}/api/v1/integrations/wallet_manager/currency_hot_wallet_address',
        #         params={'currency': currency},
        #         timeout=self.timeouts
        #     )
        #     if r.status_code == 200:
        #         return from_dict(WalletAddress, data=r.json())
        #     else:
        #         return from_dict(WalletAddress, data={'wallet_addresses': ['']})
        # except:
        #     return from_dict(WalletAddress, data={'wallet_addresses': ['']})
        
        return from_dict(WalletAddress, data={'wallet_addresses': ['partnerexchangewallet']})


    def currency_cold_wallet_address(self, currency):
        r = self.session.get(
            f'{self.base_url}/api/v1/integrations/wallet_manager/currency_cold_wallet_address',
            params={'currency': currency},
            timeout=self.timeouts
        )
        r.raise_for_status()

        return from_dict(WalletAddress, data=r.json())

    def decrypt_data(self, encrypted_data, salt):
        r = self.session.get(
            f'{self.base_url}/api/v1/integrations/encryption/decrypt',
            params={'encrypted_data': encrypted_data,
                    'salt': salt},
            timeout=self.timeouts
        )
        r.raise_for_status()

        return from_dict(DecryptData, data=r.json())
