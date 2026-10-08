from django.urls import path
from . import views

app_name = 'casos'

urlpatterns = [
    path('clientes/', views.clientes_lista, name='clientes_lista'),
    path('clientes/nuevo/', views.cliente_crear, name='cliente_crear'),
    path('clientes/<int:id>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:id>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),
    path('casos/', views.lista_casos, name='lista_casos'),
    path('casos/<int:id>/', views.detalle_caso, name='detalle_caso'),
    path('casos/api/<int:id>/', views.api_caso, name='api_caso'),
    path('expedientes/<int:id>/documento/', views.subir_documento, name='subir_documento'),
]