from masterdata.models.sec import ParamValues
from enum import Enum
from django.conf import settings

local_currency = settings.CURRENCY_CODE

# Wash trade ruleset
class WashTradeParams(Enum):
    p1_obj = ParamValues.objects.filter(param_master__param_key='wash_trade', param_master__param_field='p1_lv1_ratio').order_by('-created_at').first()
    p2_obj = ParamValues.objects.filter(param_master__param_key='wash_trade', param_master__param_field='p2_lv2_ratio').order_by('-created_at').first()
    p3_obj = ParamValues.objects.filter(param_master__param_key='wash_trade', param_master__param_field='p3_lv3_ratio').order_by('-created_at').first()
    p4_obj = ParamValues.objects.filter(param_master__param_key='wash_trade', param_master__param_field='p4_simul_entry').order_by('-created_at').first()
    p5_obj = ParamValues.objects.filter(param_master__param_key='wash_trade', param_master__param_field='p5_trade_vol').order_by('-created_at').first()
        
    if(((p1_obj is None)| (p2_obj is None)| (p3_obj is None)| (p4_obj is None)| (p5_obj is None))):
        form_data = {
            'ruleset_name':'Wash trade monitoring',
            'celery_name':'LENs_Wash_Trade_APAC',
            'task_name':'libs.lens.output_tasks.lens_wash_trade_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Trade frequency threshold lv1 (p1):', 'type':'IntegerField', 'help_text':f'time(s) (default:{6})', 'default':6},
                {'param_name':'p2', 'label':'Trade frequency threshold lv2 (p2):', 'type':'IntegerField', 'help_text':f'time(s) (default:{8})', 'default':8},
                {'param_name':'p3', 'label':'Trade frequency threshold lv3 (p3):', 'type':'IntegerField', 'help_text':f'time(s) (default:{10})', 'default':10},
                {'param_name':'p4', 'label':'Simultaneous order window (p4):', 'type':'IntegerField', 'help_text':f'minute(s) (default:{5})', 'default':5},
                {'param_name':'p5', 'label':'Volume threshold (p5):', 'type':'DecimalField', 'help_text':f'Volume threshold (p5): (default:{50000}{local_currency})', 'default':50000},
            ]
        }
    else:
        p1_lv1_ratio = p1_obj.param_value
        p2_lv2_ratio = p2_obj.param_value
        p3_lv3_ratio = p3_obj.param_value
        p4_simul_entry = p4_obj.param_value
        p5_trade_vol = p5_obj.param_value

        tag = ','.join([p1_obj.params_tag, p2_obj.params_tag, p3_obj.params_tag, p4_obj.params_tag, p5_obj.params_tag])
        form_data = {
            'ruleset_name':'Wash trade monitoring',
            'celery_name':'LENs_Wash_Trade_APAC',
            'task_name':'libs.lens.output_tasks.lens_wash_trade_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Trade frequency threshold lv1 (p1):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p1_lv1_ratio})', 'default':p1_lv1_ratio},
                {'param_name':'p2', 'label':'Trade frequency threshold lv2 (p2):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p2_lv2_ratio})', 'default':p2_lv2_ratio},
                {'param_name':'p3', 'label':'Trade frequency threshold lv3 (p3):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p3_lv3_ratio})', 'default':p3_lv3_ratio},
                {'param_name':'p4', 'label':'Simultaneous order window (p4):', 'type':'IntegerField', 'help_text':f'minute(s) (default:{p4_simul_entry})', 'default':p4_simul_entry},
                {'param_name':'p5', 'label':'Volume threshold (p5):', 'type':'DecimalField', 'help_text':f'Volume threshold (p5): (default:{p5_trade_vol}{local_currency})', 'default':p5_trade_vol},
            ]
        }

