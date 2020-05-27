import json
import requests
from collections import defaultdict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from geopy import distance
from django.db import IntegrityError

import stripe

from rest_framework import (status, views, parsers, permissions)
from rest_framework.response import Response
from django.http import HttpResponse

from oauth2_provider.models import AccessToken
from oauth2_provider.views import TokenView

from foodtaskerapp.models import (
    Restaurant, Meal, Order, OrderDetails, Driver, Modifier,
    Customer, CustomerOneSignal, MealCategory, Modifier, UpsellAndExtra, LoyaltyProgram)
from foodtaskerapp.serializers import (
    RestaurantSerializer, MealSerializer, OrderSerializer,
    CustomerRegisterSerializer, LoginSerializer, CustomerOneSignalSerializer, CategoriesSerializer, ModifierSerializer,
    UpsellSerializer, LoyaltyProgramSerializer, OrderDetailsSerializer)
from foodtaskerapp.onesignal import OneSignal

stripe.api_key = settings.STRIPE_API_KEY


def customer_get_restaurants(request):
    restaurants = RestaurantSerializer(
        Restaurant.objects.all().order_by("-id"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"restaurants": restaurants})


def customer_get_meals(request, restaurant_id):
    meals = MealSerializer(
        Meal.objects.filter(restaurant_id=restaurant_id).order_by("category__meal"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"meals": meals})


def customer_get_modifiers(request, restaurant_id):
    modifier = ModifierSerializer(
        Modifier.objects.filter(id=restaurant_id).order_by("name"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"modifier": modifier})


def customer_get_modifiersItems(request, restaurant_id, modifier_id):
    modifier = UpsellSerializer(
        UpsellAndExtra.objects.filter(restaurant=restaurant_id, modifier=modifier_id).order_by("name"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"modifier": modifier})


@csrf_exempt
def customer_loyalty_account(request):
    access_token = AccessToken.objects.get(
        token=request.POST.get("access_token"), expires__gt=timezone.now())

    # Get Profile from token
    customer = access_token.user

    loyalty = LoyaltyProgramSerializer(
        LoyaltyProgram.objects.filter(user=customer),
        many=True,
        context={"request": request}
    ).data

    # restaurantID = Restaurant.objects.filter(id=1)
    # print(restaurantID)

    # for restaurant in restaurantID:
    #     print(restaurant.loyalty_program_percent)
    #     restaurant_percent = float(restaurant.loyalty_program_percent)

    # loyaltyCalculation = (restaurant_percent * 27.90) / 100.0
    # print(loyaltyCalculation)

    # loyaltyRewards = LoyaltyProgram.objects.filter(user=customer)
    # for loyal in loyaltyRewards:
    #     print(loyal.loyalty_amount)
    #     loyaltyCurrentAmount=loyal.loyalty_amount

    #     loyalNewAmount = float(loyaltyCurrentAmount) + float(loyaltyCalculation)
    #     print(loyalNewAmount)

    # # print loyaltyRewards
    # loyaltyRewards.update(
    #     loyalty_amount=loyalNewAmount)

    # customerInstance = access_token.user.customer

    # oneSignalID = CustomerOneSignal.objects.filter(customer=customerInstance)
    # print(oneSignalID)

    # onesignal_ids = oneSignalID
    # # print onesignal_ids
    # if onesignal_ids:
    #     player_ids = []
    #     message = 'Your order has been accepted and $%s0 has been added to your Loyalty Rewards account!' % float(loyaltyCalculation)
    # for onesignal_id in onesignal_ids:
    #         if onesignal_id.onesignal_id:
    #             player_ids.append(onesignal_id.onesignal_id)
    #             push = OneSignal(
    #                 message=message, player_ids=player_ids)
    #             print(message)
    #             print(push)
    #             push.send_message()

    return JsonResponse({"loyalty": loyalty})


def customer_get_itemsInCategories(request, restaurant_id, category_id):
    itemsInCategory = MealSerializer(
        Meal.objects.filter(restaurant_id=restaurant_id, category=category_id).order_by("name"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"itemsInCategory": itemsInCategory})


