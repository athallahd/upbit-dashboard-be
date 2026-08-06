import os

from django.conf import settings
from django.urls import re_path
from django.contrib import admin
from django.http import HttpRequest, HttpResponse, Http404
from django.urls import reverse
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin

from lens_csv.models.csv_task import InputCsvTask, OutputCsvTask


@admin.register(InputCsvTask)
class InputCsvTaskAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    def get_urls(self):
        urls = super(InputCsvTaskAdmin, self).get_urls()
        urls += [
            re_path(r'^download/(?P<pk>\d+)$', self.download,
                name='input_csv_task_download'),
        ]
        return urls

    def download_link(self, obj):
        return format_html(
            '<a href="{}">Download</a>',
            reverse('admin:input_csv_task_download', args=[obj.pk])
        )

    list_per_page = 30
    list_display = [
        'id',
        'name',
        'state',
        'file_name',
        'target_date',
        'created_at',
        'updated_at',
        'download_link',
    ]
    fields = [
        'id',
        'name',
        'state',
        'file_name',
        'target_date',
        'created_at',
        'updated_at',
        'download_link',
    ]
    readonly_fields = [
        'id',
        'name',
        'state',
        'target_date',
        'created_at',
        'updated_at',
        'download_link',
    ]
    list_filter = [
        'name'
    ]
    search_fields = [
        'name', 
        'file_name'
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def download(self, request: HttpRequest, pk: int):
        if request.user.is_authenticated:
            query = InputCsvTask.objects.using('reporter').filter(id=pk).first()
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


@admin.register(OutputCsvTask)
class OutputCsvTaskAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    def get_urls(self):
        urls = super(OutputCsvTaskAdmin, self).get_urls()
        urls += [
            re_path(r'^download/(?P<pk>\d+)$', self.download,
                name='output_csv_task_download'),
        ]
        return urls

    def download_link(self, obj):
        return format_html(
            '<a href="{}">Download</a>',
            reverse('admin:output_csv_task_download', args=[obj.pk])
        )

    list_per_page = 30
    list_display = [
        'id',
        'name',
        'state',
        'file_name',
        'target_date',
        'created_at',
        'updated_at',
        'download_link',
    ]
    fields = [
        'id',
        'name',
        'state',
        'file_name',
        'target_date',
        'created_at',
        'updated_at',
        'download_link',
    ]
    readonly_fields = [
        'id',
        'name',
        'state',
        'target_date',
        'created_at',
        'updated_at',
        'download_link',
    ]
    list_filter = [
        'name'
    ]
    search_fields = [
        'name', 
        'file_name'
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def download(self, request: HttpRequest, pk: int):
        if request.user.is_authenticated:
            query = OutputCsvTask.objects.using('reporter').filter(id=pk).first()
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