# FATF ruleset
class FATFParams(Enum):
    p1_obj = ParamValues.objects.filter(param_master__param_key='fatf', param_master__param_field='p1_fatf_countries_list').order_by('-created_at').first()

    if(p1_obj is None):
        form_data = {
            'ruleset_name':'FATF monitoring',
            'celery_name':'LENs_FATF_Monitoring_APAC',
            'task_name':'libs.lens.output_tasks.lens_fatf_monitoring_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Countries code:', 'type':'CharField', 'help_text':f'Input format must be country code seperated by | eg. KP|IR|MM, You can find country code here : https://www.iban.com/country-codes', 'default':'KP|IR|MM|BG|BF|CD|HR|HT|JM|KE|ML|PH|SN|ZA|SS|SY|TR|VN|YE|AF|DZ|AW|BD|BJ|BI|CM|TD|CN|CU|DJ|EG|ER|ET|GH|GY|HN|IQ|CI|XK|MA|MZ|NA|NP|NG|PK|QA|CG|RW|RS|KR|LK|TJ|TZ|TG|TT|TN|TM|UG|US|UZ|VE'}
            ]
        }
    else:
        p1_fatf_countries_list = p1_obj.param_value
        tag = p1_obj.params_tag    
        form_data = {
            'ruleset_name':'FATF monitoring',
            'celery_name':'LENs_FATF_Monitoring_APAC',
            'task_name':'libs.lens.output_tasks.lens_fatf_monitoring_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Countries code:', 'type':'CharField', 'help_text':f'Input format must be country code seperated by | eg. KP|IR|MM, You can find country code here : https://www.iban.com/country-codes', 'default':p1_fatf_countries_list}
            ]
        }

    fatf_countries_object = [
        {'country_code':'KP', 'fatf_level':'black'},#North Korea
        {'country_code':'IR', 'fatf_level':'black'},#Iran
        {'country_code':'MM', 'fatf_level':'black'},#Myanmar

        {'country_code':'BG', 'fatf_level':'grey'},#Bulgaria
        {'country_code':'BF', 'fatf_level':'grey'},#Burkina Faso
        {'country_code':'CD', 'fatf_level':'grey'},#Congo (the Democratic Republic of the)
        {'country_code':'HR', 'fatf_level':'grey'},#Croatia
        {'country_code':'HT', 'fatf_level':'grey'},#Haiti
        {'country_code':'JM', 'fatf_level':'grey'},#Jamaica
        {'country_code':'KE', 'fatf_level':'grey'},#Kenya
        {'country_code':'ML', 'fatf_level':'grey'},#Mali
        {'country_code':'PH', 'fatf_level':'grey'},#Philippines (the)
        {'country_code':'SN', 'fatf_level':'grey'},#Senegal
        {'country_code':'ZA', 'fatf_level':'grey'},#South Africa
        {'country_code':'SS', 'fatf_level':'grey'},#South Sudan
        {'country_code':'SY', 'fatf_level':'grey'},#Syrian Arab Republic
        {'country_code':'TR', 'fatf_level':'grey'},#Turkey
        {'country_code':'VN', 'fatf_level':'grey'},#Vietnam
        {'country_code':'YE', 'fatf_level':'grey'},#Yemen
        #----------- this both internal and grey
        # {'country_code':'CM', 'fatf_level':'internal deny'},
        # {'country_code':'MZ', 'fatf_level':'internal deny'},
        # {'country_code':'NA', 'fatf_level':'internal deny'},
        # {'country_code':'NG', 'fatf_level':'internal deny'},
        # {'country_code':'CG', 'fatf_level':'internal deny'},
        # {'country_code':'TZ', 'fatf_level':'internal deny'},
        {'country_code':'AF', 'fatf_level':'internal deny'},#Afghanistan
        {'country_code':'DZ', 'fatf_level':'internal deny'},#Algeria
        {'country_code':'AW', 'fatf_level':'internal deny'},#Aruba
        {'country_code':'BD', 'fatf_level':'internal deny'},#Bangladesh
        {'country_code':'BJ', 'fatf_level':'internal deny'},#Benin
        {'country_code':'BI', 'fatf_level':'internal deny'},#Burundi
        {'country_code':'CM', 'fatf_level':'internal deny'},#Cameroon
        {'country_code':'TD', 'fatf_level':'internal deny'},#Chad
        {'country_code':'CN', 'fatf_level':'internal deny'},#China
        {'country_code':'CU', 'fatf_level':'internal deny'},#Cuba
        {'country_code':'DJ', 'fatf_level':'internal deny'},#Djibouti
        {'country_code':'EG', 'fatf_level':'internal deny'},#Egypt
        {'country_code':'ER', 'fatf_level':'internal deny'},#Eritea
        {'country_code':'ET', 'fatf_level':'internal deny'},#Ethiopia
        {'country_code':'GH', 'fatf_level':'internal deny'},#Ghana
        {'country_code':'GY', 'fatf_level':'internal deny'},#Guyana
        {'country_code':'HN', 'fatf_level':'internal deny'},#Honduras
        {'country_code':'IQ', 'fatf_level':'internal deny'},#Iraq
        {'country_code':'CI', 'fatf_level':'internal deny'},#Ivory Coast
        {'country_code':'XK', 'fatf_level':'internal deny'},#Kosovo
        {'country_code':'MA', 'fatf_level':'internal deny'},#Morocco
        {'country_code':'MZ', 'fatf_level':'internal deny'},#Mozambique
        {'country_code':'NA', 'fatf_level':'internal deny'},#Namibia
        {'country_code':'NP', 'fatf_level':'internal deny'},#Nepal
        {'country_code':'NG', 'fatf_level':'internal deny'},#Nigeria
        {'country_code':'PK', 'fatf_level':'internal deny'},#Pakistan
        {'country_code':'QA', 'fatf_level':'internal deny'},#Qatar
        {'country_code':'CG', 'fatf_level':'internal deny'},#Congo (the Replublic of)
        {'country_code':'RW', 'fatf_level':'internal deny'},#Rwanda
        {'country_code':'RS', 'fatf_level':'internal deny'},#Serbia
        {'country_code':'KR', 'fatf_level':'internal deny'},#South Korea
        {'country_code':'LK', 'fatf_level':'internal deny'},#Sri Lanka
        {'country_code':'TJ', 'fatf_level':'internal deny'},#Tajikistan
        {'country_code':'TZ', 'fatf_level':'internal deny'},#Tanzania
        {'country_code':'TG', 'fatf_level':'internal deny'},#Togo
        {'country_code':'TT', 'fatf_level':'internal deny'},#Trinidad and tobago
        {'country_code':'TN', 'fatf_level':'internal deny'},#Tunisia
        {'country_code':'TM', 'fatf_level':'internal deny'},#Turkmenistan
        {'country_code':'UG', 'fatf_level':'internal deny'},#Uganda
        {'country_code':'US', 'fatf_level':'internal deny'},#USA
        {'country_code':'UZ', 'fatf_level':'internal deny'},#Uzbekistan
        {'country_code':'VE', 'fatf_level':'internal deny'},#Venezuela
    ]

