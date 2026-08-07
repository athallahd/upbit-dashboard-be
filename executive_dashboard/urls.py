from django.urls import path

from .views import DashboardDailyView


urlpatterns = [
    path("dashboard/daily/", DashboardDailyView.as_view(), name="dashboard-daily"),
    path(
        "dashboard/daily",
        DashboardDailyView.as_view(),
        name="dashboard-daily-no-slash",
    ),
]
