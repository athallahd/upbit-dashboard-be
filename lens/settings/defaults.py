import logging
import os

from dotenv import find_dotenv, load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(find_dotenv(), encoding='utf-8')

LOCAL_TIME_DELTA = os.getenv('LOCAL_TIME_DELTA', default=7)
LOCAL_TIMEZONE = os.getenv('LOCAL_TIMEZONE', default='Asia/Jakarta')
LOCAL_TIME_ZERO = os.getenv('LOCAL_TIME_ZERO', default=17)
CURRENCY_CODE = os.getenv('CURRENCY_CODE', default='IDR')
LOCAL_API_PREFIX = os.getenv('LOCAL_API_PREFIX', default='id-api')

SECRET_KEY = os.getenv('SECRET_KEY', default='keykeykikiki123ki@#$')

PROJECT_ENV = os.getenv('PROJECT_ENV', default='').lower()

DEBUG = True if PROJECT_ENV == 'local' else False

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'lens',
    'trigger',
    'masterdata',
    'snapshot',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_saml2_auth',
    'django_filters',
    'rest_framework',
    'rangefilter',
    'lens_csv',
    'lens_data',
    'lens_monitoring',
    'executive_dashboard',
]

# for admin modal interfaces

X_FRAME_OPTIONS = 'SAMEORIGIN'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'lens.middlewares.SAMLRequiredMiddleware',
]

SESSION_COOKIE_AGE = 3600

SESSION_SAVE_EVERY_REQUEST = True

ROOT_URLCONF = 'lens.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lens.wsgi.application'

DATABASES = {
    # CCX
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('SEC_DATABASE'),
        'USER': os.getenv('SEC_USER'),
        'PASSWORD': os.getenv('SEC_PASSWORD'),
        'HOST': os.getenv('SEC_HOST'),
        'PORT': os.getenv('SEC_PORT', default=3306),
        'OPTIONS': {
            'isolation_level': 'REPEATABLE READ',
            "ssl": {},
            "ssl_mode": "REQUIRED",
        }
    },
    'reporter': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('SEC_DATABASE'),
        'USER': os.getenv('SEC_USER'),
        'PASSWORD': os.getenv('SEC_PASSWORD'),
        'HOST': os.getenv('SEC_HOST'),
        'PORT': os.getenv('SEC_PORT', default=3306),
        'OPTIONS': {
            'isolation_level': 'REPEATABLE READ',
            "ssl": {},
            "ssl_mode": "REQUIRED",
        }
    },
}

DATABASE_ROUTERS = ['lens.routers.AuthRouter']

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Rest framework settings.

# Rest framework settings.

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.TokenAuthentication',
        'lens.authentication.OktaAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}

# Application settings

GIT_REV = os.getenv('GIT_REV')
logging.info(f"GIT_REV: {GIT_REV}")

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

CLOUDFLARE_AUTH_POLICY_AUD = os.getenv('CLOUDFLARE_AUTH_POLICY_AUD')
CLOUDFLARE_AUTH_DOMAIN = os.getenv('CLOUDFLARE_AUTH_DOMAIN')

LICENSE_NUMBER = os.getenv('LICENSE_NUMBER')
COMPANY_ID = os.getenv('COMPANY_ID')

CRIX_API_URL = os.getenv('CRIX_API_URL')

ORDER_PER_PAGING = os.getenv('ORDER_PER_PAGING') or 1000

KYC_ENCRYPTION_KEY = os.getenv('KYC_ENCRYPTION_KEY')

EXCHANGE_API_URL = os.getenv('EXCHANGE_API_URL')
EXCHANGE_API_KEY = os.getenv('EXCHANGE_API_KEY')

WALLET_API_KEY = os.getenv('WALLET_API_KEY')
KR_API_GATEWAY_KEY = os.getenv('KR_API_GATEWAY_KEY')

UPBIT_KR_BUSINESS_NO = os.getenv('UPBIT_KR_BUSINESS_NO')

FILEBROWSER_DIRECTORY = ''
MEDIA_ROOT = 'data/'

TMS_URL = os.getenv('TMS_URL')
TMS_USERNAME = os.getenv('TMS_USERNAME')
TMS_PASSWORD = os.getenv('TMS_PASSWORD')

DUKCAPIL_URL = os.getenv('DUKCAPIL_URL', default="http://202.165.33.154:8800/dukcapil/get_json/990042423040001/CALL_VERIFY_BY_ELEMEN")
DUKCAPIL_USERNAME = os.getenv('DUKCAPIL_USERNAME', default="130220241547519900424230400016829")
DUKCAPIL_PASSWORD = os.getenv('DUKCAPIL_PASSWORD')

CFX_API_KEY = os.getenv('CFX_API_KEY')

LOCAL_CODE = 'id'

# SILENCED_SYSTEM_CHECKS = ['models.E026','fields.W122']

