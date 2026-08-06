import time

import requests
from dacite import from_dict
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from libs.crix.models import MarketPrice


class Client:
    def __init__(self):
        self.session = requests.Session()

        retries = Retry(total=3,
                        backoff_factor=0.1,
                        status_forcelist=[500, 502, 503, 504])

        self.session.mount('http://', HTTPAdapter(max_retries=retries))

        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        self.base_url = settings.CRIX_API_URL

        conn_timeout = 1
        read_timeout = 5

        self.timeouts = (conn_timeout, read_timeout)

    def fiat_price_with_time(self, currency, _time, fiat='THB'):
        # crix 호출시에는 UNI로 호출.
        if currency == "UNISWAP":
            currency = "UNI"
        if currency == "Gitcoin":
            currency = "GTC"
        if currency == "Radicle":
            currency = "RAD"
        if currency == "BTT20":
            currency = "BTT"

        pairs = [f'{fiat}-{currency}']

        timestamp = int(time.mktime(_time.timetuple()) * 1000)

        return self.market_prices(pairs, timestamp)

    def market_prices(self, pairs, _time, filtered_by_master='true'):
        r = self.session.get(
            f'{self.base_url}/v1/crix/integrations/ccx/prices',
            params={'exchange': 'UPBIT',
                    'filteredByMaster': filtered_by_master,
                    'pairs': pairs,
                    'time': _time},
            timeout=self.timeouts
        )

        r.raise_for_status()

        if not r.json():
            code = pairs[0].split('-')[1] if pairs[0].split('-')[1] else '-'
            default_json = {'code': code, 'tradePrice': 0.00, 'timestamp': _time, 'error_code': None}
            return from_dict(MarketPrice, default_json)

        return from_dict(MarketPrice, data=r.json()[0])