def customer_get_categories(request, restaurant_id):
    categories = CategoriesSerializer(
        MealCategory.objects.filter(restaurant_id=restaurant_id).order_by("name"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"categories": categories})


@csrf_exempt
def customer_add_order(request):
    """
        @params:
            access_token
            restaurant_id
            address
            order_details (json format)
            phone_no
            order_type
            pickup_time
            delivery_time
        """

    if request.method == "POST":

        print(request)
        # Get Token
        access_token = AccessToken.objects.get(
            token=request.POST.get("access_token"), expires__gt=timezone.now())

        print(access_token)
        # Get Profile from token

        customer = access_token.user.customer
        print(customer)
        # GET STRIPE token
        stripe_token = request.POST["stripe_token"]
        print(stripe_token)

        # GET PHONE NUMBER AND ASSIGN TO CUSTOMER
        # I tried to do this, but it did not work :(
        # customer.phone = request.POST["phone_no"]

        # Check whether customer has any order that is not delivered

        # if Order.objects.filter(customer=customer).exclude(status=Order.DELIVERED):
        #     return JsonResponse({"status": "fail", "error": "Your Last Order must be completed."})

        # Check the address
        if not request.POST["address"]:
            return JsonResponse({"status": "failed", "error": "Address is required"})

        # Get Order Details
        order_details = json.loads(request.POST["order_details"])
        print("ORDER DETAILS FROM APP: ", order_details)

        order_total = 0
        modifier_price_total = 0
        order_final_total = 0

        for meal in order_details:
            for item in meal['modifierItems']:
                modifier_price_total += UpsellAndExtra.objects.get(pk=item).price * meal["quantity"]
            order_total += Meal.objects.get(pk=meal["meal_id"]).price * meal["quantity"]

        print(order_total)
        print(modifier_price_total)

        order_final_total = order_total + modifier_price_total
        print(order_final_total)
        # Convert Price to Int and Send to Stripe
        order_converted_total = int(order_final_total)

        if len(order_details) > 0:

            # Step 1: Create a charge: This will Charge Customers Card
            charge = stripe.Charge.create(
                amount=order_converted_total * 100,  # Amount in Cents
                currency="aud",
                source=stripe_token,
                description="B!te Order"
            )

            if charge.status != "failed":
                # Step two - Create Order
                # Provide datetime in ISO format
                pickup_time = request.POST['pickup_time']
                delivery_time = request.POST['delivery_time']

                order = Order.objects.create(
                    customer=customer,
                    restaurant_id=request.POST["restaurant_id"],
                    total=order_final_total,
                    status=Order.PREPARING,
                    address=request.POST["address"],
                    phone=request.POST.get('phone_no', ''),
                    order_type=request.POST.get('order_type', 'pickup'),
                    pickup_time=pickup_time,
                    delivery_time=delivery_time,
                    extra_notes=request.POST['extra_notes']
                )
                # step two - Create Order Details
                for meal in order_details:
                    modifier_item_total = 0

                    detail = OrderDetails.objects.create(
                        order=order,
                        meal_id=meal["meal_id"],
                        quantity=meal["quantity"],
                        sub_total=Meal.objects.get(id=meal["meal_id"]).price * meal["quantity"])

                    for item in meal['modifierItems']:
                        item = UpsellAndExtra.objects.get(pk=item)
                        detail.modifiers.add(item)
                        detail.save()
                        modifier_item_total += item.price * meal["quantity"]
                    detail.sub_total += modifier_item_total
                    detail.save()

            customerInstance = access_token.user
            customerInstanceObject = access_token.user.customer
            print("CUSTOMER INSTANCE", customerInstance)
            print("CUSTOMER OBJECT", customerInstanceObject)

            loyaltyRewards = LoyaltyProgram.objects.filter(user=customerInstance)
            for loyal in loyaltyRewards:
                print(loyal.loyalty_amount)

            restaurantID = Restaurant.objects.filter(id=request.POST["restaurant_id"])
            print(restaurantID)
            for restaurant in restaurantID:
                print(restaurant.loyalty_program_percent)
                restaurant_percent = float(restaurant.loyalty_program_percent)
                loyaltyCalculation = (restaurant_percent * float(order_converted_total)) / 100.0
                print(loyaltyCalculation)

            if not loyaltyRewards:
                # print("LOYAL NEW AMOUNT: ", loyalNewAmount)
                print("No Loyalty Account, Creating now")
                print("CUSTOMER", customer)
                loyaltyRewards.create(
                    user=customerInstance,
                    loyalty_amount=loyaltyCalculation)
            else:
                loyalNewAmount = float(loyal.loyalty_amount) + float(loyaltyCalculation)
                loyaltyRewards.update(
                    loyalty_amount=loyalNewAmount)

            oneSignalID = CustomerOneSignal.objects.filter(customer=customerInstanceObject)
            print(oneSignalID)

            onesignal_ids = oneSignalID
            print(onesignal_ids)
            if onesignal_ids:
                player_ids = []
                message = 'Your order has been accepted and $%s0 has been added to your Loyalty Rewards account!' % float(
                    loyaltyCalculation)
            for onesignal_id in onesignal_ids:
                if onesignal_id.onesignal_id:
                    player_ids.append(onesignal_id.onesignal_id)
                    push = OneSignal(
                        message=message, player_ids=player_ids)
                    print(message)
                    print(push)
                    push.send_message()

        return HttpResponse("success")
    else:
        return HttpResponse("failed")


