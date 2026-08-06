from .forms import *
from .ruleset_params import *

from django.contrib import admin
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse
from django.forms.models import modelform_factory
from lens.celeryconfig import beat_schedule

ruleset_dict = dict((key, value['task']) for key, value in beat_schedule.items() if key.startswith('LENs'))
active_ruleset = [WashTradeParams, FATFParams, EmployeeAccountParams, InsiderTradingParams, MicroStructuringParams,SmurfingParams]


@admin.register(TaskTrigger)
class TaskTriggerAdmin(admin.ModelAdmin):
    list_display = (        
        'id',
        'task_name',
        'target_date',
        'is_trigger',
        'comments',
        'created_at',
    )

    exclude = (
        'created_at',
    )


    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(TaskTrigger2)
class TaskTrigger2Admin(admin.ModelAdmin):
    list_display = (        
        'id',
        'task_name',
        'start_date',
        'end_date',
        'param',
        'is_trigger',
        'progress_flag',
        'comments',
        'created_at',
    )

    exclude = (
        'created_at',
        # 'progress_flag',
    )


    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(BacktestTrigger)
class BacktestTriggerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ruleset_name',
        'start_date',
        'end_date',
        'is_trigger',
        'parameters',
        'tag',
        'event_log',
        'comments',
        'created_by',
        'created_at',
    )
    readonly_fields = [
    ]
    exclude = ( 
        'created_at',
    )
    def get_form(self, request, obj=None, **kwargs):
        if(obj):
            selected_ruleset_name=obj.ruleset_name
            for active in active_ruleset:
                if(active.form_data.value['task_name']==selected_ruleset_name):
                    form_class=create_dynamic_form(active.form_data.value, obj.parameters)
                    return modelform_factory(BacktestTrigger, form=form_class)
                else:
                    form_class=BacktestBlankForm
        else:
            form_class=BacktestBlankForm
        return modelform_factory(BacktestTrigger, form=form_class,)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
            context.update({
                'show_save': True,
                'show_save_and_continue': False,
                'show_save_and_add_another': False,
                'show_delete': True
            })
            return super().render_change_form(request, context, add, change, form_url, obj)

    def response_add(self, request, obj, post_url_continue=None):
        current_user = request.user
        if current_user.is_authenticated:
            add_obj = obj
            add_obj.created_by = current_user.username
            add_obj.save()
        return HttpResponseRedirect(reverse('admin:trigger_backtesttrigger_change', args=(obj.pk,)))
    
    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True
    