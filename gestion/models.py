import requests
from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.exceptions import ValidationError

# Modelo para las temáticas de los libros
class CategoriaTematica(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

# Modelo para los libros
class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=200)
    edicion = models.CharField(max_length=100)
    archivo = models.FileField(upload_to='libros/', blank=True, null=True)
    propietario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='libros_propios')
    total_paginas = models.PositiveIntegerField(null=True, blank=True)
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True)
    tematica = models.ForeignKey(CategoriaTematica, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    en_prestamo = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo} - {self.autor} ({self.isbn})"

    def obtener_isbn(self):
        """
        Intenta obtener el ISBN automáticamente usando la API de Open Library.
        """
        # URL de la API de Open Library
        url = f"https://openlibrary.org/search.json?title={self.titulo}&author={self.autor}&edition={self.edicion}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Revisa si hay resultados y extrae el ISBN del primer libro que coincida
            if data['numFound'] > 0:
                libro_info = data['docs'][0]  # Primer resultado
                isbn_13 = libro_info.get('isbn', [None])[0]  # Obtener el primer ISBN disponible
                return isbn_13
        return None

    def save(self, *args, **kwargs):
        # Si el ISBN no fue proporcionado manualmente, intenta obtenerlo automáticamente
        if not self.isbn:
            isbn_automatico = self.obtener_isbn()
            if isbn_automatico:
                self.isbn = isbn_automatico
            else:
                raise ValidationError("No se pudo obtener el ISBN automáticamente. Por favor, agrégalo manualmente.")
        
        # Asegurarse de llamar al método 'save' original de Django
        super(Libro, self).save(*args, **kwargs)

# Modelo para gestionar el progreso de lectura del usuario
class ProgresoLectura(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    pagina_actual = models.PositiveIntegerField(default=0)
    porcentaje_lectura = models.FloatField(default=0.0)

    def actualizar_progreso(self):
        if self.libro.total_paginas:
            self.porcentaje_lectura = (self.pagina_actual / self.libro.total_paginas) * 100
            self.save()

    def __str__(self):
        return f"{self.usuario.username} - {self.libro.titulo}: {self.porcentaje_lectura}% leído"

# Modelo para la puntuación de los libros
class PuntuacionLibro(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    puntuacion = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.usuario.username} - {self.libro.titulo}: {self.puntuacion}/10"

# Modelo para los préstamos de libros
class Prestamo(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    usuarios = models.ManyToManyField(User, related_name='prestamos')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.fecha_fin:
            self.fecha_fin = self.fecha_inicio + timedelta(days=150)
        self.libro.en_prestamo = True
        self.libro.save()
        super(Prestamo, self).save(*args, **kwargs)

    def finalizar_prestamo(self, usuario):
        self.usuarios.remove(usuario)
        if not self.usuarios.exists():
            self.libro.en_prestamo = False
        self.libro.save()
        super(Prestamo, self).save()

    def __str__(self):
        return f"{self.libro.titulo} prestado a {', '.join([user.username for user in self.usuarios.all()])}"

# Modelo para asociar un libro con su ISBN
class ISBNLibro(models.Model):
    isbn = models.CharField(max_length=20, unique=True)
    libro = models.OneToOneField(Libro, on_delete=models.CASCADE, related_name='isbn_libro')
    tematica = models.ForeignKey(CategoriaTematica, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.libro.titulo} - ISBN: {self.isbn}"