def customer_get_latest_order(request):
    access_token = AccessToken.objects.get(
        token=request.GET.get("access_token"), expires__gt=timezone.now())

    customer = access_token.user.customer
    order = OrderSerializer(Order.objects.filter(
        customer=customer).last()).data

    return JsonResponse({"order": order})


def restaurant_order_notification(request, last_request_time):
    print("request==============>", request.user.restaurant)
    print("last_request_time=======>", last_request_time)
    notification = Order.objects.filter(restaurant=request.user.restaurant,
                                        created_at__gt=last_request_time).count()

    return JsonResponse({"notification": notification})


def customer_driver_location(request):
    access_token = AccessToken.objects.get(
        token=request.GET.get("access_token"), expires__gt=timezone.now())

    customer = access_token.user.customer

    # Get Driver Assigned to Job's location
    current_order = Order.objects.filter(
        customer=customer, status=Order.ONTHEWAY).last()
    location = current_order.driver.location

    return JsonResponse({"location": location})


#############
# DRIVER API FUNCTIONS
#############

def driver_get_ready_orders(request):
    '''
    Get orders which are ready to be picked. Restaurant should be within 5km
    of the driver's location
    :param request: Django request object
    :return: List of orders which are ready
    '''

    restaurant = getattr(request.user, 'driver', None)

    orders = OrderSerializer(
        Order.objects.filter(status=Order.READY, driver=None,
                             restaurant=restaurant).order_by("-id"),
        many=True).data
    return JsonResponse({"orders": orders})


@csrf_exempt
def driver_pick_order(request):
    if request.method == "POST":
        access_token = AccessToken.objects.get(
            token=request.POST.get("access_token"), expires__gt=timezone.now())

        driver = access_token.user.driver

        # Check if Available for Driver Selection
        if Order.objects.filter(driver=driver).exclude(status=Order.ONTHEWAY):
            return JsonResponse({"status": "failed", "error": "Only One Order can be selected at the same time"})

        try:
            order = Order.objects.get(
                id=request.POST["order_id"],
                driver=None,
                status=Order.READY
            )

            order.driver = driver
            order.status = Order.ONTHEWAY
            order.picked_at = timezone.now()
            order.save()

            return JsonResponse({"status": "success"})

        except Order.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "This order has been picked up by another driver"})


