from django.urls import path
from . import views
from .views import StockCreateView, StockUpdateView, OpenPositionCreateView, OpenPositionUpdateView,StockListView,OpenPositionListView,StockDeleteView,OpenPositionDeleteView,index,OpenPositionCreateForStockView,OpenPositionCreateForStockCodeView

urlpatterns = [
    path('', index, name='home'),
    path('stock/create/', StockCreateView.as_view(), name='stock_create'),
    path('stock/update/<int:pk>/', StockUpdateView.as_view(), name='stock_update'),
    path('stock/delete/<int:pk>/', StockDeleteView.as_view(), name='stock_delete'),
    path('open-position/create-for-stock/<int:stock_id>/', OpenPositionCreateForStockView.as_view(), name='open_position_create_with_stock'),
    path('create-open-position/<str:stock_code>/', OpenPositionCreateForStockCodeView.as_view(), name='create_open_position_by_code'),
    path('open-position/create/', OpenPositionCreateView.as_view(), name='open_position_create'),
    path('open-position/update/<int:pk>/', OpenPositionUpdateView.as_view(), name='open_position_update'),
    path('open-position/delete/<int:pk>/', OpenPositionDeleteView.as_view(), name='open_position_delete'),
    path('open-position/', OpenPositionListView.as_view(), name='open_position_list'),
    path('stock/', StockListView.as_view(), name='stock_list'),
    path('graph/', views.graph_view, name='graph'),

    
]
