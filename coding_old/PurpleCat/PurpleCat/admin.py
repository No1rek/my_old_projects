from django.contrib import admin
from PurpleCat.models import *


# -------------- Post
class PostInline(admin.TabularInline):
    model = Post
    extra = 0

class PostAdmin(admin.ModelAdmin):
    class Meta:
        model = Post
        inlines = [PostInline]


admin.site.register(Post, PostAdmin)


# -------------- Category
class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0

class CategoryAdmin(admin.ModelAdmin):
    class Meta:
        model = Category
        inlines = [CategoryInline]


admin.site.register(Category, CategoryAdmin)


# -------------- User
class UserInline(admin.TabularInline):
    model = User
    extra = 0

class UserAdmin(admin.ModelAdmin):
    class Meta:
        model = User
        inlines = [UserInline]


admin.site.register(User, UserAdmin)


# -------------- Image
class ImageInline(admin.TabularInline):
    model = Image
    extra = 0


class ImageAdmin(admin.ModelAdmin):
    class Meta:
        model = Image
        inlines = [ImageInline]


admin.site.register(Image, ImageAdmin)


# -------------- Post
class LikeInline(admin.TabularInline):
    model = Like
    extra = 0

class LikeAdmin(admin.ModelAdmin):
    class Meta:
        model = Like
        inlines = [LikeInline]

admin.site.register(Like, LikeAdmin)