# Pump and dump ruleset
# class PumpDumpParams(Enum):
#     p1_obj = ParamValues.objects.filter(param_master__param_key='pump_dump', param_master__param_field='p1_lv1_ratio').order_by('-created_at').first()
#     p2_obj = ParamValues.objects.filter(param_master__param_key='pump_dump', param_master__param_field='p2_lv2_ratio').order_by('-created_at').first()
#     p3_obj = ParamValues.objects.filter(param_master__param_key='pump_dump', param_master__param_field='p3_lv3_ratio').order_by('-created_at').first()

#     if((p1_obj is None)|(p2_obj is None)|(p3_obj is None)):
#         form_data = {
#             'ruleset_name':'Pump and dump monitoring',
#             'celery_name':'LENs_Pump_Dump_APAC',
#             'task_name':'libs.lens.output_tasks.lens_pump_dump_apac.start',
#             'fields':[
#                 {'param_name':'p1', 'label':'Pump and dump level 1 threshold (p1):', 'type':'DecimalField', 'help_text':f'percent (default:{20})', 'default':20},
#                 {'param_name':'p2', 'label':'Pump and dump level 2 threshold (p2):', 'type':'DecimalField', 'help_text':f'percent (default:{25})', 'default':25},
#                 {'param_name':'p3', 'label':'Pump and dump level 3 threshold (p3):', 'type':'DecimalField', 'help_text':f'percent (default:{30})', 'default':30},
#             ]
#         }
#     else:
#         p1_lv1_ratio = p1_obj.param_value
#         p2_lv2_ratio = p2_obj.param_value
#         p3_lv3_ratio = p3_obj.param_value
#         tag = ','.join([p1_obj.params_tag, p2_obj.params_tag, p3_obj.params_tag])

