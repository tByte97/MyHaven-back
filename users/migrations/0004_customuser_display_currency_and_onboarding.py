from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0003_telegram_link_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='display_currency',
            field=models.CharField(
                choices=[
                    ('UAH', 'UAH'),
                    ('USD', 'USD'),
                    ('EUR', 'EUR'),
                    ('PLN', 'PLN'),
                    ('GBP', 'GBP'),
                    ('CHF', 'CHF'),
                ],
                default='UAH',
                max_length=3,
            ),
        ),
        migrations.AddField(
            model_name='customuser',
            name='onboarding_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='tracking_sources',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='currency',
            field=models.CharField(
                choices=[
                    ('UAH', 'UAH'),
                    ('USD', 'USD'),
                    ('EUR', 'EUR'),
                    ('PLN', 'PLN'),
                    ('GBP', 'GBP'),
                    ('CHF', 'CHF'),
                ],
                default='UAH',
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='language',
            field=models.CharField(
                choices=[
                    ('uk', 'Українська'),
                    ('en', 'English'),
                    ('de', 'Deutsch'),
                    ('es', 'Español'),
                    ('pl', 'Polski'),
                ],
                default='uk',
                max_length=5,
            ),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='theme',
            field=models.CharField(
                choices=[
                    ('light', 'Frost'),
                    ('dark', 'Abyss'),
                    ('auto', 'System'),
                ],
                default='light',
                max_length=10,
            ),
        ),
    ]