SAML2_AUTH = {
    'METADATA_AUTO_CONF_URL': 'https://dunamu.okta.com/app/exkd49msvaApjmOPv697/sso/saml/metadata',
    'DEFAULT_NEXT_URL': '/admin/',
    'CREATE_USER': False,
    'DEBUG': False,
    'TOKEN_REQUIRED': False,
    'ATTRIBUTES_MAP': {
        'email': 'Email',
        'username': 'UserName',
        'first_name': 'FirstName',
        'last_name': 'LastName',
    },
    # triggers can be used to perform various task. Before_login is triggered right when the saml response comes form idp
    'TRIGGER': {
    },
    # 'ASSERTION_URL': 'https://id-lens.idnprod.upbitit.pro', # Custom URL to validate incoming SAML requests against
    'ASSERTION_URL': 'https://id-lens.idnprod.upbitapac.io', # Custom URL to validate incoming SAML requests against
    # 'ENTITY_ID': 'https://id-lens.idnprod.upbitit.pro/saml2_auth/acs/', # Populates the Issuer element in authn request
    'ENTITY_ID': 'https://id-lens.idnprod.upbitapac.io/saml2_auth/acs/', # Populates the Issuer element in authn request
    'NAME_ID_FORMAT': "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress", # Sets the Format property of authn NameIDPolicy element
}

TASKS_LIST = {
    'reporting': [
        'Daily_Trade_Value_OJK',
        'Monthly_Transaction_Top25_OJK',
        'Monthly_User_Movement_OJK',
        'Monthly_Withdraw_Top25_OJK',
        'Daily_Crypto_Balance_OJK',
        'Daily_Crypto_Recap_OJK',
        'Monthly_Deposit_Top25_OJK',
        'Monthly_Tax_Detail_Report',
        'Monthly_Transaction_Detail_ID',
    ],
    'fa': [
        'Daily_UserBalance',
        'Daily_Crypto_Balance_OJK',
        'Monthly_Trade_BTC_OJK',
        'Monthly_Trade_IDR_OJK',
        'Monthly_Trade_USDT_OJK',
        'Monthly_Trade_BTC',
        'Monthly_Trade_IDR',
        'Monthly_Trade_USDT',
        'Monthly_Dealer_ID_Balance',
        'Monthly_Dealer_id_DTW',
        'Monthly_ID_Wallet_Balance',
        'Monthly_id_Wallet_DTW',
        'Monthly_Tax_Summary',
        'Monthly_500_Top_Trader',
        'Monthly_Withdraw_DigitalAsset',
        'Monthly_Withdraw_IDR',
        'Monthly_Transaction_Detail_ID',
        'Monthly_Tax_Detail_Report_UTC',
        'Monthly_Tax_Detail_Report_GMT+7',
        'Monthly_Asset_Movement',
        'Monthly_RS_Settlement',
        'Monthly_Withdrawal_fee',
        'Monthly_Detail_Trader_UTC',
        'Monthly_Detail_Trader_GMT+7',
        'Monthly_Detail_Trader_Pair_UTC',
        'Monthly_Detail_Trader_Pair_GMT+7'
    ],
    'kyt': [
        'Monthly_Withdraw_DigitalAsset',
        'Monthly_Withdraw_IDR',
        'Monthly_Transaction_Detail_ID',
        'Daily_CryptoBalance',
        'Monthly_DepositsTop10_Report',
        'Monthly_DepositWithdraw_User10B',
        'Monthly_Transaction_Top25_OJK',
        'Monthly_Withdraw_Top25_OJK',
        'Monthly_Deposit_Top25_OJK'
    ]
}

# Okta JWT configuration
OKTA_DOMAIN = os.getenv('OKTA_DOMAIN')
OKTA_AUDIENCE = os.getenv('OKTA_AUDIENCE')
OKTA_CLIENT_ID = os.getenv('OKTA_CLIENT_ID')

# Executive Dashboard configuration. The SQL-owned dashboard table and its
# source tables are read/written through the reporter connection by default.
DASHBOARD_DB_ALIAS = os.getenv('DASHBOARD_DB_ALIAS', default='reporter')
DASHBOARD_APPROVED_SECURITY_LEVEL = int(
    os.getenv('DASHBOARD_APPROVED_SECURITY_LEVEL', default='2')
)
DASHBOARD_DORMANT_DAYS = int(os.getenv('DASHBOARD_DORMANT_DAYS', default='180'))
DASHBOARD_REVENUE_FIELD = os.getenv('DASHBOARD_REVENUE_FIELD', default='fiat_fee')

# CORS settings
CORS_ALLOWED_ORIGINS = [
    os.getenv('CORS_ALLOWED_ORIGIN', default="http://localhost:3000")
]

CORS_ALLOW_CREDENTIALS = True
