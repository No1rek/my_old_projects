from django.db import models
import datetime
from ckeditor.fields import RichTextField
from PurpleCat.settings import MEDIA_DIR
import os


class User(models.Model):
    name = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    email = models.EmailField()

class Category(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField(default='')
    link = models.CharField(max_length=64, default='', blank=True)
    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.link == '':
            self.link = self.name.lower()
        super(Category, self).save(*args, **kwargs)

class Image(models.Model):
    image = models.ImageField(upload_to=MEDIA_DIR)
    upload_time = models.DateTimeField(default=None, blank=True)
    def save(self, *args, **kwargs):
        self.upload_time = datetime.datetime.now()
        super(Image, self).save(*args, **kwargs)

class Post(models.Model):
    title = models.TextField(default='Title')
    description = models.TextField(default='')
    date_published = models.DateTimeField(blank=True)
    hidden = models.BooleanField()
    content = RichTextField()
    # content = models.TextField()

    likes = models.IntegerField(default=0, blank=True)
    views = models.IntegerField(default=0, blank=True)

    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        self.date_published = datetime.datetime.now()
        super(Post, self).save(*args, **kwargs)

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
