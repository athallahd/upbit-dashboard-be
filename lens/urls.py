import django_saml2_auth.views
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

from lens.admin import permission, task
from lens.views import HomePageView
from lens_csv.admin import csv_task
from lens_data.admin import data
from lens_monitoring.admin import monitoring
from masterdata.admin import sec
from snapshot.admin import snapshot
from trigger.admin import trigger

admin.site.site_header = 'LENs ID'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('', include('lens_data.urls')),
    path('', include('snapshot.urls')),
    path('', include('masterdata.urls')),
    path('api/', include('lens_monitoring.urls')),
    path('admin/', admin.site.urls),
    path('saml2_auth/', include('django_saml2_auth.urls')),
    path('accounts/login/', django_saml2_auth.views.signin),
    path('admin/login/', django_saml2_auth.views.signin),
]
