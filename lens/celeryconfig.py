
# UTC Based Schedule
# DB Clone system run at 11:20 UTC
beat_schedule = {
    'Daily_Tradebook': {
        'task': 'reporter.tasks.daily_tradebook.start',
    },
    'Daily_Crypto': {
        'task': 'reporter.tasks.daily_crypto.start',
    },
    'Monthly_Tax_Report': {
        'task': 'reporter.tasks.monthly_tax_report.start',
    },
    'Quarterly_User_Report': {
        'task': 'reporter.tasks.quarterly_user_report.start',
    },
    'Monthly_Deposits_Report': {
        'task': 'reporter.tasks.monthly_deposits_report.start',
    },
    'File_Checker': {
        'task': 'reporter.tasks.file_checker_v2.process',
    },
    'NID_Check': {
        'task': 'reporter.tasks.nid_check_v3.start',
    },
    'Daily_Crypto_BTC_Rates' : {
        'task' : 'libs.lens.input_tasks.daily_btc_rates.start',
    },
    'Daily_Local_Currency_Rates' : {
        'task' : 'libs.lens.input_tasks.daily_local_currency_rates.start',
    },
    'Account_Version_Snapshot': {
        'task': 'reporter.tasks.account_version_snapshot_v4.start',
    },
    'Daily_UserBalance': {
        'task': 'reporter.tasks.daily_userbalance.start',
    },
    'Dukcapil_Check': {
        'task': 'reporter.tasks.dukcapil_check.start',
    },
    'Daily_Lens_Base_TradeData': {
        'task': 'libs.lens.input_tasks.base_order_n_trade.start',
    },
    'Daily_Lens_Base_OrderData': {
        'task': 'libs.lens.input_tasks.base_order_n_trade.start',
    },
    'Base_Deposit_N_Withdraw': {
        'task': 'libs.lens.input_tasks.base_deposit_n_withdraw.start',
    },
    'Base_User_Info': {
        'task': 'libs.lens.input_tasks.user_info.start',
    },
    'Fetch_Country_IP': {
        'task': 'libs.lens.input_tasks.fetch_ip_country.start',
    },
    'Daily_IP_Input': {
        'task': 'libs.lens.output_tasks.user_actiontype_report.start',
    },
    'Monthly_DepositWithdraw_User10B': {
        'task': 'reporter.tasks.monthly_depositwithdraw_user10B.start',
    },
    'Monthly_LPUser': {
        'task': 'reporter.tasks.monthly_LPUser_report.start',
    },
    'Monthly_DigitalAsset_Balance': {
        'task': 'reporter.tasks.monthly_digitalAsset_balance.start',
    },
    'Backtest_Trigger': {
        'task': 'reporter.tasks.backtest_ruleset_trigger.start',
    },
    'LENs_FATF_Monitoring_APAC': {
        'task': 'libs.lens.output_tasks.lens_fatf_monitoring_apac.start',
    },
    'LENs_Wash_Trade_APAC': {
        'task': 'libs.lens.output_tasks.lens_wash_trade_apac.start',
    },
    'LENs_Employee_Account_APAC': {
        'task': 'libs.lens.output_tasks.lens_employee_account_apac.start',
    },
    'LENs_Insider_Trading_APAC':{
        'task': 'libs.lens.output_tasks.lens_insider_trading_apac.start',
    },
    'Daily_Lens_InvestmentEvent_BaseData': {
        'task': 'libs.lens.input_tasks.base_investment_event.start',
    },
    'Task_Trigger': {
        'task': 'reporter.tasks.trigger_task.start',
    },
    'Task_Trigger2': {
        'task': 'reporter.tasks.trigger_task2.start',
    },
    'Update_Asset_Master': {
        'task': 'libs.lens.input_tasks.update_asset_master.start',
    },
    'Monthly_Transaction_Detail': {
        'task': 'reporter.tasks.monthly_transaction_detail.start',
    },
    'Daily_Report_OJK': {
        'task': 'reporter.tasks.daily_report_ojk.start',
    },
    'Monthly_Report_OJK': {
        'task': 'reporter.tasks.monthly_report_ojk.start',
    },
    'Monthly_Tax_Detail_Report': {
        'task': 'reporter.tasks.monthly_tax_detail_report.start',
    },
    'Monthly_500_Top_Trader': {
        'task': 'reporter.tasks.monthly_500_top_trader.start',
    },
    'Daily_CFX_Asset_Update': {
        'task': 'reporter.tasks.daily_cfx_asset_update.start',
    },
    'Monthly_Asset_Movement': {
        'task': 'reporter.tasks.monthly_asset_movement.start',
    },
    'Monthly_RS_Settlement': {
        'task': 'reporter.tasks.monthly_rs_settlement.start',
    },
    'Monthly_Withdrawal_fee': {
        'task': 'reporter.tasks.monthly_withdrawal_fee.start',
    },
    'Realtime_Account_Snapshot_Lp': {
        'task': 'libs.lens.input_tasks.account_snapshot_lp.start',
    },
    'LENs_Order_Count_Summary': {
        'task': 'libs.lens.output_tasks.lens_order_count_summary.start',
    },
    'Daily_Lens_Trading_Volume': {
        'task': 'libs.lens.output_tasks.lens_trading_volume.start',
    },
    'LENs_Micro_Structuring_APAC': {
        'task': 'libs.lens.output_tasks.lens_micro_structuring_apac.start',
    },
    'LENs_Smurfing_ID': {
        'task': 'reporter.tasks.ruleset.lens_smurfing_id.start',
    },
    'Daily_Lens_FiatFee_Volume': {
        'task': 'libs.lens.output_tasks.lens_fiat_fee_volume.start',
    },
    'Monthly_Detail_Trader': {
        'task': 'reporter.tasks.monthly_detail_trader.start',
    },
    'Daily_Reconciliation': {
        'task': 'lens_data.daily_reconciliation.daily_reconciliation.start',
    },
    'Monthly_Detail_Trader_Pair': {
        'task': 'reporter.tasks.monthly_detail_trader_pair.start',
    }
}
