from django.contrib import admin
from masterdata.models.sec import AssetMaster

@admin.register(AssetMaster)
class AssetMasterAdmin(admin.ModelAdmin):
    list_display = (        
        'sec_asset_id',
        'sec_asset_short_name',
        'currency_ticker',
    ) 
    list_display_links = ('sec_asset_id',)
    search_fields = [
        'sec_asset_id',
        'sec_asset_short_name',
        'currency_ticker',
    ]
    