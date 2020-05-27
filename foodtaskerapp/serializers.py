from django.contrib.auth.models import User

from rest_framework import serializers

from oauth2_provider.models import AccessToken

from foodtaskerapp.models import Restaurant, Meal, Customer, Driver, Order, OrderDetails, MealCategory, Modifier, UpsellAndExtra, LoyaltyProgram


class RestaurantSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, restaurant):
        request = self.context.get('request')
        logo_url = restaurant.logo.url
        return request.build_absolute_uri(logo_url)

    class Meta:
        model = Restaurant
        fields = ("id", "name", "phone", "address", "logo", "opening_time", "closing_time",
                  "latitude", "longitude", "is_open")


class MealSerializer(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()

    def get_image(self, meal):
        request = self.context.get('request')
        image_url = meal.image.url
        return request.build_absolute_uri(image_url)

    class Meta:
        model = Meal
        fields = ("id", "name", "short_description", "image", "price", "modifier")


# ORDER SERIALIZERS
class OrderCustomerSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Customer
        fields = ("id", "name", "phone", "address")

class ModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modifier
        fields = ("id", "name", "restaurant", "upsellandextra")

class OrderDriverSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Customer
        fields = ("id", "name", "phone", "address")


class OrderRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ("id", "name", "phone", "address")


class OrderMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ("id", "name", "price")


class OrderMealModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpsellAndExtra
        fields = ("id", "name")


class LoyaltyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyProgram
        fields = ("user", "loyalty_amount")


class OrderDetailsSerializer(serializers.ModelSerializer):
    meal = OrderMealSerializer()
    modifiers = OrderMealModifierSerializer(many=True)

    class Meta:
        model = OrderDetails
        fields = ("id", "meal", "quantity", "sub_total", "modifiers")


class CategoriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = MealCategory
        fields = ("id", "name", "categoryImage")


class UpsellSerializer(serializers.ModelSerializer):

    class Meta:
        model = UpsellAndExtra
        fields = ("id", "name", "price", "restaurant")



class OrderSerializer(serializers.ModelSerializer):
    customer = OrderCustomerSerializer()
    # driver = OrderDriverSerializer()
    # restaurant = OrderRestaurantSerializer()
    order_details = OrderDetailsSerializer(many=True)
    status = serializers.ReadOnlyField(source="get_status_display")

    class Meta:
        model = Order
        # fields = ("id", "customer", "restaurant", "driver", "order_details",
        #           "total", "status", "address", "extra_notes")
        fields = ("id", "customer", "order_details",
                  "total", "status", "address", "extra_notes", "pickup_time", "delivery_time")


class CustomerRegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField()
    avatar = serializers.CharField()
    email_id = serializers.EmailField()
    phone = serializers.CharField()

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
            raise serializers.ValidationError('Username is taken')
        except User.DoesNotExist:
            return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid username')


class CustomerOneSignalSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    onesignal_id = serializers.CharField()

    def validate_access_token(self, value):
        try:
            AccessToken.objects.get(token=value)
            return value
        except AccessToken.DoesNotExist:
            raise serializers.ValidationError(
                "The provided access token can't be found")
