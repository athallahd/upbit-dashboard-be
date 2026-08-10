from django.conf import settings


class AuthRouter(object):
    """
    A router to control all database operations on models in the
    auth application.
    """

    model_list = [
        'assetmaster', 
        'tasktrigger',
        'tasktrigger2',
        'backtesttrigger',
        'accountversionsnapshot',
        'nidchecklog',
        'dukcapilchecklog',
        "userinfo",
        "dashboarddaily",
        "tradebase",
        "cfxassetmaster",
        "depositbase",
        "withdrawbase",
        "inputcsvtask",
        "outputcsvtask",
        "cmcdaily",
        "cmchourly",
        "usertransactioninfo",
        "usertransaction",
        "globaldailyratebtc",
        "localdailyrate",
        "cfxlog",
        "cfxsenttrades",
        "kkilog",
        "kkisenttransactions",
        "icclog",
        "iccsenttransactions",
        "ipaddresscache",
        "loginhistory",
        "parammaster",
        "paramvalues",
        "employeemaster",
        "lenswashtradeapac",
        "lensfatfmonitoringapac",
        "lensemployeeaccountapac",
        "lensinsidertradingapac",
        "investmenteventbase",
        "lensfiatfeevolume",
        "uptimesummary",
        "marketcategory",
    ]

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth models go to auth.
        """
        print("READ ",model._meta.app_label)
        if model._meta.model_name in self.model_list:
            return 'reporter'

        if model._meta.app_label in ['auth', 'contenttypes', 'admin', 'sessions']:
            print(True)
            return 'reporter'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth models go to auth.
        """
        print("WRITE ",model._meta.app_label)
        if model._meta.model_name in self.model_list:
            return 'reporter'
            
        if model._meta.app_label in ['auth', 'contenttypes', 'admin', 'sessions']:
            print(True)
            return 'reporter'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth app is involved.
        """
        print("REL ", obj1._meta.app_label, ' ', obj2._meta.app_label)
        if obj1._meta.app_label in ['auth', 'contenttypes', 'admin', 'sessions'] or \
                obj2._meta.app_label in ['auth', 'contenttypes', 'admin', 'sessions']:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        The reporting schema is provisioned from SQL and must not be managed by
        Django migrations.  Local API testing additionally needs Django's own
        authentication tables so an Okta subject can be allowlisted locally.
        """
        local_auth_apps = {'auth', 'contenttypes', 'sessions'}
        if (
            db == 'reporter'
            and app_label in local_auth_apps
            and settings.LOCAL_AUTH_SCHEMA_MANAGED
        ):
            return True

        return False
