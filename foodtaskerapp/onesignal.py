import json
import requests

from django.conf import settings


class OneSignal(object):
    def __init__(self, message, player_ids):
        self.message = message
        self.player_ids = player_ids
        print("%s", player_ids)
    def send_message(self):
        header = {"Content-Type": "application/json",
                  "Authorization": "Basic OTY4N2EzYTEtYzA3ZS00OTQ4LWFjYjctNzlkOGVkOTY4NDhk"}

        payload = {
            "app_id": "bccfa89a-4893-41ba-930a-03182e9e5abd",
            "include_player_ids": self.player_ids,
            "contents": {"en": self.message}
        }

        res = requests.post(
            "https://onesignal.com/api/v1/notifications",
            headers=header,
            data=json.dumps(payload)
        )

        print(res.status_code, res.content)
