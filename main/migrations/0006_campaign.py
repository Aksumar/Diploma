# Generated by Django 3.2.3 on 2021-05-31 01:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_rename_id_customer_customer_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_cost', models.FloatField()),
                ('sms_cost', models.FloatField()),
                ('email_cost', models.FloatField()),
            ],
        ),
    ]
