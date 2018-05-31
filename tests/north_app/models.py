from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)


class Reader(models.Model):
    name = models.CharField(max_length=100)


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    pages = models.IntegerField()
    readers = models.ManyToManyField(Reader)