#         form_data = {
#             'ruleset_name':'Pump and dump monitoring',
#             'celery_name':'LENs_Pump_Dump_APAC',
#             'task_name':'libs.lens.output_tasks.lens_pump_dump_apac.start',
#             'fields':[
#                 {'param_name':'p1', 'label':'Pump and dump level 1 threshold (p1):', 'type':'DecimalField', 'help_text':f'percent (default:{p1_lv1_ratio})', 'default':p1_lv1_ratio},
#                 {'param_name':'p2', 'label':'Pump and dump level 2 threshold (p2):', 'type':'DecimalField', 'help_text':f'percent (default:{p2_lv2_ratio})', 'default':p2_lv2_ratio},
#                 {'param_name':'p3', 'label':'Pump and dump level 3 threshold (p3):', 'type':'DecimalField', 'help_text':f'percent (default:{p3_lv3_ratio})', 'default':p3_lv3_ratio},
#             ]
#         }

# account takeover ruleset
# class AccountTakeoverParams(Enum):
#     p1_obj = ParamValues.objects.filter(param_master__param_key='account_takeover', param_master__param_field='p1_acc_takeover_lookback_days').order_by('-created_at').first()
#     p2_obj = ParamValues.objects.filter(param_master__param_key='account_takeover', param_master__param_field='p2_acc_takeover_pct_threshold').order_by('-created_at').first()

#     if((p1_obj is None)|(p2_obj is None)):
#         form_data={
#             'ruleset_name':'Account takeover monitoring',
#             'celery_name':'LENs_Account_Takeover_APAC',
#             'task_name':'libs.lens.output_tasks.lens_account_takeover_apac.start',
#             'fields':[
#                 {'param_name':'p1', 'label':'Account takeover lookback days (p1):', 'type':'DecimalField', 'help_text':f'day(s) (default:{90})', 'default':90},
#                 {'param_name':'p2', 'label':'Account takeover pct threshold (p2):', 'type':'DecimalField', 'help_text':f'pct(s) (default:{150})', 'default':150},
#             ]
#     }
#     else:
#         p1_acc_takeover_lookback_days = p1_obj.param_value
#         p2_acc_takeover_pct_threshold = p2_obj.param_value
#         tag = ','.join([p1_obj.params_tag, p2_obj.params_tag])
#         form_data={
#             'ruleset_name':'Account takeover monitoring',
#             'celery_name':'LENs_Account_Takeover_APAC',
#             'task_name':'libs.lens.output_tasks.lens_account_takeover_apac.start',
#             'fields':[
#                 {'param_name':'p1', 'label':'Account takeover lookback days (p1):', 'type':'DecimalField', 'help_text':f'day(s) (default:{p1_acc_takeover_lookback_days})', 'default':p1_acc_takeover_lookback_days},
#                 {'param_name':'p2', 'label':'Account takeover pct threshold (p2):', 'type':'DecimalField', 'help_text':f'pct(s) (default:{p2_acc_takeover_pct_threshold})', 'default':p2_acc_takeover_pct_threshold},
#             ]
#     }


