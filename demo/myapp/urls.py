from django.urls import path
from . import views
# from .views import  list_parts
# from .views import parts_list
# from .views import PartDetailView
from .views import part_detail

urlpatterns = [
    #path("",views.home,name="home"),
    # path('parts/', list_parts, name='list-parts'),
    # path('api/parts/', parts_list, name='parts_list')
    #path('api/parts/<int:number>/', PartDetailView.as_view(), name='part-detail'),
    # path('parts/<int:number>/', part_detail, name='part-detail'),
    path('', part_detail, name='part-detail'),
]

