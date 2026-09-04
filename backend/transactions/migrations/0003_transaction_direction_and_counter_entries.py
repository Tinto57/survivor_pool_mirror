import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_remove_transaction_qr_code_transaction_token'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='is_cancelled',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='cancelled_at',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='cancelled_by',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='cancellation_reason',
        ),
        migrations.AddField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(
                choices=[('PAYMENT', 'Payment'), ('ABONDMENT', 'Abondment')],
                default='PAYMENT',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='counter_entry_of',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='counter_entry',
                to='transactions.transaction',
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='partner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='partners.partner',
            ),
        ),
    ]