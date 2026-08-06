from django.contrib.admin import SimpleListFilter
from django.db.models import Q

class BCustomerCodeFilter(SimpleListFilter):
    title = 'Buyer Customer Code'
    parameter_name = 'b_customer_code'

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.request = request

    def has_output(self):
        # Only show this filter if user has typed in the search bar
        return bool(self.request.GET.get('q'))

    def lookups(self, request, model_admin):
        if not request.GET.get('q'):
            return ()
        
        q = request.GET.get('q')
        codes = (
            model_admin.get_queryset(request)
            # .filter(Q(s_customer_code__icontains=q) | Q(b_customer_code__icontains=q))
            .values_list('b_customer_code', flat=True)
            .distinct()
            .order_by('b_customer_code')
        )
        return [(code, code) for code in codes if code]        
        # return ()

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(b_customer_code=self.value())
        return queryset
class SCustomerCodeFilter(SimpleListFilter):
    title = 'Seller Customer Code'
    parameter_name = 's_customer_code'

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.request = request

    def has_output(self):
        return bool(self.request.GET.get('q'))

    def lookups(self, request, model_admin):
        if not request.GET.get('q'):
            return ()
        
        q = request.GET.get('q')
        codes = (
            model_admin.get_queryset(request)
            # .filter(Q(s_customer_code__icontains=q) | Q(b_customer_code__icontains=q))
            .values_list('s_customer_code', flat=True)
            .distinct()
            .order_by('s_customer_code')
        )
        return [(code, code) for code in codes if code]        

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(s_customer_code=self.value())
        return queryset
