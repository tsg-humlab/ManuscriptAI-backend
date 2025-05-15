from django.db import models
from django.contrib.auth.models import User


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="activities")
    endpoint =  models.CharField(max_length=64)
    created = models.DateTimeField(auto_now_add=True)
    input = models.JSONField()
    output = models.JSONField()

    def __str__(self):
        return f'User: {self.user} -- Endpoint: {self.endpoint} -- Created: {self.created}'