from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    avatar = models.ImageField(null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "username"]


class Subscription(models.Model):
    subsciber = models.ForeignKey(
        User, related_name="subscriptions", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name="subscribers", on_delete=models.CASCADE
    )
