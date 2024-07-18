# daily_checks/utils.py
from .models import OpenPosition

def build_open_positions_dict():
    # Fetching only required fields
    open_positions = OpenPosition.objects.select_related('stock').values(
        'interval', 'period', 'stock__code', 'stock__exchange_prefix')
    
    open_positions_dict = {}
    for position in open_positions:
        stock_code = f"{position['stock__code']}.{position['stock__exchange_prefix']}" if position['stock__exchange_prefix'] else position['stock__code']
        
        open_positions_dict[stock_code] = {
            'interval': position['interval'],
            'period': position['period']
        }
    return open_positions_dict