from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import ProtectedError
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Cliente, Caso, Expediente, Pago, EstadoCaso
from .forms import ClienteForm


def clientes_lista(request):
    clientes = Cliente.objects.all()
    return render(request, 'casos/clientes_lista.html', {'clientes': clientes})


def cliente_crear(request):
    form = ClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('casos:clientes_lista')
    return render(request, 'casos/cliente_form.html', {'form': form, 'titulo': 'Nuevo cliente'})


def cliente_editar(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    form = ClienteForm(request.POST or None, instance=cliente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('casos:clientes_lista')
    return render(request, 'casos/cliente_form.html', {'form': form, 'titulo': 'Editar cliente'})


def cliente_eliminar(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    error = None
    if request.method == 'POST':
        try:
            cliente.delete()
            return redirect('casos:clientes_lista')
        except ProtectedError:
            error = 'No se puede eliminar: el cliente tiene casos registrados.'
    return render(request, 'casos/cliente_eliminar.html', {'cliente': cliente, 'error': error})


def lista_casos(request):
    estado_get = request.GET.get('estado')
    estado_id = estado_get if estado_get is not None else request.COOKIES.get('ultimo_estado', '')
    casos = Caso.objects.select_related('cliente', 'estado').prefetch_related('abogados__usuario')
    if estado_id.isdigit():
        casos = casos.filter(estado_id=estado_id)
    else:
        estado_id = ''
    response = render(request, 'casos/lista_casos.html', {
        'casos': casos,
        'estados': EstadoCaso.objects.all(),
        'estado_id': estado_id,
    })
    if estado_get is not None:
        response.set_cookie('ultimo_estado', estado_id, max_age=60 * 60 * 24 * 30)
    return response


def detalle_caso(request, id):
    caso = get_object_or_404(Caso, id=id)
    if request.method == 'POST':
        if not caso.estado.permite_pagos:
            messages.error(request, f"No se registró el pago: el caso está en estado '{caso.estado}' y no permite pagos.")
        else:
            try:
                monto = Decimal(request.POST.get('monto', ''))
                if not monto.is_finite() or monto <= 0:
                    raise InvalidOperation
            except InvalidOperation:
                messages.error(request, 'El monto no es válido.')
            else:
                Pago.objects.create(
                    caso=caso,
                    monto=monto,
                    fecha=timezone.localdate(),
                    descripcion=request.POST.get('descripcion') or 'Pago',
                )
                messages.success(request, 'Pago registrado correctamente.')
        return redirect('casos:detalle_caso', id=caso.id)
    return render(request, 'casos/detalle_caso.html', {
        'caso': caso,
        'expedientes': caso.expedientes.all(),
        'pagos': caso.pagos.all(),
    })


def subir_documento(request, id):
    expediente = get_object_or_404(Expediente, id=id)
    if request.method == 'POST':
        archivo = request.FILES.get('documento')
        if archivo:
            expediente.documento = archivo
            expediente.save()
            messages.success(request, 'Documento subido correctamente.')
        else:
            messages.error(request, 'Selecciona un archivo.')
    return redirect('casos:detalle_caso', id=expediente.caso.id)


def api_caso(request, id):
    caso = get_object_or_404(Caso, id=id)
    return JsonResponse({
        'codigo': caso.codigo,
        'cliente': caso.cliente.nombres,
        'estado': caso.estado.nombre,
        'abogados': [a.usuario.get_full_name() or a.usuario.username for a in caso.abogados.all()],
        'num_expedientes': caso.expedientes.count(),
        'total_pagado': float(caso.total_pagado()),
    }, json_dumps_params={'ensure_ascii': False})