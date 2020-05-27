from foodtaskerapp.models import Customer, Driver

def create_user_by_type(backend, user, request, response, *args, **kwargs):
    if backend.name == 'facebook':
        avatar = 'https://graph.facebook.com/%s/picture?width=1000&height=1000' % response['id']

    if request['user_type'] == "driver" and not Driver.objects.filter(user_id=user.id):
        driver = Driver.objects.create(user_id=user.id, avatar=avatar)
        driver.user.is_active = False
        driver.user.save()

    elif not Customer.objects.filter(user_id=user.id):
        Customer.objects.create(user_id=user.id, avatar = avatar)