# spoofing ruleset
# class SpoofingParams(Enum):
#     p1_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p1_retail_first_period').order_by('-created_at').first()
#     p2_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p2_retail_second_period').order_by('-created_at').first()
#     p3_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p3_retail_first_canceled_orders_threshold').order_by('-created_at').first()
#     p4_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p4_retail_second_canceled_orders_threshold').order_by('-created_at').first()
#     p5_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p5_retail_trade_threshold').order_by('-created_at').first()
#     p6_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p6_retail_opposite_order_threshold').order_by('-created_at').first()
#     p7_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p7_api_first_period').order_by('-created_at').first()
#     p8_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p8_api_second_period').order_by('-created_at').first()
#     p9_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p9_api_first_canceled_orders_threshold').order_by('-created_at').first()
#     p10_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p10_api_second_canceled_orders_threshold').order_by('-created_at').first()
#     p11_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p11_api_trade_threshold').order_by('-created_at').first()
#     p12_obj = ParamValues.objects.filter(param_master__param_key='spoofing', param_master__param_field='p12_api_opposite_order_threshold').order_by('-created_at').first()

#     if(((p1_obj is None)|(p2_obj is None)|(p3_obj is None)|(p4_obj is None)|(p5_obj is None)|(p6_obj is None)|(p7_obj is None)|(p8_obj is None)|(p9_obj is None)|(p10_obj is None)|(p11_obj is None)|(p12_obj is None))):
#         form_data={
#             'ruleset_name':'Spoofing monitoring',
#             'celery_name':'LENs_Spoofing_Monitoring_APAC',
#             'task_name':'libs.lens.output_tasks.lens_spoofing_apac.start',
#             'fields':[
#                 {'param_name':'p1', 'label':'(Retail) First repetitive cancel count period (p1):', 'type':'IntegerField', 'help_text':f'second(s) (default:{600})', 'default':600},
#                 {'param_name':'p2', 'label':'(Retail) Second repetitive cancel count period (p2):', 'type':'IntegerField', 'help_text':f'second(s) (default:{1800})', 'default':1800},
#                 {'param_name':'p3', 'label':'(Retail) First canceled orders threshold (p3):', 'type':'IntegerField', 'help_text':f'time(s) (default:{15})', 'default':15},
#                 {'param_name':'p4', 'label':'(Retail) Second canceled orders threshold (p4):', 'type':'IntegerField', 'help_text':f'time(s) (default:{8})', 'default':8},
#                 {'param_name':'p5', 'label':'(Retail) Trade frequency threshold (p5):', 'type':'IntegerField', 'help_text':f'time(s) (default:{2})', 'default':2},
#                 {'param_name':'p6', 'label':'(Retail) Oposite side orders threshold (p6):', 'type':'IntegerField', 'help_text':f'time(s) (default:{5})', 'default':5},
                
