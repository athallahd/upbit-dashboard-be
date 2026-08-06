import datetime
import os

from django.conf import settings
from django.contrib import admin
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import re_path, reverse
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin

from lens.models.task import Task
from lens.settings.defaults import TASKS_LIST

@admin.register(Task)
class TaskAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    def get_urls(self):
        urls = super(TaskAdmin, self).get_urls()
        urls += [
            re_path(r'^download/(?P<pk>\d+)$', self.download,
                name='reporter_task_download'),
        ]
        return urls


    def download_link(self, obj):
        return format_html(
            '<a href="{}">Download</a>',
            reverse('admin:reporter_task_download', args=[obj.pk])
        )

    list_per_page = 30
    list_display = [
        'id',
        'name',
        'state',
        'file_name',
        'target_date',
        'created_at_jkt',
        'updated_at_jkt',
        'download_link',
    ]
    fields = [
        'id',
        'name',
        'state',
        'file_name',
        'target_date',
        'created_at_jkt',
        'updated_at_jkt',
        'download_link',
    ]
    readonly_fields = [
        'id',
        'name',
        'state',
        'target_date',
        'created_at_jkt',
        'updated_at_jkt',
        'download_link',
    ]
    list_filter = [
        'name'
    ]
    search_fields = [
        'name', 
        'file_name'
    ]


    def created_at_jkt(self, obj):
        return obj.created_at + datetime.timedelta(hours=settings.LOCAL_TIME_DELTA)
    created_at_jkt.short_description = 'Created at (JKT)'


    def updated_at_jkt(self, obj):
        return obj.updated_at + datetime.timedelta(hours=settings.LOCAL_TIME_DELTA)
    updated_at_jkt.short_description = 'Updated at (JKT)'


    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False


    def get_queryset(self, request):
        qs = super(TaskAdmin, self).get_queryset(request).using('reporter')

        user_groups = request.user.groups.all()
        group_names = [group.name.lower() for group in user_groups]
        task_pool = []

        for group, tasks in TASKS_LIST.items():
            if group in group_names:
                task_pool.extend(tasks)

        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(name__in=task_pool)
        
        # If the user does not belong to any group with specific tasks, return empty set
        return Task.objects.none()


    def download(self, request: HttpRequest, pk: int):
        if request.user.is_authenticated:
            query = Task.objects.using('reporter').filter(id=pk).first()
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
