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
        Make sure the auth app only appears in the 'auth'
        database.
        """
        return False