#                 {'param_name':'p7', 'label':'(API) First repetitive cancel count period (p7):', 'type':'IntegerField', 'help_text':f'second(s) (default:{600})', 'default':600},
#                 {'param_name':'p8', 'label':'(API) Second repetitive cancel count period (p8):', 'type':'IntegerField', 'help_text':f'second(s) (default:{1800})', 'default':1800},
#                 {'param_name':'p9', 'label':'(API) First canceled orders threshold (p9):', 'type':'IntegerField', 'help_text':f'time(s) (default:{200})', 'default':200},
#                 {'param_name':'p10', 'label':'(API) Second canceled orders threshold (p10):', 'type':'IntegerField', 'help_text':f'time(s) (default:{100})', 'default':100},
#                 {'param_name':'p11', 'label':'(API) Trade frequency threshold (p11):', 'type':'IntegerField', 'help_text':f'time(s) (default:{2})', 'default':2},
#                 {'param_name':'p12', 'label':'(API) Oposite side orders threshold (p12):', 'type':'IntegerField', 'help_text':f'time(s) (default:{5})', 'default':5},
#             ]
#         }
#     else:
#         # Retail trader
#         p1_retail_first_period = p1_obj.param_value
#         p2_retail_second_period = p2_obj.param_value
#         p3_retail_first_canceled_orders_threshold = p3_obj.param_value
#         p4_retail_second_canceled_orders_threshold = p4_obj.param_value
#         p5_retail_trade_threshold = p5_obj.param_value
#         p6_retail_opposite_order_threshold = p6_obj.param_value
#         # API trader
#         p7_api_first_period = p7_obj.param_value
#         p8_api_second_period = p8_obj.param_value
#         p9_api_first_canceled_orders_threshold = p9_obj.param_value
#         p10_api_second_canceled_orders_threshold = p10_obj.param_value
#         p11_api_trade_threshold = p11_obj.param_value
#         p12_api_opposite_order_threshold = p12_obj.param_value

#         tag = ','.join([p1_obj.params_tag,
#             p2_obj.params_tag,
#             p3_obj.params_tag,
#             p4_obj.params_tag,
#             p5_obj.params_tag,
#             p6_obj.params_tag,
#             p7_obj.params_tag,
#             p8_obj.params_tag,
#             p9_obj.params_tag,
#             p10_obj.params_tag,
#             p11_obj.params_tag,
#             p12_obj.params_tag
#             ])

#         form_data={
#             'ruleset_name':'Spoofing monitoring',
#             'celery_name':'LENs_Spoofing_Monitoring_APAC',
#             'task_name':'libs.lens.output_tasks.lens_spoofing_apac.start',
#             'fields':[
#                 {'param_name':'p1', 'label':'(Retail) First repetitive cancel count period (p1):', 'type':'IntegerField', 'help_text':f'second(s) (default:{p1_retail_first_period})', 'default':p1_retail_first_period},
#                 {'param_name':'p2', 'label':'(Retail) Second repetitive cancel count period (p2):', 'type':'IntegerField', 'help_text':f'second(s) (default:{p2_retail_second_period})', 'default':p2_retail_second_period},
#                 {'param_name':'p3', 'label':'(Retail) First canceled orders threshold (p3):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p3_retail_first_canceled_orders_threshold})', 'default':p3_retail_first_canceled_orders_threshold},
#                 {'param_name':'p4', 'label':'(Retail) Second canceled orders threshold (p4):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p4_retail_second_canceled_orders_threshold})', 'default':p4_retail_second_canceled_orders_threshold},
#                 {'param_name':'p5', 'label':'(Retail) Trade frequency threshold (p5):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p5_retail_trade_threshold})', 'default':p5_retail_trade_threshold},
#                 {'param_name':'p6', 'label':'(Retail) Oposite side orders threshold (p6):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p6_retail_opposite_order_threshold})', 'default':p6_retail_opposite_order_threshold},
                
#                 {'param_name':'p7', 'label':'(API) First repetitive cancel count period (p7):', 'type':'IntegerField', 'help_text':f'second(s) (default:{p7_api_first_period})', 'default':p7_api_first_period},
#                 {'param_name':'p8', 'label':'(API) Second repetitive cancel count period (p8):', 'type':'IntegerField', 'help_text':f'second(s) (default:{p8_api_second_period})', 'default':p8_api_second_period},
#                 {'param_name':'p9', 'label':'(API) First canceled orders threshold (p9):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p9_api_first_canceled_orders_threshold})', 'default':p9_api_first_canceled_orders_threshold},
#                 {'param_name':'p10', 'label':'(API) Second canceled orders threshold (p10):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p10_api_second_canceled_orders_threshold})', 'default':p10_api_second_canceled_orders_threshold},
#                 {'param_name':'p11', 'label':'(API) Trade frequency threshold (p11):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p11_api_trade_threshold})', 'default':p11_api_trade_threshold},
#                 {'param_name':'p12', 'label':'(API) Oposite side orders threshold (p12):', 'type':'IntegerField', 'help_text':f'time(s) (default:{p12_api_opposite_order_threshold})', 'default':p12_api_opposite_order_threshold},
#             ]
#         }

