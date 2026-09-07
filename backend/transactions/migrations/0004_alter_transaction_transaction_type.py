from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_transaction_direction_and_counter_entries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(
                choices=[
                    ('PAYMENT', 'Payment'),
                    ('ABONDMENT', 'Abondment'),
                    ('PAYMENT_CANCELLED', 'Payment Cancelled'),
                ],
                default='PAYMENT',
                max_length=20,
            ),
        ),
    ]
