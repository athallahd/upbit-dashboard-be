from enum import Enum

from django.conf import settings

from masterdata.models.sec import ParamValues


local_currency = settings.CURRENCY_CODE


class LazyRulesetParams:
    """Static ruleset metadata with database-backed values resolved on demand."""

    ruleset_name = ''
    celery_name = ''
    task_name = ''
    param_key = ''
    field_definitions = ()

    @classmethod
    def get_form_data(cls):
        param_fields = [field['param_field'] for field in cls.field_definitions]
        latest_values = {}
        queryset = (
            ParamValues.objects.select_related('param_master')
            .filter(
                param_master__param_key=cls.param_key,
                param_master__param_field__in=param_fields,
            )
            .order_by('param_master__param_field', '-created_at')
        )
        for value in queryset:
            latest_values.setdefault(value.param_master.param_field, value)

        fields = []
        for definition in cls.field_definitions:
            stored_value = latest_values.get(definition['param_field'])
            value = stored_value.param_value if stored_value else definition['default']
            fields.append(
                {
                    'param_name': definition['param_name'],
                    'label': definition['label'],
                    'type': definition['type'],
                    'help_text': definition['help_text'].format(
                        value=value,
                        currency=local_currency,
                    ),
                    'default': value,
                }
            )

        return {
            'ruleset_name': cls.ruleset_name,
            'celery_name': cls.celery_name,
            'task_name': cls.task_name,
            'fields': fields,
        }


class WashTradeParams(LazyRulesetParams):
    ruleset_name = 'Wash trade monitoring'
    celery_name = 'LENs_Wash_Trade_APAC'
    task_name = 'libs.lens.output_tasks.lens_wash_trade_apac.start'
    param_key = 'wash_trade'
    field_definitions = (
        {'param_field': 'p1_lv1_ratio', 'param_name': 'p1', 'label': 'Trade frequency threshold lv1 (p1):', 'type': 'IntegerField', 'help_text': 'time(s) (default:{value})', 'default': 6},
        {'param_field': 'p2_lv2_ratio', 'param_name': 'p2', 'label': 'Trade frequency threshold lv2 (p2):', 'type': 'IntegerField', 'help_text': 'time(s) (default:{value})', 'default': 8},
        {'param_field': 'p3_lv3_ratio', 'param_name': 'p3', 'label': 'Trade frequency threshold lv3 (p3):', 'type': 'IntegerField', 'help_text': 'time(s) (default:{value})', 'default': 10},
        {'param_field': 'p4_simul_entry', 'param_name': 'p4', 'label': 'Simultaneous order window (p4):', 'type': 'IntegerField', 'help_text': 'minute(s) (default:{value})', 'default': 5},
        {'param_field': 'p5_trade_vol', 'param_name': 'p5', 'label': 'Volume threshold (p5):', 'type': 'DecimalField', 'help_text': 'Volume threshold (p5): (default:{value}{currency})', 'default': 50000},
    )


class FATFParams(LazyRulesetParams):
    ruleset_name = 'FATF monitoring'
    celery_name = 'LENs_FATF_Monitoring_APAC'
    task_name = 'libs.lens.output_tasks.lens_fatf_monitoring_apac.start'
    param_key = 'fatf'
    field_definitions = (
        {'param_field': 'p1_fatf_countries_list', 'param_name': 'p1', 'label': 'Countries code:', 'type': 'CharField', 'help_text': 'Input format must be country code seperated by | eg. KP|IR|MM, You can find country code here : https://www.iban.com/country-codes', 'default': 'KP|IR|MM|BG|BF|CD|HR|HT|JM|KE|ML|PH|SN|ZA|SS|SY|TR|VN|YE|AF|DZ|AW|BD|BJ|BI|CM|TD|CN|CU|DJ|EG|ER|ET|GH|GY|HN|IQ|CI|XK|MA|MZ|NA|NP|NG|PK|QA|CG|RW|RS|KR|LK|TJ|TZ|TG|TT|TN|TM|UG|US|UZ|VE'},
    )


class EmployeeAccountParams(LazyRulesetParams):
    ruleset_name = 'Employee Account'
    celery_name = 'LENs_Employee_Account_APAC'
    task_name = 'libs.lens.output_tasks.lens_employee_account_apac.start'
    param_key = 'employee_account'
    field_definitions = (
        {'param_field': 'p1_observation_period', 'param_name': 'p1', 'label': 'Observation period (p1):', 'type': 'IntegerField', 'help_text': 'hour(s) (default:{value})', 'default': 24},
        {'param_field': 'p2_trade_threshold', 'param_name': 'p2', 'label': 'Trade threshold (p2):', 'type': 'DecimalField', 'help_text': '{currency} (default:{value})', 'default': 50000},
    )


class InsiderTradingParams(LazyRulesetParams):
    ruleset_name = 'Insider Trading'
    celery_name = 'LENs_Insider_Trading_APAC'
    task_name = 'libs.lens.output_tasks.lens_insider_trading_apac.start'
    param_key = 'insider_trading'
    field_definitions = (
        {'param_field': 'p1_suspended_period', 'param_name': 'p1', 'label': 'Suspended period (p1):', 'type': 'IntegerField', 'help_text': 'hour(s) (default:{value})', 'default': 24},
    )


class MicroStructuringParams(LazyRulesetParams):
    ruleset_name = 'Microstructuring'
    celery_name = 'LENs_Micro_Structuring_APAC'
    task_name = 'libs.lens.output_tasks.lens_micro_structuring_apac.start'
    param_key = 'microstructuring'
    field_definitions = (
        {'param_field': 'p1_observation_period', 'param_name': 'p1', 'label': 'Observation Period (p1):', 'type': 'IntegerField', 'help_text': 'day(s) (default:{value})', 'default': 30},
        {'param_field': 'p2_accumulate_dw', 'param_name': 'p2', 'label': 'Accumulate Deposit/Withdraw (p2):', 'type': 'DecimalField', 'help_text': 'IDR (default: IDR {value})', 'default': 1100000000},
        {'param_field': 'p3_counts_dw', 'param_name': 'p3', 'label': 'Count Deposit/Withdraw (p3):', 'type': 'IntegerField', 'help_text': 'Minimum D/W to be detected', 'default': 25},
    )


class SmurfingParams(LazyRulesetParams):
    ruleset_name = 'Smurfing'
    celery_name = 'LENs_Smurfing_ID'
    task_name = 'reporter.tasks.ruleset.lens_smurfing_id.start'
    param_key = 'smurfing'
    field_definitions = (
        {'param_field': 'p1_observation_period', 'param_name': 'p1', 'label': 'Observation period (p1):', 'type': 'IntegerField', 'help_text': 'day(s) (default:{value})', 'default': 30},
        {'param_field': 'p2_salary_multiplication_threshold', 'param_name': 'p2', 'label': 'Salary multiplication threshold (p2):', 'type': 'IntegerField', 'help_text': 'Minimum amount of {value} times of monthly salary to be detected', 'default': 3},
    )


class ExcludeList(Enum):
    excluded_customer_list = []
