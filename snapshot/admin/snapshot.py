import csv
import os
from datetime import timedelta

from django.conf import settings
from django.urls import re_path
from django.contrib import admin
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.shortcuts import HttpResponseRedirect
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilter
from djangoql.admin import DjangoQLSearchMixin

from snapshot.models.snapshot import (AccountVersionSnapshot, AssetSnapshot, DukcapilCheckLog, NIDCheckLog, AccountSnapshotLp)


class NoCountPaginator(Paginator):
    """
    Paginator that does not count the rows in the table.
    """
    @cached_property
    def count(self):
        return 9999999999
    

class LimitCountPaginator(Paginator):
    LIMIT = 2000000

    @cached_property
    def count(self):
        """
        Returns the total number of objects, across all pages.
        """
        try:
            limit = self.LIMIT
            total = self.object_list.order_by()[:limit].count()
            # ^-- User order_by() to remove any ordering and
            # count objects as quickly as possible. (Shouldn't
            # SQL optimize the query regardless of ordering?)
            return total if total < limit else IntPlus(total)
        except (AttributeError, TypeError):
            # AttributeError if object_list has no count() method.
            # TypeError if object_list.count() requires arguments
            # (i.e. is of type list).
            return len(self.object_list)


class IntPlus(int):
    def __str__(self):
        return '{}+'.format(int.__str__(self))


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


@admin.register(NIDCheckLog)
class NIDCheckLogAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(NIDCheckLogAdmin, self).get_urls()
        urls += [
            re_path(r'^download/(?P<pk>\d+)$', self.download,
                name='nid_check_task_download'),
        ]
        return urls


    def download_link(self, obj):
        return format_html(
            '<a href="{}">Download</a>',
            reverse('admin:nid_check_task_download', args=[obj.pk])
        )
    
    list_display = (   
        'id',     
        'created_at',
        'status',
        'download_link',
    )
    readonly_fields = ('status',)


    def download(self, request: HttpRequest, pk: int):
        query = NIDCheckLog.objects.using('reporter').filter(id=pk).first()
        filename = query.input_file.name
        file_path = os.path.join(settings.MEDIA_ROOT, '{}_result.csv'.format(filename[:-4] if filename and len(filename) >= 4 else "" if filename else None))
        file_path = os.path.join(os.path.abspath(os.path.dirname(__name__)), file_path)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/force-download")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        else:
            raise Http404


@admin.register(DukcapilCheckLog)
class DuckapilCheckLogAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(DuckapilCheckLogAdmin, self).get_urls()
        urls += [
            re_path(r'^download/(?P<pk>\d+)$', self.download,
                name='dukcapil_check_task_download'),
        ]
        return urls


    def download_link(self, obj):
        return format_html(
            '<a href="{}">Download</a>',
            reverse('admin:dukcapil_check_task_download', args=[obj.pk])
        )
    

    list_display = ( 
        'id',       
        'created_at_jkt',
        'status',
        'download_link',
        'created_by',
    )
    exclude=(
        'created_by',
    )
    readonly_fields = ('status',)

    def created_at_jkt(self, obj):
        return obj.created_at + timedelta(hours=settings.LOCAL_TIME_DELTA)
    created_at_jkt.short_description = 'Created At (JKT)'
    

    def response_add(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.created_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:snapshot_dukcapilchecklog_changelist'))


    def download(self, request: HttpRequest, pk: int):
        query = DukcapilCheckLog.objects.using('reporter').filter(id=pk).first()
        filename = query.input_file.name
        file_path = os.path.join(settings.MEDIA_ROOT, '{}_result.csv'.format(filename[:-4]))
        file_path = os.path.join(os.path.abspath(os.path.dirname(__name__)), file_path)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/force-download")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        else:
            raise Http404

@admin.register(AccountVersionSnapshot)
class AccountVersionSnapshotAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = [
        'id',
        'target_date',
        'member_id',
        'member_uuid',
        'currency',
        'amount',
        'value_btc_market',
        'value_fiat_market',
        'tag',
        'created_at_gmt',
    ]
    
    list_filter = (
        ('target_date', DateRangeFilter), 
        'currency',)
        
    search_fields = [
        'member_id',
    ]

    actions = ['export_as_csv']
    paginator = LimitCountPaginator
    show_full_result_count = False


    def created_at_gmt(self, obj):
        return obj.created_at + timedelta(hours=settings.LOCAL_TIME_DELTA)
    created_at_gmt.short_description = 'Created at (WIB)'


    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccountSnapshotLp)
class AccountSnapshotLpAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = [
        'member_id',
        'currency',
        'out',
        'balance',
        'locked',
        # 'default_withdraw_fund_source_id',
        # 'default_deposit_fund_source_id',
        'created_at',
        'updated_at',
        'passbook_id',
        'imported_at',
        'fiat_value',
    ]
    
    list_filter = (
        ('imported_at', DateRangeFilter), 
    )
        
    search_fields = [
        'member_id',
    ]

    actions = ['export_as_csv']
    paginator = LimitCountPaginator
    show_full_result_count = False


    def created_at_gmt(self, obj):
        return obj.created_at + timedelta(hours=settings.LOCAL_TIME_DELTA)
    created_at_gmt.short_description = 'Created at (WIB)'

    def updated_at_gmt(self, obj):
        return obj.updated_at + timedelta(hours=settings.LOCAL_TIME_DELTA)
    updated_at_gmt.short_description = 'Updated at (WIB)'

    def imported_at_gmt(self, obj):
        return obj.imported_at + timedelta(hours=settings.LOCAL_TIME_DELTA)
    imported_at_gmt.short_description = 'Imported at (WIB)'

    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(AssetSnapshot)
class AssetSnapshotAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    def get_urls(self):
        urls = super(AssetSnapshotAdmin, self).get_urls()
        urls += [
            re_path(r'^download/(?P<pk>\d+)$', self.download,
                name='asset_snapshot_download'),
        ]
        return urls

    def download_link(self, obj):
        return format_html(
            '<a href="{}">Download</a>',
            reverse('admin:asset_snapshot_download', args=[obj.pk])
        )

    list_per_page = 30
    list_display = [
        'id',
        'target_date',
        'file_name',
        'created_at_jkt',
        'download_link',
    ]
    fields = [
        'id',
        'target_date',
        'file_name',
        'created_at_jkt',
        'download_link',
    ]
    readonly_fields = [
        'id',
        'target_date',
        'file_name',
        'created_at_jkt',
        'download_link',
    ]
    list_filter = [
        ('target_date', DateRangeFilter), 
    ]
    search_fields = [
        'file_name'
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def created_at_jkt(self, obj):
        return obj.created_at + timedelta(hours=settings.LOCAL_TIME_DELTA)
    created_at_jkt.short_description = 'Created At (JKT)'
    
    def download(self, request: HttpRequest, pk: int):
        if request.user.is_authenticated:
            query = AssetSnapshot.objects.using('reporter').filter(id=pk).first()
            file_path = os.path.join(settings.MEDIA_ROOT, query.file_name + '.csv')
            file_path = os.path.join(os.path.abspath(os.path.dirname(__name__)), file_path)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/force-download")
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                    return response
            else:
                raise Http404
        else:
            raise Http404
