from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime

# Create your models here.


class Restaurant(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='restaurant')
    name = models.CharField(max_length=500)
    phone = models.CharField(max_length=500)
    address = models.CharField(max_length=500)
    logo = models.ImageField(upload_to='restaurant_logo/', blank=False)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    loyalty_program_percent = models.CharField(max_length=500, blank=False, default=5)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True, default=None)
    longitude = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True, default=None)
    is_open_for_orders = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def is_open(self):
        now = timezone.now().astimezone(timezone.get_default_timezone())
        is_open = True
        if self.opening_time and self.closing_time:
            is_open = (self.opening_time <= now.time() < self.closing_time)
        print(is_open, self.is_open_for_orders)
        return is_open and self.is_open_for_orders

    def get_distance(self, latitude, longitude):
        '''
        Return distance of a point from this restaurant if the
        latitude and longitude of the restaurant are available
        :param latitude: Latitude of the point
        :param longitude: Longitude of the point
        :return: distance in kms
        '''
        from haversine import haversine
        if self.longitude and self.latitude:
            return haversine((latitude, longitude), (self.latitude, self.longitude))
        else:
            return None


class Customer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='customer')
    # avatar = models.ImageField(upload_to='user_images/', blank=False)
    phone = models.CharField(max_length=500, blank=True)
    address = models.CharField(max_length=500, blank=True)
    email_id = models.EmailField(null=True)

    def __str__(self):
        return self.user.get_full_name()


class LoyaltyProgram(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='loyalty')
    loyalty_amount = models.CharField(max_length=500, null=True, default=None)


class UserNotification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications')
    notification = models.TextField(blank=True, null=True, default=None)


class Driver(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='driver')
    avatar = models.CharField(max_length=500)
    phone = models.CharField(max_length=500, blank=True)
    address = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=500, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.SET_NULL, null=True, blank=True, default=None)

    def __str__(self):
        return self.user.get_full_name()


class MealCategory(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    name = models.CharField(max_length=256)
    short_description = models.CharField(max_length=256, default="")
    categoryImage = models.ImageField(upload_to='categoryImage/', blank=False)

    def __str__(self):
        return self.name


class UpsellAndExtra(models.Model):
    name = models.CharField(max_length=500, default="", unique=True)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    restaurant = models.ForeignKey(Restaurant, default=None)

    def __str__(self):
        return '%s:%s' % (self.name, self.price)


class Modifier(models.Model):
    name = models.CharField(max_length=256)
    restaurant = models.ForeignKey(Restaurant)
    upsellandextra = models.ManyToManyField(UpsellAndExtra, null=True, blank=True, default=None)

    def __str__(self):
        return self.name


class Meal(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    name = models.CharField(max_length=500)
    short_description = models.CharField(max_length=500)
    image = models.ImageField(upload_to='meal_images/', blank=False)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    category = models.ForeignKey(
        MealCategory, null=True, blank=True, default=None)
    is_available = models.BooleanField(default=True)
    modifier = models.ManyToManyField(
        Modifier, null=True, blank=True, default=None)

    def __str__(self):
        return self.name


class Order(models.Model):
    PREPARING = 1
    READY = 2
    DELIVERED = 3

    STATUS_CHOICES = (
        (PREPARING, "Preparing Order"),
        (READY, "Ready"),
        (DELIVERED, "Completed")
    )

    ORDER_TYPE_CHOICES = (
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery')
    )

    customer = models.ForeignKey(Customer, related_name='customer_details')
    restaurant = models.ForeignKey(Restaurant)
    driver = models.ForeignKey(Driver, blank=True, null=True)
    address = models.CharField(max_length=500)
    total = models.DecimalField(decimal_places=2, max_digits=10)
    status = models.IntegerField(choices=STATUS_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    picked_at = models.DateTimeField(blank=True, null=True)
    extra_notes = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=255, null=True,
                             blank=True, default=None)
    order_type = models.CharField(
        choices=ORDER_TYPE_CHOICES, max_length=20, default='pickup')
    pickup_time = models.CharField(max_length=100, blank=True, null=True)
    delivery_time = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class OrderDetails(models.Model):
    order = models.ForeignKey(Order, related_name='order_details')
    meal = models.ForeignKey(Meal)
    quantity = models.IntegerField()
    sub_total = models.DecimalField(decimal_places=2, max_digits=10)
    modifiers = models.ManyToManyField(
        UpsellAndExtra, blank=True, default=None)

    def __str__(self):
        return str(self.id)


class CustomerOneSignal(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='onesignal')
    onesignal_id = models.CharField(max_length=500, default="")
    
    def __str__(self):
        return '%s_onesignal_id' % self.customer.user.username

