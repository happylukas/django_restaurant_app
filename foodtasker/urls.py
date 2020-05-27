from django.conf.urls import url, include
from django.contrib import admin
from foodtaskerapp import views, apis
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [

    # Restaurant Methods
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home, name='home'),
    url(r'^restaurant/sign-in/$', auth_views.login,
        {'template_name': 'restaurant/sign_in.html'}, name='restaurant-sign-in'),
    url(r'^restaurant/sign-out', auth_views.logout,
        {'next_page': 'restaurant/sign-out.html'}, name='restaurant-sign-out'),
    url(r'^restaurant/sign-up', views.restaurant_sign_up, name='restaurant-sign-up'),
    url(r'^restaurant/$', views.restaurant_home, name='restaurant-home'),

    url(r'^restaurant/account/$', views.restaurant_account,
        name='restaurant-account'),
    url(r'^restaurant/meal/$', views.restaurant_meal, name='restaurant-meal'),
    url(r'^restaurant/meal/add/$', views.restaurant_add_meal,
        name='restaurant-add-meal'),
    url(r'^restaurant/meal/edit/(?P<meal_id>\d+)/$',
        views.restaurant_edit_meal, name='restaurant-edit-meal'),
    url(r'^restaurant/order/$', views.restaurant_order, name='restaurant-order'),
    url(r'^restaurant/order/add/$', views.restaurant_add_order,
        name='restaurant-add-order'),
    url(r'^restaurant/order/edit/(?P<order_id>\d+)/$',
        views.restaurant_edit_order_detail, name='restaurant-edit-order_detail'),
    url(r'^restaurant/customer/edit/(?P<customer_id>\d+)/$',
        views.restaurant_edit_customer_detail, name='restaurant-edit-customer_detail'),
    url(r'^restaurant/category/$', views.restaurant_categories,
        name='restaurant-categories'),
    url(r'^restaurant/category/edit/(?P<category_id>\d+)/$',
        views.restaurant_edit_category, name='restaurant-edit-category'),
    url(r'^restaurant/category/add/$', views.restaurant_add_category,
        name='restaurant-add-category'),
    url(r'^restaurant/modifiers/$', views.restaurant_modifiers,
        name='restaurant-modifiers'),
    url(r'^restaurant/modifiers/edit/(?P<modifier_id>\d+)/$',
        views.restaurant_edit_modifier, name='restaurant-edit-modifier'),
    url(r'^restaurant/modifiers/add/$', views.restaurant_add_modifier,
        name='restaurant-add-modifier'),

    url(r'^restaurant/upsellandextra/$', views.restaurant_upsellandextra,
        name='restaurant-upsellandextra'),
    url(r'^restaurant/upsellandextra/edit/(?P<upsellandextra_id>\d+)/$',
        views.restaurant_edit_upsellandextra, name='restaurant-edit-upsellandextra'),
    url(r'^restaurant/upsellandextra/add/$', views.restaurant_add_upsellandextra,
        name='restaurant-add-upsellandextra'),

    url(r'^restaurant/report/$', views.restaurant_report, name='restaurant-report'),

    # FACEBOOK AUTHENTICATION - REST AUTH
    url(r'^api/social/', include('rest_framework_social_oauth2.urls')),

    # Login API(Same for restaurant and customer)
    url(r'^api/login/$', apis.LoginView.as_view()),

    # API's For Restaurants
    url(r'^api/restaurant/orders/$', apis.RestaurantOrdersView),
    url(r'^api/restaurant/order/statuschange/$', apis.RestaurantChangeOrderStatusView.as_view()),
    url(r'^api/restaurant/getorderdetails/$', apis.restaurant_get_orderdetails),
    url(r'^api/restaurant/opening_hours/$', apis.restaurant_get_opening_hours),

    # API's FOR CUSTOMERS
    url(r'^api/customer/add/onesignalid/$',
        apis.CustomerOneSignalView.as_view()),
    url(r'^api/customer/signup/$', apis.RegisterCustomerView),
    url(r'^api/customer/restaurants/$', apis.customer_get_restaurants),
    url(r'^api/customer/nearby-restaurants/$',
        apis.get_open_restaurants_near_customer),
    url(r'^api/customer/loyaltyaccount/$', apis.customer_loyalty_account),
    url(r'^api/customer/categories/(?P<restaurant_id>\d+)/$', apis.customer_get_categories),
    url(r'^api/customer/getmodifier/(?P<restaurant_id>\d+)/$', apis.customer_get_modifiers),
    url(r'^api/customer/getmodifieritems/(?P<restaurant_id>\d+)/(?P<modifier_id>\d+)/$', apis.customer_get_modifiersItems),
    url(r'^api/customer/getcategoryitems/(?P<restaurant_id>\d+)/(?P<category_id>\d+)/$', apis.customer_get_itemsInCategories),
    url(r'^api/customer/meals/(?P<restaurant_id>\d+)/$', apis.customer_get_meals),
    url(r'^api/customer/order/add/$', apis.customer_add_order),
    url(r'^api/customer/order/latest/$', apis.customer_get_latest_order),
    url(r'^api/restaurant/order/notification/(?P<last_request_time>.+)/$',
        apis.restaurant_order_notification),
    url(r'^api/customer/driver/location/$', apis.customer_driver_location),
    url(r'^api/meal-extras/(?P<restaurant_id>\d+)/$', apis.get_meal_modifiers),

     url(r'^api/customer/check/delivery_address/$',
        apis.restaurant_delivery_zone),

    # APIs for DRIVERS
    url(r'^api/driver/orders/ready/$', apis.driver_get_ready_orders),
    url(r'^api/driver/order/pick/$', apis.driver_pick_order),
    url(r'^api/driver/order/latest/$', apis.driver_get_latest_order),
    url(r'^api/driver/order/complete/$', apis.driver_complete_order),
    url(r'^api/driver/revenue/$', apis.driver_get_revenue),
    url(r'^api/driver/location/update/$', apis.driver_update_location),
    url(r'^api/driver/order/get-ready-order/$', apis.get_oldest_order),

    # OAUTH2 Provider
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),


    # APIs for RESTAURANT


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