# Employee Account Ruleset
class EmployeeAccountParams(Enum):
    p1_obj = ParamValues.objects.filter(param_master__param_key='employee_account', param_master__param_field='p1_observation_period').order_by('-created_at').first()
    p2_obj = ParamValues.objects.filter(param_master__param_key='employee_account', param_master__param_field='p2_trade_threshold').order_by('-created_at').first()

    if((p1_obj is None)|(p2_obj is None)):
        form_data = {
            'ruleset_name':'Employee Account',
            'celery_name':'LENs_Employee_Account_APAC',
            'task_name':'libs.lens.output_tasks.lens_employee_account_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Observation period (p1):', 'type':'IntegerField', 'help_text':f'hour(s) (default:{24})', 'default':24},
                {'param_name':'p2', 'label':'Trade threshold (p2):', 'type':'DecimalField', 'help_text':f'{local_currency} (default:{50000})', 'default':50000},
            ]
        }

    else:
        p1_observation_period = p1_obj.param_value
        p2_trade_threshold = p2_obj.param_value
        tag = ','.join([p1_obj.params_tag, p2_obj.params_tag])
        form_data = {
            'ruleset_name':'Employee Account',
            'celery_name':'LENs_Employee_Account_APAC',
            'task_name':'libs.lens.output_tasks.lens_employee_account_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Observation period (p1):', 'type':'IntegerField', 'help_text':f'hour(s) (default:{p1_observation_period})', 'default':p1_observation_period},
                {'param_name':'p2', 'label':'Trade threshold (p2):', 'type':'DecimalField', 'help_text':f'{local_currency} (default:{p2_trade_threshold})', 'default':p2_trade_threshold},
            ]
        }

# Insider Trading Ruleset
class InsiderTradingParams(Enum):
    p1_obj = ParamValues.objects.filter(param_master__param_key='insider_trading', param_master__param_field='p1_suspended_period').order_by('-created_at').first()

    if(p1_obj is None):
        form_data = {
            'ruleset_name':'Insider Trading',
            'celery_name':'LENs_Insider_Trading_APAC',
            'task_name':'libs.lens.output_tasks.lens_insider_trading_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Suspended period (p1):', 'type':'IntegerField', 'help_text':f'hour(s) (default:{24})', 'default':24},
            ]
        }

    else:
        p1_suspended_period = p1_obj.param_value
        tag = p1_obj.params_tag
        form_data = {
            'ruleset_name':'Insider Trading',
            'celery_name':'LENs_Insider_Trading_APAC',
            'task_name':'libs.lens.output_tasks.lens_insider_trading_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Suspended period (p1):', 'type':'IntegerField', 'help_text':f'hour(s) (default:{p1_suspended_period})', 'default':p1_suspended_period},
            ]
        }
