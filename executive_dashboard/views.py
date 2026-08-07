from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DashboardDailySerializer
from .services import DashboardDataNotReady, get_daily_dashboard


class DashboardDailyView(APIView):
    """Return the cached Executive Dashboard summary for Jakarta T-1."""

    def get(self, request) -> Response:
        try:
            snapshot = get_daily_dashboard()
        except DashboardDataNotReady as exc:
            target_date = exc.args[0]
            raise NotFound(
                f"Dashboard data for {target_date.isoformat()} is not available. "
                "Run `python manage.py refresh_dashboard` first."
            ) from exc

        return Response(DashboardDailySerializer(snapshot).data)