def driver_get_latest_order(request):
    access_token = AccessToken.objects.get(
        token=request.GET.get("access_token"), expires__gt=timezone.now())

    driver = access_token.user.driver
    order = OrderSerializer(
        Order.objects.filter(driver=driver).order_by("picked_at").last()
    ).data

    return JsonResponse({"order": order})


@csrf_exempt
def driver_complete_order(request):
    access_token = AccessToken.objects.get(
        token=request.POST.get("access_token"), expires__gt=timezone.now())

    driver = access_token.user.driver
    order = Order.objects.get(id=request.POST["order_id"], driver=driver)
    order.status = Order.DELIVERED
    order.save()
    return JsonResponse({"status": "success"})


def driver_get_revenue(request):
    access_token = AccessToken.objects.get(
        token=request.GET.get("access_token"), expires__gt=timezone.now())

    driver = access_token.user.driver

    from datetime import timedelta

    revenue = {}
    today = timezone.now()
    current_weekdays = [
        today + timedelta(days=i) for i in range(0 - today.weekday(), 7 - today.weekday())]

    for day in current_weekdays:
        orders = Order.objects.filter(
            driver=driver,
            status=Order.DELIVERED,
            created_at__year=day.year,
            created_at__month=day.month,
            created_at__day=day.day
        )

        revenue[day.strftime("%a")] = sum(order.total for order in orders)

    return JsonResponse({"revenue": revenue})


@csrf_exempt
def driver_update_location(request):
    if request.method == "POST":
        access_token = AccessToken.objects.get(
            token=request.POST.get("access_token"), expires__gt=timezone.now())

        driver = access_token.user.driver

        # Set Location String
        driver.location = request.POST["location"]
        driver.save()

        return JsonResponse({"status": "success"})


def get_open_restaurants_near_customer(request):
    '''
    Returns a list of 10 restaurants which are open and near the user
    Latitude and longitude of the customer are required.
    If the starting id of the restaurant is provided, results are filtered 
    on restaurants having id more than that of the provided id
    :param request: http request
    :return: list of restaurants, each entry a dict of the restaurant's attributes
    '''
    from haversine import haversine
    latitude = float(request.GET.get('latitude'))
    longitude = float(request.GET.get('longitude'))
    starting_id = request.GET.get('starting_id')
    batch_size = int(request.GET.get('batch_size', 10))
    operating_distance = int(request.GET.get('distance', 5))
    if starting_id:
        restaurants = Restaurant.objects.filter(
            id__gt=starting_id).order_by('id')
    else:
        restaurants = Restaurant.objects.all().order_by('id')

    restaurants_within_distance = []
    for restaurant in restaurants:
        distance = None
        if restaurant.latitude and restaurant.longitude:
            distance = haversine((latitude, longitude),
                                 (restaurant.latitude, restaurant.longitude))
        if distance and distance <= operating_distance and restaurant.is_open():
            restaurants_within_distance.append(restaurant)
        if len(restaurants_within_distance) >= batch_size:
            break

    serialized_restaurants = RestaurantSerializer(
        restaurants_within_distance,
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"restaurants": serialized_restaurants})


def get_meal_modifiers(request, restaurant_id):
    meals = Meal.objects.filter(restaurant_id=restaurant_id)
    modifiers = defaultdict(list)
    for meal in meals:
        meal_modifiers = meal.modifier.all()
        for meal_modifier in meal_modifiers:
            modifiers[meal_modifier].append(meal)
    meal_extras = dict()
    for modifier in modifiers.keys():
        meal_extras[modifier.name] = MealSerializer(
            modifiers[modifier], many=True, context={'request': request}).data

    return JsonResponse({"modifiers": meal_extras})


