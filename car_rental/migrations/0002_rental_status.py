from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_rental', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rental',
            name='status',
            field=models.CharField(
                choices=[
                    ('active',    'Активен'),
                    ('returned',  'Возвращён'),
                    ('cancelled', 'Отменён'),
                ],
                default='active',
                db_index=True,
                max_length=20,
                verbose_name='Статус',
            ),
        ),
    ]
