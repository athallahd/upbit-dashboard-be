from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DashboardQuerySerializer, OperationalDashboardSerializer
from .services import DashboardDataNotReady, get_operational_dashboard


class DashboardDailyView(APIView):
    """Return period-based Executive Dashboard metrics from the existing URL."""

    def get(self, request) -> Response:
        query = DashboardQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        try:
            dashboard = get_operational_dashboard(**query.validated_data)
        except DashboardDataNotReady as exc:
            period_end = exc.args[0]
            raise NotFound(
                f"Dashboard data through {period_end.isoformat()} is not available. "
                "Run `python manage.py refresh_dashboard` first."
            ) from exc

        return Response(OperationalDashboardSerializer(dashboard).data)
