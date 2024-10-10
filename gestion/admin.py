from django.contrib import admin
from .models import CategoriaTematica, Libro, ISBNLibro, Prestamo, ProgresoLectura, PuntuacionLibro
admin.site.register(CategoriaTematica)
admin.site.register(Libro)
admin.site.register(ISBNLibro)
admin.site.register(Prestamo)
admin.site.register(ProgresoLectura)
admin.site.register(PuntuacionLibro)