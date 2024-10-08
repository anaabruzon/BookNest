from django.contrib import admin
from .models import CategoriaTematica, Libro, LibroUsuario, DatoUsuario, Prestamo, RankingAnual
admin.site.register(CategoriaTematica)
admin.site.register(Libro)
admin.site.register(LibroUsuario)
admin.site.register(DatoUsuario)
admin.site.register(Prestamo)
admin.site.register(RankingAnual)