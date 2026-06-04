from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_rental', '0002_rental_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='photo',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='cars/',
                verbose_name='Фотография',
            ),
        ),
    ]
