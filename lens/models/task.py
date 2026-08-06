from django.db import models
from lens.models.base_timestamped import TimeStampedModel


class Task(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    file_name = models.CharField(max_length=255)
    upload_tried_at = models.DateTimeField()
    uploaded_at = models.DateTimeField()
    target_date = models.DateField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'task'


class ReportStatus(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    license_number = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    target_date = models.DateField()
    status = models.CharField(max_length=100) # Status on SEC website

    class Meta:
        managed = False
        db_table = 'report_status'
