from django.contrib import admin

# Register your models here.
from foodtaskerapp.models import Restaurant, Customer, Driver, Meal, Order, OrderDetails, UserNotification, CustomerOneSignal, LoyaltyProgram
from foodtaskerapp.models import Modifier, UpsellAndExtra, MealCategory

class ModifierAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant','get_upsellandextra')
    def get_upsellandextra(self, obj):
        return ",".join([p.name+"+"+str(p.price) for p in obj.upsellandextra.all()])
    fields = ['name', 'restaurant', 'upsellandextra']
    autocomplete_fields = ['upsellandextra']
pass

admin.site.register(Restaurant)
admin.site.register(Customer)
admin.site.register(Driver)
admin.site.register(Meal)
admin.site.register(Order)
admin.site.register(OrderDetails)
admin.site.register(UserNotification)
admin.site.register(CustomerOneSignal)
admin.site.register(UpsellAndExtra)
admin.site.register(Modifier, ModifierAdmin)
admin.site.register(LoyaltyProgram)
admin.site.register(MealCategory)
