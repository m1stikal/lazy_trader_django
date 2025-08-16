from django.core.management.base import BaseCommand
from daily_checks.models import Stock,Platform

class Command(BaseCommand):
    help = 'Updates the platform field in the Stock model based on the stock code prefix'

    def handle(self, *args, **options):
        stocks = Stock.objects.all()
        stx_count = 0
        ee_count = 0
        for stock in stocks:
            if stock.code.startswith('STX'):
                stock.platform = Platform.objects.get(code="stx")
                stx_count += 1
            else:
                stock.platform = Platform.objects.get(code="ee")
                ee_count += 1
            stock.save()

        self.stdout.write(self.style.SUCCESS(f'Updated {stx_count} stocks to platform Satrix (stx).'))
        self.stdout.write(self.style.SUCCESS(f'Updated {ee_count} stocks to platform Easy Equities (ee).'))