from django.db import models


class InputCsvTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    file_name = models.CharField(max_length=255)
    target_date = models.DateField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'input_csv_task'


class OutputCsvTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    file_name = models.CharField(max_length=255)
    target_date = models.DateField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'output_csv_task'