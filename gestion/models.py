from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
import requests

class CategoriaTematica(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=200, default="Autor Desconocido")  
    edicion = models.CharField(max_length=100)
    archivo = models.FileField(upload_to='libros/', default='path/to/default/file.pdf')
    propietario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Cambiado a SET_NULL y null=True
    total_paginas = models.PositiveIntegerField()  # Total de páginas del libro
    isbn = models.CharField(max_length=20, null=True, blank=True)  # ISBN del libro
    tematica = models.ForeignKey(CategoriaTematica, on_delete=models.SET_NULL, null=True, blank=True)  # Temática del libro
    fecha_subida = models.DateTimeField(auto_now_add=True)  # Fecha de subida

    def obtener_tematica_por_isbn(self, isbn):
        # Función para obtener la temática del libro a partir del ISBN
        try:
            # Usar Open Library API
            url = f'https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data'
            response = requests.get(url)
            data = response.json()

            if data:
                libro_data = data.get(f'ISBN:{isbn}', {})
                tematicas = libro_data.get('subjects', [])
                if tematicas:
                    # Si se encuentran temáticas, devolver la primera o la más relevante
                    return CategoriaTematica.objects.get_or_create(nombre=tematicas[0]['name'])[0]
            return None
        except Exception as e:
            print(f"Error al obtener temática para ISBN {isbn}: {e}")
            return None

    def save(self, *args, **kwargs):
        # Obtener la temática automáticamente al guardar
        if self.isbn and not self.tematica:
            self.tematica = self.obtener_tematica_por_isbn(self.isbn)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.titulo} - {self.autor} ({self.isbn})"


class LibroUsuario(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.libro.titulo} - {self.usuario.username}"


class DatoUsuario(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    paginas_leidas = models.PositiveIntegerField(default=0)  # Páginas leídas
    porcentaje_lectura = models.FloatField(default=0.0)  # Porcentaje de lectura
    puntuacion = models.IntegerField(null=True, blank=True)  # Puntuación del 1 al 10
  
    def save(self, *args, **kwargs):
        # Actualizar el porcentaje de lectura antes de guardar
        if self.libro.total_paginas > 0:
            self.porcentaje_lectura = (self.paginas_leidas / self.libro.total_paginas) * 100

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.libro.titulo} - {self.usuario.username}"


class Prestamo(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)  # Fecha en la que se inicia el préstamo
    fecha_fin = models.DateTimeField(null=True)  # Cambiado a null=True para que sea opcional

    def __str__(self):
        return f"{self.libro.titulo} prestado a {self.usuario.username}"

    def save(self, *args, **kwargs):
        # Calcular la fecha de fin del préstamo (5 meses a partir de la fecha de inicio) si no se establece
        if not self.fecha_fin:
            self.fecha_fin = self.fecha_inicio + timedelta(days=150)  # 5 meses
        super().save(*args, **kwargs)

    def devolver(self, libro):
        # Método para devolver el libro
        LibroUsuario.objects.filter(libro=libro).delete()


class RankingAnual(models.Model):
    año = models.PositiveIntegerField()
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    puntuacion_media = models.FloatField()

    class Meta:
        unique_together = ('año', 'libro')

    def __str__(self):
        return f"Ranking {self.año}: {self.libro.titulo} - Puntuación: {self.puntuacion_media}"

