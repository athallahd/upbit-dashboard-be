import csv

from django import forms
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse

from masterdata.models.sec import (AssetMaster, ICEXAssetMaster,
                                   DashboardAlertMaster,
                                   DashboardRulesetMaster, EmployeeMaster, ICEXAssetMaster,
                                   LpMaster, ParamMaster, ParamValues, MarketCategory, TaggableMaster,
                                   UbidTestAccount)
from masterdata.registry import RULESET_CHOICES


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"

@admin.register(AssetMaster)
class AssetMasterAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (        
        'sec_asset_id',
        'sec_asset_short_name',
        'currency_ticker',
        'asset_name',
        'flag1',
        'comments',
        'listing_date',
        'listing_time',
        'created_at',
        'updated_at',
    ) 
    list_display_links = ('sec_asset_id',)
    search_fields = [
        'sec_asset_id',
        'sec_asset_short_name',
        'currency_ticker',
    ]
    save_as = True
    actions = ['export_as_csv']

@admin.register(ICEXAssetMaster)
class ICEXAssetMasterAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (        
        'asset_id',
        'asset_code',
        'asset_name',
        'is_whitelisted',
        'created_at',
        'updated_at'
    ) 
    list_display_links = ('asset_id',)
    search_fields = [
        'asset_id',
        'asset_code',
        'asset_name',
    ]
    save_as = True
    actions = ['export_as_csv']


@admin.register(ParamMaster)
class ParamMasterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'param_key',
        'param_field',
        'created_at',
        'updated_at',
    )
    search_fields = [
        'param_key',
        'param_field',
    ]

@admin.register(ParamValues)
class ParamValuesAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'param_master',
        'param_value',
        'created_by',
        'params_tag',
        'created_at',
        'updated_at',
    )
    search_fields = [
        'param_master',
    ]
    exclude=(
        'created_by',
    )

    def response_add(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.created_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:masterdata_paramvalues_changelist'))
    
@admin.register(EmployeeMaster)
class EmployeeMasterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'member_uuid',
        'employee_name',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'member_uuid',
        'employee_name',
    ]

    exclude=(
        'created_by',
    )

@admin.register(LpMaster)
class LpMasterAdmin(admin.ModelAdmin):
    list_display = (        
        'member_id',
        'company_name',
        'is_default',
        'providing_pairs',
        'created_at',
        'updated_at',
    ) 
    list_display_links = ('member_id',)
    search_fields = [
        'member_id',
        'company_name',
    ]


@admin.register(DashboardAlertMaster)
class DashboardAlertMasterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'alert_name',
        'alert_for',
        'alert_key',
        'alert_type',
        'alert_condition',
        'alert_threshold',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
    )
    search_fields = [
        'alert_name',
        'alert_for',
    ]
    exclude=(
        'created_by',
        'updated_by',
    )

    def response_add(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.created_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:masterdata_dashboardalertmaster_changelist'))

    def response_change(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.updated_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:masterdata_dashboardalertmaster_changelist'))


class DashboardRulesetMasterForm(forms.ModelForm):
    ruleset_name = forms.ChoiceField(choices=RULESET_CHOICES)

    class Meta:
        model = DashboardRulesetMaster
        fields = '__all__'


@admin.register(DashboardRulesetMaster)
class DashboardRulesetMasterAdmin(admin.ModelAdmin):

    form = DashboardRulesetMasterForm
    list_display = (
        'id',
        'ruleset_name',
        'display_name',
        'is_active',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
    )
    search_fields = [
        'ruleset_name',
    ]
    exclude = (
        'created_by',
        'updated_by',
    )

    def response_add(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.created_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:masterdata_dashboardrulesetmaster_changelist'))

    def response_change(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.updated_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:masterdata_dashboardrulesetmaster_changelist'))



@admin.register(MarketCategory)
class MarketCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'market',
        'category',
        'created_at',
        'updated_at',
        'updated_by',
    )
    search_fields = [
        'market',
        'category',
    ]

    # def market(self, obj):
    #     return obj.enum.name

    def response_add(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.updated_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:masterdata_marketcategory_changelist'))
    
@admin.register(UbidTestAccount)
class UbidTestAccountAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'member_uuid',
        'note',
        'created_by',
        'created_at',
        'updated_at'
    )

    search_fields = [
        'member_uuid',
        'note'
    ]

    exclude=(
        'created_by',
    )

    def response_add(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.created_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:masterdata_ubidtestaccount_changelist'))
    
@admin.register(TaggableMaster)
class TaggableMasterAdmin(admin.ModelAdmin):
    list_display = (
        'member_id',
        'member_uuid',
        'email',
        'type',
        'nationality'
    )

    search_fields = [
        'member_uuid',
        'email'
    ]

    def response_add(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:masterdata_taggablemaster_changelist'))