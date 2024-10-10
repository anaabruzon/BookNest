from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect  # Importación de render y redirect
from django.db.models import Avg
from django.core.exceptions import ValidationError
from .models import Libro, ProgresoLectura, PuntuacionLibro, Prestamo

# Vista para mostrar la biblioteca del usuario
class BibliotecaView(LoginRequiredMixin, ListView):
    model = Libro
    template_name = 'biblioteca.html'
    context_object_name = 'libros'

    def get_queryset(self):
        return Libro.objects.filter(propietario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puntuaciones'] = PuntuacionLibro.objects.filter(usuario=self.request.user)
        context['progreso'] = ProgresoLectura.objects.filter(usuario=self.request.user)
        return context

# Vista para mostrar libros disponibles para préstamo
class PrestamosView(LoginRequiredMixin, ListView):
    model = Libro
    template_name = 'prestamos.html'
    context_object_name = 'libros'

    def get_queryset(self):
        return Libro.objects.filter(en_prestamo=False)

# Vista para prestar un libro
class PrestarLibroView(LoginRequiredMixin, RedirectView):
    pattern_name = 'prestamos'

    def post(self, request, *args, **kwargs):
        libro = get_object_or_404(Libro, id=self.kwargs['libro_id'], en_prestamo=False)

        # Intentar obtener el ISBN si no está registrado
        if not libro.isbn:
            try:
                libro.isbn = libro.obtener_isbn()
                libro.save()
            except ValidationError as e:
                return render(request, 'error.html', {'error': str(e)})  # render definido correctamente

        prestamo, created = Prestamo.objects.get_or_create(libro=libro)
        prestamo.usuarios.add(request.user)
        prestamo.save()
        libro.en_prestamo = True
        libro.save()

        # Crear un registro de progreso de lectura si no existe
        ProgresoLectura.objects.get_or_create(usuario=request.user, libro=libro)

        return super().get_redirect_url()

# Vista para devolver un libro
class DevolverLibroView(LoginRequiredMixin, RedirectView):
    pattern_name = 'biblioteca'

    def post(self, request, *args, **kwargs):
        libro = get_object_or_404(Libro, id=self.kwargs['libro_id'])
        prestamo = get_object_or_404(Prestamo, libro=libro)

        if request.user in prestamo.usuarios.all():
            prestamo.finalizar_prestamo(request.user)

        return super().get_redirect_url()

# Vista para mostrar detalles del libro
class DetalleLibroView(LoginRequiredMixin, DetailView):
    model = Libro
    template_name = 'detalle_libro.html'
    context_object_name = 'libro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        libro = self.get_object()
        context['puntuacion'] = PuntuacionLibro.objects.filter(libro=libro, usuario=self.request.user).first()
        context['progreso'] = ProgresoLectura.objects.filter(libro=libro, usuario=self.request.user).first()
        return context

# Vista para puntuar un libro
class PuntuarLibroView(LoginRequiredMixin, RedirectView):
    pattern_name = 'detalle_libro'

    def post(self, request, *args, **kwargs):
        libro = get_object_or_404(Libro, id=self.kwargs['libro_id'])
        puntuacion_value = request.POST.get('puntuacion')

        PuntuacionLibro.objects.update_or_create(
            usuario=request.user,
            libro=libro,
            defaults={'puntuacion': puntuacion_value}
        )

        return super().get_redirect_url(libro_id=libro.id)

# Vista para mostrar el ranking anual de libros
class RankingView(LoginRequiredMixin, ListView):
    template_name = 'ranking.html'
    context_object_name = 'ranking'

    def get_queryset(self):
        # Agrupar y contar las puntuaciones por libro, tomando el promedio y ordenando de mayor a menor
        return PuntuacionLibro.objects.values('libro__titulo').annotate(promedio=Avg('puntuacion')).order_by('-promedio')[:5]
