from django.contrib import admin
from .models import Category, Location, Post, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'location', 'is_published', 'pub_date', 'created_at')
    list_filter = ('is_published', 'category', 'location', 'pub_date', 'created_at')
    search_fields = ('title', 'text')
    date_hierarchy = 'pub_date'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text',)