def get_oldest_order(request):
    '''
    Returns the oldest order which is awaiting a driver in a vicinity of 5km
    requires the latitude and longitude of the driver to determine the business
    :param request: request object of Django
    :return: Order details of the oldest order available
    '''

    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')

    # return error if latitude and longitude are not provided
    if not (latitude and longitude):
        return JsonResponse({
            'status': 'failed',
            'error': 'Driver co-ordinates required'
        })

    # convert to float
    latitude = float(latitude)
    longitude = float(longitude)

    # cycle through orders which are ready sorted by order created on time
    # return first order which is in the vicinity of the driver
    open_orders = Order.objects.filter(
        status=Order.READY).order_by('created_at')
    for order in open_orders:
        if order.restaurant.get_distance(latitude, longitude) <= 5:
            return JsonResponse({'order': OrderSerializer(order).data})

    return JsonResponse({
        "status": "success",
        "message": "No orders are ready in your vicinity"
    })


@csrf_exempt
def RegisterCustomerView(request):
    """
    This view will be used to register a customer
    """
    if request.method == "POST":
        user = User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password'],
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name']
        )
        Customer.objects.create(
            user=user,
            # avatar=serializer.validated_data['avatar'],
            phone=request.POST['phone'],
            email_id=request.POST['email_id']
        )

        print(request.POST['username'])
        print(request.POST['password'])
        print(request.POST['first_name'])
        print(request.POST['last_name'])
        print(request.POST['phone'])
        print(request.POST['email_id'])
        return JsonResponse({
            "status": "success"
        })
    return JsonResponse({"status": "Failed"})


