from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

username_validator = RegexValidator(
    regex=r"^[\w.@+-]+\Z",
    message="Username may contain only letters, numbers, and @/./+/-/_ characters.",
)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=50, unique=True, validators=[username_validator]
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    avatar = models.ImageField(null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "username"]


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User, related_name="subscriptions", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name="subscribers", on_delete=models.CASCADE
    )
