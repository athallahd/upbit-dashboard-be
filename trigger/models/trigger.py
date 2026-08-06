from django.db import models
from lens.celeryconfig import beat_schedule


# Create your models here.
class TaskTrigger(models.Model):
    task_name = models.CharField(max_length=255, choices=tuple((value['task'], key) for key, value in beat_schedule.items()))
    target_date = models.DateField()
    is_trigger = models.BooleanField(default=False)
    comments = models.TextField(max_length=4000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'task_trigger'

class BacktestTrigger(models.Model):
    id = models.BigAutoField(primary_key=True)
    ruleset_name = models.CharField(max_length=100, choices=tuple((value['task'], key) for key, value in beat_schedule.items() if key.startswith('LENs'))) ## All daily tasks that name start with LENs
    start_date = models.DateField(blank=True)
    end_date = models.DateField(blank=True)
    is_trigger = models.BooleanField(default=False)
    parameters = models.TextField(blank=True)
    tag = models.CharField(max_length=100)
    event_log = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'backtest_trigger'


class TaskTrigger2(models.Model):
    task_name = models.CharField(max_length=255, choices=tuple((value['task'], key) for key, value in beat_schedule.items()))
    start_date = models.DateField()
    end_date = models.DateField()
    param = models.CharField(max_length=100, blank=True)
    is_trigger = models.BooleanField(default=False)
    progress_flag = models.BooleanField(default=False)
    comments = models.TextField(max_length=4000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'task_trigger2'
        