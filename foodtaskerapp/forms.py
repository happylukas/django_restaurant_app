from django import forms
from django.contrib.auth.models import User
from foodtaskerapp.models import Restaurant, Meal, MealCategory, Modifier, Order, OrderDetails, Customer, UpsellAndExtra

class UserForm(forms.ModelForm):
    email = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ("username", "password", "first_name", "last_name", "email")

class RestaurantForm(forms.ModelForm):
    opening_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'),
                                    help_text='Format: 22:00')
    closing_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'),
                                   help_text='Format: 22:00')

    class Meta:
        model = Restaurant
        fields = ("name", "phone", "address", "logo", "latitude", "longitude", "opening_time", "closing_time",
                  "is_open_for_orders")


class UserFormForEdit(forms.ModelForm):
    email = forms.CharField(max_length=100, required=True)
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

class OrderForm(forms.ModelForm):
    def __init__(self, restaurant, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all()
    class Meta:
        model = Order
        exclude = ("restaurant",)
class OrderDetailForm(forms.ModelForm):
    class Meta:
        model = OrderDetails
        exclude = ("restaurant",)
class CustomerDetailForm(forms.ModelForm):
    class Meta:
        model = Customer
        exclude = ("restaurant",)
class MealForm(forms.ModelForm):
    def __init__(self, restaurant, *args, **kwargs):
        super(MealForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = MealCategory.objects.filter(restaurant=restaurant)
        self.fields['modifier'] = forms.ModelMultipleChoiceField(queryset=Modifier.objects.filter(restaurant=restaurant),
                                                                 widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Meal
        exclude = ("restaurant",)

class UpsellAndExtraForm(forms.ModelForm):
    class Meta:
        model = UpsellAndExtra
        fields = ("id", "name", "price")
        # exclude = ("restaurant",)


class MealCategoryForm(forms.ModelForm):
    class Meta:
        model = MealCategory
        exclude = ()

class ModifierForm(forms.ModelForm):
    class Meta:
        model = Modifier
        exclude = ("restaurant",)
