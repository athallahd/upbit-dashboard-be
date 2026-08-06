import os

import requests
from dotenv import load_dotenv


load_dotenv()


class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.url = os.getenv('SLACK_INCOMING_WEBHOOK_URL')
        self.post_message_url = os.getenv(
            'SLACK_POST_MESSAGE_URL',
            'https://slack.com/api/chat.postMessage',
        )

    def _webhook_url(self):
        if not self.url:
            raise RuntimeError(
                'SLACK_INCOMING_WEBHOOK_URL is not configured; '
                'set it in the environment before sending Slack messages.'
            )
        return self.url


    def send_file_check_message(self, success_file_name, failed_file_name):
        r = self.session.post(
            self._webhook_url(),
            timeout=10,
            json={
                "text": "Daily report notification",
                "blocks": [
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":newspaper: Daily report file creation result ",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• File creation success: *{success_file_name}*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• File creation failed: *{failed_file_name}*"
                        }
                    },
                    # {
                    #     "type": "section",
                    #     "text": {
                    #         "type": "mrkdwn",
                    #         "text": "cc <@U0165LN0YTT>"
                    #     }
                    # },
                    {
                        "type": "divider"
                    }
                ]
            },
        )
        r.raise_for_status()
        return


    def send_upload_message(self, res_orderbook, res_dtw, res_tradebook):
        r = self.session.post(
            self._webhook_url(),
            timeout=10,
            json={
                "text": "Daily report notification",
                "blocks": [
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":newspaper: Daily report file upload result ",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• File upload result:\n"
                                    f"Orderbook - {res_orderbook},\n"
                                    f"dtw - {res_dtw},\n"
                                    f"tradebook - {res_tradebook}"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            },
        )
        r.raise_for_status()
        return


    def send_retry_message(self):
        r = self.session.post(
            self._webhook_url(),
            timeout=10,
            json={
                "text": "Daily report notification",
                "blocks": [
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":newspaper: Re-creation of failed daily report file ",
                            "emoji": True
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            }
        )
        r.raise_for_status()
        return


    def report_account_version_count(self, response_dict):
        r = self.session.post(
            self._webhook_url(),
            timeout=10,
            json={
                "text": "Daily report notification",
                "blocks": [
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📰 Daily Trade, Deposit and Withdraw Transaction Count",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• Trade Count in Account Version: *{response_dict.get('av_trade_count')}*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• Trade Count in Tradebook: *{response_dict.get('tb_count')}*"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• Withdraw Count in Account Version: *{response_dict.get('av_withdraw_count')}*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• Withdraw Count in DTW: *{response_dict.get('dtw_df_withdraw')}*"
                        }
                    },
                    {
                        "type": "divider"
                    },
                                        {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• Deposit Count in Account Version: *{response_dict.get('av_deposit_count')}*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• Deposit Count in DTW: *{response_dict.get('dtw_df_deposit')}*"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            },
        )
        r.raise_for_status()
        return
    
    
    def report_self_match_count(self, count_of_self_match):
        r = self.session.post(
            self._webhook_url(),
            timeout=10,
            json={
                "text": "Daily report notification",
                "blocks": [
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":newspaper: Daily report self match count",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• Self match count: *{count_of_self_match}*"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            },
        )
        r.raise_for_status()
        return
    

    def upbit_cs_th_db_message(self):
        r = self.session.post(
            self._webhook_url(),
            timeout=10,
            json={
                "text": "Database check notification",
                "blocks": [
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":newspaper: upbit-cs-th record check",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• upbit-cs-th might not up-to-date. Please check"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            },
        )
        r.raise_for_status()
        return


    def post_message(self, token, channel_id, text, block_list):
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer {}'.format(token)
        }
        payload = {
            'channel': channel_id,
            'text': text,
            'blocks': block_list
        }
        r = self.session.post(
            self.post_message_url,
            timeout=10,
            headers=headers,
            json=payload
        )
        r.raise_for_status()
        return r