class MicroStructuringParams(Enum):
    p1_obj = ParamValues.objects.filter(param_master__param_key='microstructuring', param_master__param_field='p1_observation_period').order_by('-created_at').first()
    p2_obj = ParamValues.objects.filter(param_master__param_key='microstructuring', param_master__param_field='p2_accumulate_dw').order_by('-created_at').first()
    p3_obj = ParamValues.objects.filter(param_master__param_key='microstructuring', param_master__param_field='p3_counts_dw').order_by('-created_at').first()

    if((p1_obj is None) | (p2_obj is None) | (p3_obj is None)):
        form_data = {
            'ruleset_name':'Microstructuring',
            'celery_name':'LENs_Micro_Structuring_APAC',
            'task_name':'libs.lens.output_tasks.lens_micro_structuring_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Observation Period (p1):', 'type':'IntegerField', 'help_text':f'day(s) (default:{30})', 'default':30},
                {'param_name':'p2', 'label':'Accumulate Deposit/Withdraw (p2):', 'type':'DecimalField', 'help_text':f'IDR (default: IDR 1,100,000,000)', 'default':1100000000},
                {'param_name':'p3', 'label':'Count Deposit/Withdraw (p3):', 'type':'IntegerField', 'help_text':f'Minimum D/W to be detected', 'default':25},
            ]
        }

    else:
        p1_observation_period = p1_obj.param_value
        p2_accumulate_dw = p2_obj.param_value
        p3_counts_dw = p3_obj.param_value
        tag = ','.join([p1_obj.params_tag, p2_obj.params_tag, p3_obj.params_tag])
        
        form_data = {
            'ruleset_name':'Microstructuring',
            'celery_name':'LENs_Micro_Structuring_APAC',
            'task_name':'libs.lens.output_tasks.lens_micro_structuring_apac.start',
            'fields':[
                {'param_name':'p1', 'label':'Observation Period (p1):', 'type':'IntegerField', 'help_text':f'day(s) (default:{p1_observation_period})', 'default':p1_observation_period},
                {'param_name':'p2', 'label':'Accumulate Deposit/Withdraw (p2):', 'type':'DecimalField', 'help_text':f'IDR (default: IDR {p2_accumulate_dw})', 'default':p2_accumulate_dw},
                {'param_name':'p3', 'label':'Count Deposit/Withdraw (p3):', 'type':'IntegerField', 'help_text':f'Minimum D/W to be detected', 'default':p3_counts_dw},
            ]
        }

class SmurfingParams(Enum):
    p1_obj = ParamValues.objects.filter(param_master__param_key='smurfing', param_master__param_field='p1_observation_period').order_by('-created_at').first()
    p2_obj = ParamValues.objects.filter(param_master__param_key='smurfing', param_master__param_field='p2_salary_multiplication_threshold').order_by('-created_at').first()

    if((p1_obj is None) | (p2_obj is None)):
        form_data = {
            'ruleset_name':'Smurfing',
            'celery_name':'LENs_Smurfing_ID',
            'task_name':'reporter.tasks.ruleset.lens_smurfing_id.start',
            'fields':[
                {'param_name':'p1', 'label':'Observation period (p1):', 'type':'IntegerField', 'help_text':f'day(s) (default:{30})', 'default':30},
                {'param_name':'p2', 'label':'Salary multiplication threshold (p2):', 'type':'IntegerField', 'help_text':f'Minimum amount of {3} times of monthly salary to be detected', 'default':3},
            ]
        }

    else:
        p1_observation_period = p1_obj.param_value
        p2_salary_multiplication_threshold = p2_obj.param_value
        tag = ','.join([p1_obj.params_tag, p2_obj.params_tag])
        
        form_data = {
            'ruleset_name':'Smurfing',
            'celery_name':'LENs_Smurfing_ID',
            'task_name':'reporter.tasks.ruleset.lens_smurfing_id.start',
            'fields':[
                {'param_name':'p1', 'label':'Observation period (p1):', 'type':'IntegerField', 'help_text':f'day(s) (default:{p1_observation_period})', 'default':p1_observation_period},
                {'param_name':'p2', 'label':'Salary multiplication threshold (p2):', 'type':'IntegerField', 'help_text':f'Minimum amount of {p2_salary_multiplication_threshold} times of monthly salary to be detected', 'default':p2_salary_multiplication_threshold},
            ]
        }

class ExcludeList(Enum):
    excluded_customer_list = []
