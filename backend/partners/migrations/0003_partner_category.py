import django.db.models.deletion
from django.db import migrations, models


def assign_default_category(apps, schema_editor):
    Category = apps.get_model('partners', 'Category')
    Partner = apps.get_model('partners', 'Partner')

    if not Partner.objects.filter(category__isnull=True).exists():
        return

    default_category, _ = Category.objects.get_or_create(name='Non catégorisé')
    Partner.objects.filter(category__isnull=True).update(category=default_category)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0002_partner_is_featured'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='partner',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='partners', to='partners.category'),
        ),
        migrations.RunPython(assign_default_category, noop),
        migrations.AlterField(
            model_name='partner',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partners', to='partners.category'),
        ),
    ]
