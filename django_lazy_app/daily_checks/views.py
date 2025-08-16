from django.shortcuts import render
from .libs.yahoo_fin import get_open_positions,get_buys
from django.http import JsonResponse

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from .models import Stock, OpenPosition
from .forms import StockForm, OpenPositionForm

from django.shortcuts import get_object_or_404

from .utils import build_open_positions_dict

from pprint import pprint

def index(request):
    
    open_posistions = build_open_positions_dict()
    
    buys = {
        "ee":get_buys(max_count=5,exchanges=["ee"]),
        "stx":get_buys(max_count=1,exchanges=["stx"])
        }
    ret_open = get_open_positions(open_posistions)
    
    # stock_df.to_csv(stock+".csv",index=True)
    pageData = {"buys":buys,"open_position_analysis":ret_open}
    pprint(pageData)
    return render(request,'index.html',pageData)

def graph_view(request):
    data = {
        'labels': ['January', 'February', 'March', 'April', 'May', 'June'],
        'datasets': [{
            'label': 'Sales Data',
            'data': [65, 59, 80, 81, 56, 55],
            'backgroundColor': 'rgba(54, 162, 235, 0.2)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        }]
    }
    return render(request, 'graph.html', {'data': data})


class StockCreateView(CreateView):
    model = Stock
    form_class = StockForm
    template_name = 'stock_form.html'
    success_url = reverse_lazy('stock_list')  # Replace 'stock_list' with your actual list view or desired URL

class StockUpdateView(UpdateView):
    model = Stock
    form_class = StockForm
    template_name = 'stock_form.html'
    success_url = reverse_lazy('stock_list')  # Replace 'stock_list' with your actual list view or desired URL

class StockListView(ListView):
    model = Stock
    template_name = 'stock_list.html'

class StockDeleteView(DeleteView):
    model = Stock
    template_name = 'stock_confirm_delete.html'
    success_url = reverse_lazy('stock_list')  # Redirects to the stock list after deletion

    def get(self, request, *args, **kwargs):
        """This method ensures that the delete view does not require a confirmation page."""
        return self.post(request, *args, **kwargs)

class OpenPositionCreateView(CreateView):
    model = OpenPosition
    form_class = OpenPositionForm
    template_name = 'open_position_form.html'
    success_url = reverse_lazy('open_position_list')  # Replace 'open_position_list' with your actual list view or desired URL

class OpenPositionUpdateView(UpdateView):
    model = OpenPosition
    form_class = OpenPositionForm
    template_name = 'open_position_form.html'
    success_url = reverse_lazy('open_position_list')  # Replace 'open_position_list' with your actual list view or desired URL

class OpenPositionListView(ListView):
    model = OpenPosition
    template_name = 'open_position_list.html'

class OpenPositionDeleteView(DeleteView):
    model = OpenPosition
    template_name = 'open_position_confirm_delete.html'
    success_url = reverse_lazy('open_position_list')  # Redirects to the list after deletion

    def get(self, request, *args, **kwargs):
        """This method ensures that the delete view does not require a confirmation page."""
        return self.post(request, *args, **kwargs)

class OpenPositionCreateForStockView(CreateView):
    model = OpenPosition
    form_class = OpenPositionForm
    template_name = 'open_position_form.html'

    def get_initial(self):
        """Prepopulate the stock field of the form based on the stock_id URL parameter."""
        stock_id = self.kwargs.get('stock_id')
        stock = get_object_or_404(Stock, pk=stock_id)
        return {'stock': stock}

    def get_success_url(self):
        """Redirect back to stock list or wherever is appropriate after creation."""
        return reverse_lazy('open_position_list')
    
class OpenPositionCreateForStockCodeView(CreateView):
    model = OpenPosition
    form_class = OpenPositionForm
    template_name = 'open_position_form.html'

    def get_initial(self):
        """Prepopulate the stock field of the form based on the stock_code URL parameter."""
        stock_code = self.kwargs.get('stock_code')
        stock = get_object_or_404(Stock, code=stock_code)
        return {'stock': stock}

    def get_success_url(self):
        """Redirect back to stock list or wherever is appropriate after creation."""
        return reverse_lazy('open_position_list')
