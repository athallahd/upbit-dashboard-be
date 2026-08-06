import base64
import datetime

import requests
from django.conf import settings


def get_monthly_encryption_key(today):
    # Get previous month first day DATETIME object
    monthly_date = (today - datetime.timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_encryption_key, iv = get_encryption_key(monthly_date)
    return monthly_encryption_key, iv


def get_encryption_key(target_date, api_key=None, api_secret=None):
    if api_key:
        access_token = get_token(api_key, api_secret)
    else:
        access_token = get_token(settings.SEC_API_KEY, settings.SEC_API_SECRET)

    data = {
        'date': target_date.strftime('%Y-%m-%d')
    }
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token)
    }
    r = requests.post('{0}/api/DataKey/getEncryptionKey'.format(settings.SEC_API_URI), json=data, headers=headers)
    return_data = r.json()
    encrypt_key = return_data.get('encryptKey')
    iv = base64.b64decode(encrypt_key.split('.')[1])
    encrypt_key = base64.b64decode(encrypt_key.split('.')[0])
    return encrypt_key, iv


def get_token(api_key, api_secret):
    data = {
        'api_key': api_key,
        'api_secret': api_secret
    }
    r = requests.post('{0}/getToken'.format(settings.SEC_API_URI), json=data)
    return_data = r.json()
    access_token = return_data.get('access_token')
    return access_token


def initialize_file_upload(file_name, file_size, sec_api_key=None, sec_api_secret=None):
    if not sec_api_key:
        sec_api_key = settings.SEC_API_KEY
        sec_api_secret = settings.SEC_API_SECRET

    access_token = get_token(sec_api_key, sec_api_secret)

    data = {
        'fileName': file_name,
        'fileSize': file_size
    }
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token)
    }
    r = requests.post('{0}/api/File/initial'.format(settings.SEC_API_URI), json=data, headers=headers)
    return_data = r.json()
    print(data)
    print('---')
    print(return_data)
    upload_url = return_data.get('uploadUrl')
    file_id = return_data['fileSplit'][0]['id'] if return_data.get('fileSplit') else None

    res_msg = return_data.get('errors') if return_data.get('errors') else "not errors"
    return upload_url, file_id, res_msg


def upload_file(upload_url, file_id, file_name, file_data, sec_api_key=None, sec_api_secret=None):
    if not sec_api_key:
        sec_api_key = settings.SEC_API_KEY
        sec_api_secret = settings.SEC_API_SECRET

    is_success = False
    try:
        for i in range(5):
            access_token = get_token(sec_api_key, sec_api_secret)
            headers = {
                'Authorization': 'Bearer {0}'.format(access_token),
                'FileID': file_id,
                'Content-Type': 'application/octet-stream'
            }
            r = requests.post(upload_url, data=file_data, headers=headers)
            return_data = r.json()
            print(return_data)
            result_code = return_data.get('message_code')
            if result_code == 'I003':
                is_success = True
                break
    except Exception as e:
        return False, str(e)

    return is_success, str(return_data)
