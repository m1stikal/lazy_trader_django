from django.db import models

INTERVALS = [
        ('1d', 'Daily'),
        ('1wk', 'Weekly'),
        ('3mo', '3 Monthly'),
        ('1y', 'Yearly'),
    ]


class Platform(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Stock(models.Model):
    PLATFORM = [
        ('stx','Satrix'),
        ('ee','Easy Equities')
    ]
    code = models.CharField(max_length=8,default='',null=True,blank=True)
    name = models.CharField(max_length=32,default='',null=True,blank=True)
    exchange_prefix = models.CharField(max_length=8,default='JO',null=True,blank=True)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    default_interval = models.CharField(max_length=16, choices=INTERVALS, default='1d')
    default_period = models.CharField(max_length=16, choices=INTERVALS, default='3mo')

    def __str__(self):
        return f"{self.code}.{self.exchange_prefix} - {self.name}"


class OpenPosition(models.Model):
    
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, unique=True, null=True, blank=True)
    active = models.BooleanField(default=True)
    interval = models.CharField(max_length=16, choices=INTERVALS, default='1d')
    period = models.CharField(max_length=16, choices=INTERVALS, default='3mo')

    def __str__(self):
        return f"{self.stock.name} - Interval: {self.interval} - Period: {self.period}"