class LoginView(views.APIView):
    """
    This view will be used to log in(get access_token of) a customer/resturant
    """

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            res = requests.post(settings.OAUTH2_SERVER_URL + '/o/token/', data={
                'username': serializer.validated_data['username'],
                'password': serializer.validated_data['password'],
                'grant_type': 'password'
            }, auth=(settings.FOODTASKER_OAUTH2_APP_CLIENT_ID,
                     settings.FOODTASKER_OAUTH2_APP_CLIENT_SECRET))
            response_data = res.json()

            if response_data.get('access_token'):
                user = AccessToken.objects.get(
                    token=response_data.get('access_token')).user
                response_data['username'] = user.username
                response_data['first_name'] = user.first_name
                response_data['last_name'] = user.last_name
                if hasattr(user, 'customer'):
                    response_data['user_type'] = 'customer'
                    # response_data['avatar'] = user.customer.avatar
                    response_data['email_id'] = user.customer.email_id
                    response_data['phone'] = user.customer.phone
                if hasattr(user, 'restaurant'):
                    response_data['user_type'] = 'restaurant'
                    response_data['logo'] = user.restaurant.logo.url
                return Response(response_data)
            return Response(
                {
                    'status': 'failed',
                    'error_message': 'Couldn\'t login with provided credentials'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerOneSignalView(views.APIView):
    """
    This view will be used to add onesignal id to a customer
    """

    def post(self, request, format=None):
        serializer = CustomerOneSignalSerializer(data=request.data)
        if serializer.is_valid():
            user = AccessToken.objects.get(
                token=serializer.validated_data['access_token']).user
            if hasattr(user, 'customer'):
                if CustomerOneSignal.objects.filter(customer=user.customer).exists():
                    print("ONESIGNAL MODEL EXISTS FOR USER", user.customer)
                    CustomerOneSignal.objects.update(
                        onesignal_id=serializer.validated_data['onesignal_id'])
                else:
                    print("ONESIGNAL MODEL DOESN'T EXIST - CREATE NOW")
                    CustomerOneSignal.objects.create(
                        customer=user.customer,
                        onesignal_id=serializer.validated_data['onesignal_id']
                    )
            return JsonResponse({"status": "registered"})
            return JsonResponse(
                {
                    'status': 'failed',
                    'error_message': 'User is not customer'
                }
            )
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def RestaurantOrdersView(request):
    """
    This view will return all orders for the restaurant
    """

    restaurantId = request.POST['restaurantId']
    restaurant = Restaurant.objects.get(id=restaurantId)

    print(restaurant)
    print(restaurant.name)
    print(restaurant.id)

    orders = OrderSerializer(
        Order.objects.filter(restaurant=restaurant).order_by("-id"), many=True).data

    return JsonResponse({"orders": orders})
    # orders = Order.objects.filter(restaurant=user.restaurant)
    # new_orders = defaultdict(list)
    # key = 'order'
    # for order in orders:
    #     # print(order.customer)
    #     orderDet = list(order.order_details.all())
    #     # print(orderDet)
    #     new_orders[key+":{'id':"+str(order.id)+",'customer':"+str(order.customer)+",'customerImg':"+str(order.customer.avatar)+", restaurant':"+str(order.restaurant)+
    #      ",'driver':"+str(order.driver)+",'order_details':"+str(orderDet)+",'total':"+str(order.total)+",'status':"+str(order.status)+
    #                                           ",'address':" + str(order.address) +",'extra_notes':"+str(order.extra_notes)+"}"].append(order)
    # return Response(OrderSerializer(new_orders, many=True).data)


class RestaurantChangeOrderStatusView(views.APIView):
    """
    This view will be used to change order status
    """

    def post(self, request, format=None):
        user = AccessToken.objects.get(
            token=request.data['access_token']).user
        if hasattr(user, 'restaurant'):
            try:
                order = Order.objects.get(id=request.data['order_id'])
                if order.restaurant == user.restaurant:
                    order.status = Order.DELIVERED
                    order.save()
                    onesignal_ids = order.customer.onesignal.all()
                    if onesignal_ids:
                        player_ids = []
                        message = 'Your order from %s is ready. Please head in store to colect it' % order.restaurant.name
                        for onesignal_id in onesignal_ids:
                            if onesignal_id.onesignal_id:
                                player_ids.append(onesignal_id.onesignal_id)
                        push = OneSignal(
                            message=message, player_ids=player_ids)
                        push.send_message()
                    return JsonResponse({"message": "Order Status Changed"})
                return Response(
                    {
                        'status': 'failed',
                        'error_message': 'Not owner restaurant'
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
            except Order.DoesNotExist:
                return Response(
                    {
                        'status': 'failed',
                        'error_message': 'Order can\'t be found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(
            {
                'status': 'failed',
                'error_message': 'Not a restaurant'
            },
            status=status.HTTP_403_FORBIDDEN
        )


@csrf_exempt
def restaurant_get_orderdetails(request):
    orderdetails_id = request.POST['order_id']

    orderDetails = OrderDetailsSerializer(
        OrderDetails.objects.filter(id=orderdetails_id),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"orderDetails": orderDetails})


@csrf_exempt
def restaurant_delivery_zone(request):
    print(request.POST['latitude'])
    print(request.POST['longitude'])

    centre_point = [{'latitude': request.POST['latitude'], 'longitude': request.POST['longitude']}]
    restaurant_id = 3

    restaurant = Restaurant.objects.get(id=restaurant_id)
    restaurant_point = [{'latitude': restaurant.latitude, 'longitude': restaurant.longitude}]

    radius = 5

    centre_point_tuple = tuple(centre_point[0].values())
    restaurant_point_tuple = tuple(restaurant_point[0].values())

    dis = distance.distance(centre_point_tuple, restaurant_point_tuple).km
    print("Distance: {}".format(dis))

    if dis <= radius:
        print("{} point is inside of the {} km radius from {}".format(centre_point_tuple, radius, restaurant.name))
        return JsonResponse({"available": "yes"})
    else:
        print("{} point is outside of the {} km radius from {}".format(centre_point_tuple, radius, restaurant.name))
        return JsonResponse({"available": "no"})


@csrf_exempt
def restaurant_get_opening_hours(request):
    restaurantId = request.POST['restaurantId']
    restaurant = Restaurant.objects.get(id=restaurantId)

    print(restaurant)
    print(restaurant.opening_time)
    print(restaurant.closing_time)
    print(restaurant.id)
    return JsonResponse({"open_at": restaurant.opening_time, "close_at": restaurant.closing_time})
