from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.db import models

from . import validators


class FileInput(models.Model):
    file_transactions = models.FileField("Транзакционнае данные",
                                         validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx']),
                                                     validators.validate_file_content
                                                     ], default=None
                                         )

    file_goods = models.FileField("Данные о товарах",
                                  validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx']),
                                              validators.validate_file_content
                                              ], default=None)

    file_customers = models.FileField("Данные о клиентах",
                                      validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx'], ),
                                                  validators.validate_file_content
                                                  ], default=None)

    min_conf = models.FloatField(default=0.01,
                                 validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)

    min_support = models.FloatField(default=0.01,
                                    validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)

    clusters = models.BooleanField(default=True)


class Rule(models.Model):
    cluster_class = models.CharField(max_length=200)
    left = models.CharField(max_length=200)
    left_support = models.FloatField()
    right = models.CharField(max_length=200)
    right_support = models.FloatField()
    support = models.FloatField()
    confidence = models.FloatField()
    lift = models.FloatField()

    def clean(self):
        self.support = self.support * 100
        self.confidence = self.confidence * 100

    def __str__(self):
        return f"{self.cluster_class}: {self.left} - {self.right}"


class Customer(models.Model):
    customer_id = models.CharField(max_length=200, primary_key=True)
    cluster_id = models.CharField(max_length=200)
    mean_cheque = models.FloatField(default=1)
    return_proba = models.FloatField(default=1)
    purchases = models.TextField()


class Campaign(models.Model):
    phone_cost = models.FloatField(default=0)
    sms_cost = models.FloatField(default=0)
    email_cost = models.FloatField(default=0)

    phone_percent = models.FloatField(default=0)
    sms_percent = models.FloatField(default=0)
    email_percent = models.FloatField(default=0)

    calls_limit = models.IntegerField(default=0)

    budget = models.FloatField(default=0)
    cheque_up = models.FloatField(default=0)
    sale = models.FloatField(default=0)
    min = models.FloatField(default=0)
