from django.core.management.base import BaseCommand
from daily_checks.models import Stock
from daily_checks.libs.stock_lists import STOCK_LIST

class Command(BaseCommand):
    help = 'Loads stock data into the database'

    def handle(self, *args, **options):
        for market, data in STOCK_LIST.items():
            suffix = data['yf_suffix']
            for code, details in data['stocks'].items():
                stock_code = code
                _, created = Stock.objects.update_or_create(
                    code=stock_code,
                    defaults={
                        'name': code,  # Assuming name is the same as the code if not given
                        'exchange_prefix': suffix,
                        'default_interval': details['interval'],
                        'default_period': details['period']
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully added stock: {stock_code}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Updated stock: {stock_code}'))