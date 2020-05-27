from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from foodtaskerapp.forms import UserForm, RestaurantForm, UpsellAndExtraForm, UserFormForEdit, MealForm, \
    MealCategoryForm, ModifierForm, OrderForm, OrderDetailForm, CustomerDetailForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from foodtaskerapp.models import Meal, Order, Driver, MealCategory, Modifier, OrderDetails, Customer, UpsellAndExtra
from django.db.models import Sum, Count, Case, When


# Create your views here.
def home(request):
    return redirect(restaurant_home)


@login_required(login_url='/restaurant/sign-in/')
def restaurant_home(request):
    return redirect(restaurant_order)


@login_required(login_url='/restaurant/sign-in/')
def restaurant_account(request):
    user_form = UserFormForEdit(instance=request.user)
    restaurant_form = RestaurantForm(instance=request.user.restaurant)

    if request.method == "POST":
        user_form = UserFormForEdit(request.POST, instance=request.user)
        restaurant_form = RestaurantForm(request.POST, request.FILES, instance=request.user.restaurant)

    if user_form.is_valid() and restaurant_form.is_valid():
        user_form.save()
        restaurant_form.save()

    if request.user.restaurant.logo:
        restaurant_form.fields['logo'].required = False

    return render(request, 'restaurant/account.html', {
        "user_form": user_form,
        "restaurant_form": restaurant_form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_upsellandextra(request):
    upsellandextra = UpsellAndExtra.objects.all().order_by("-id")
    return render(request, 'restaurant/upsellandextra.html', {"upsellandextra": upsellandextra})


@login_required(login_url='/restaurant/sign-in/')
def restaurant_add_upsellandextra(request):
    form = UpsellAndExtraForm()
    if request.method == "POST":
        form = UpsellAndExtraForm(request.POST, request.FILES)
        if form.is_valid():
            upsellandextra = form.save(commit=False)
            # meal.restaurant = request.user.restaurant
            upsellandextra.save()
            return redirect(restaurant_upsellandextra)
    return render(request, 'restaurant/add_upsellandextra.html', {
        "form": form
    })


def restaurant_edit_upsellandextra(request, upsellandextra_id):
    form = UpsellAndExtraForm(instance=UpsellAndExtra.objects.get(id=upsellandextra_id))
    if request.method == "POST":
        form = UpsellAndExtraForm(request.POST, request.FILES,
                                  instance=UpsellAndExtra.objects.get(id=upsellandextra_id))
        if form.is_valid():
            form.save()
            return redirect(restaurant_upsellandextra)
    return render(request, 'restaurant/edit_upsellandextra.html', {
        "form": form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_meal(request):
    meals = Meal.objects.filter(restaurant=request.user.restaurant).order_by("-id")
    return render(request, 'restaurant/meal.html', {"meals": meals})


@login_required(login_url='/restaurant/sign-in/')
def restaurant_add_meal(request):
    form = MealForm(request.user.restaurant)
    if request.method == "POST":
        form = MealForm(request.user.restaurant, request.POST, request.FILES)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.restaurant = request.user.restaurant
            meal.save()
            return redirect(restaurant_meal)
    return render(request, 'restaurant/add_meal.html', {
        "form": form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_edit_meal(request, meal_id):
    form = MealForm(request.user.restaurant, instance=Meal.objects.get(id=meal_id))
    form.fields['image'].required = False

    if request.method == "POST":
        form = MealForm(request.user.restaurant, request.POST, request.FILES, instance=Meal.objects.get(id=meal_id))

        if form.is_valid():
            form.save()
            return redirect(restaurant_meal)

    return render(request, 'restaurant/edit_meal.html', {
        "form": form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_order(request):
    if request.method == "POST":
        order = Order.objects.get(id=request.POST["id"], restaurant=request.user.restaurant)

        if order.status == Order.PREPARING:
            order.status = Order.READY
            order.save()

    orders = Order.objects.filter(restaurant=request.user.restaurant).order_by("-id")
    print("orders=======>", orders.values())
    return render(request, 'restaurant/order.html', {"orders": orders})


@login_required(login_url='/restaurant/sign-in/')
def restaurant_add_order(request):
    form = OrderForm(request.user.restaurant)
    if request.method == "POST":
        form = OrderForm(request.user.restaurant, request.POST, request.FILES)

        if form.is_valid():
            order = form.save(commit=False)
            order.restaurant = request.user.restaurant
            order.save()
            return redirect(restaurant_order)

    return render(request, 'restaurant/add_order.html', {
        "form": form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_edit_order_detail(request, order_id):
    form = OrderDetailForm(instance=OrderDetails.objects.get(id=order_id))

    if request.method == "POST":
        form = OrderDetailForm(request.POST, request.FILES, instance=OrderDetails.objects.get(id=order_id))

        if form.is_valid():
            form.save()
            return redirect(restaurant_order)

    return render(request, 'restaurant/edit_order_detail.html', {
        "form": form
    })


def restaurant_edit_customer_detail(request, customer_id):
    form = CustomerDetailForm(instance=Customer.objects.get(id=customer_id))

    if request.method == "POST":
        form = CustomerDetailForm(request.POST, request.FILES, instance=OrderDetails.objects.get(id=customer_id))

        if form.is_valid():
            form.save()
            return redirect(restaurant_order)

    return render(request, 'restaurant/edit_customer_detail.html', {
        "form": form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_report(request):
    # Calculate Revenue and Number of Orders By Week
    from datetime import datetime, timedelta

    revenue = []
    orders = []

    # Calculate Weekdays
    today = datetime.now()
    current_weekdays = [today + timedelta(days=i) for i in range(0 - today.weekday(), 7 - today.weekday())]

    for day in current_weekdays:
        delivered_orders = Order.objects.filter(
            restaurant=request.user.restaurant,
            status=Order.DELIVERED,
            created_at__year=day.year,
            created_at__month=day.month,
            created_at__day=day.day
        )
        revenue.append(sum(order.total for order in delivered_orders))
        orders.append(delivered_orders.count())

    # Top 3 Meals
    top3_meals = Meal.objects.filter(restaurant=request.user.restaurant) \
                     .annotate(total_order=Sum('orderdetails__quantity')) \
                     .order_by("-total_order")[:3]
    meal = {
        "labels": [meal.name for meal in top3_meals],
        "data": [meal.total_order or 0 for meal in top3_meals]
    }

    # Top 3 Drivers
    top3_drivers = Driver.objects.annotate(
        total_order=Count(
            Case(
                When(order__restaurant=request.user.restaurant, then=1)
            )
        )
    ).order_by("-total_order")[:3]

    driver = {
        "labels": [driver.user.get_full_name() for driver in top3_drivers],
        "data": [driver.total_order for driver in top3_drivers]
    }

    return render(request, 'restaurant/report.html', {
        "revenue": revenue,
        "orders": orders,
        "meal": meal,
        "driver": driver
    })


def restaurant_sign_up(request):
    user_form = UserForm()
    restaurant_form = RestaurantForm()

    if request.method == "POST":
        user_form = UserForm(request.POST)
        restaurant_form = RestaurantForm(request.POST, request.FILES)

        if user_form.is_valid() and restaurant_form.is_valid():
            new_user = User.objects.create_user(**user_form.cleaned_data)
            new_user.is_active = True
            new_user.save()
            new_restaurant = restaurant_form.save(commit=False)
            new_restaurant.user = new_user
            new_restaurant.save()

            login(request, authenticate(
                username=user_form.cleaned_data["username"],
                password=user_form.cleaned_data["password"],
            ))

            return redirect(restaurant_home)

    return render(request, 'restaurant/sign_up.html', {
        "user_form": user_form,
        "restaurant_form": restaurant_form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_categories(request):
    categories = MealCategory.objects.filter(restaurant=request.user.restaurant).order_by("-id")
    return render(request, 'restaurant/restaurant_category.html', {"categories": categories})


@login_required(login_url='/restaurant/sign-in/')
def restaurant_add_category(request):
    form = MealCategoryForm()
    if request.method == "POST":
        form = MealCategoryForm(request.POST, request.FILES)

        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = request.user.restaurant
            category.save()
            return redirect(restaurant_categories)

    return render(request, 'restaurant/add_category.html', {
        "form": form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_edit_category(request, category_id):
    form = MealCategoryForm(instance=Meal.objects.get(id=category_id))
    if request.method == "POST":
        form = MealCategoryForm(request.POST, request.FILES, instance=MealCategory.objects.get(id=category_id))

        if form.is_valid():
            form.save()
            return redirect(restaurant_categories)

    return render(request, 'restaurant/edit_category.html', {
        "form": form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_modifiers(request):
    modifiers = Modifier.objects.filter(restaurant=request.user.restaurant).order_by("-id")
    return render(request, 'restaurant/restaurant_modifiers.html', {"modifiers": modifiers})


@login_required(login_url='/restaurant/sign-in/')
def restaurant_edit_modifier(request, modifier_id):
    form = ModifierForm(instance=Modifier.objects.get(id=modifier_id))
    if request.method == "POST":
        form = ModifierForm(request.POST, request.FILES, instance=Modifier.objects.get(id=modifier_id))

        if form.is_valid():
            form.save()
            return redirect(restaurant_modifiers)

    return render(request, 'restaurant/edit_modifier.html', {
        "form": form
    })


@login_required(login_url='/restaurant/sign-in/')
def restaurant_add_modifier(request):
    form = ModifierForm()
    if request.method == "POST":
        form = ModifierForm(request.POST, request.FILES)

        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = request.user.restaurant
            category.save()
            return redirect(restaurant_modifiers)

    return render(request, 'restaurant/add_modifier.html', {
        "form": form
    })

# @login_required(login_url='/restaurant/sign-in')
# def restaurant_download(request):
#     if request.method == "POST": 
# content = '<Order>' 
# order = Order.objects.get(id = request.POST["id"])
# cid = order.customer_id 
# customer = Customer.objects.get(id = cid)
# content = content + '<customer>'
# content = content + customer.user.get_full_name()
# content = content + '</customer>'
# #orderDetails = OrderDetails.objects.filter()
# orderDetails = OrderDetails.objects.filter(order_id = order.id)
# total = 0
# for orderdetail in orderDetails:
# content = content + '<OrderDetail>'
# content = content + '<Qty>'
# content = content + str(orderdetail.quantity)
# content = content + '</Qty>'
# mid = orderdetail.meal_id
# meal = Meal.objects.get(id = mid)
# content = content + '<Meal>'
# content = content + '<name>'
# content = content + meal.name
# content = content + '</name>'
# omiDetails = OrderMealItemDetails.objects.filter(Q(meal_id = mid) & Q(order_id = order.id))
# for omid in omiDetails:
# content = content + '<items>'
# content = content + '<item>'
# content = content + '<qty>'
# content = content + str(omid.quantity)
# content = content + '</qty>'
# content = content + '<item-name>'
# iid = omid.item_id
# item = Item.objects.get(item_id = iid)
# content = content + item.name
# content = content + '</item-name>'
# content = content + '<item-price>'
# content = content + str(omid.sub_total)
# total = total + omid.sub_total
# content = content + '</item-price>'
# content = content + '</item>'
# content = content + '</items>'
# content = content + '</Meal>'
# content = content + '<SubTotal>'
# content = content + str(orderdetail.sub_total)
# total = total + orderdetail.sub_total
# content = content + '</SubTotal>'
# content = content + '</OrderDetail>'
# content = content + '<Total>'
# content = content + str(total)
# content = content + '</Total>'
# content = content + '</Order>'
# response = HttpResponse(content_type='application/xml')
# response['Content-Disposition'] = 'attachment; filename="alethic.xml"'
# response.write(content)
# return response
# orders = Order.objects.filter(restaurant = request.user.restaurant).order_by("-id")
# return render(request, 'restaurant/download.html', {"orders": orders})
