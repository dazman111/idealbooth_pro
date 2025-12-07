from django.urls import path
from . import views


urlpatterns = [
    path('', views.blog_home, name='blog_home'),

    # Admin blog
    path('admin/manage/', views.manage_blog, name='manage_blog'),
    path('admin/article/add/', views.add_article, name='add_article'),
    path('admin/article/edit/<int:article_id>/', views.edit_article, name='edit_article'),
    path('admin/article/delete/<int:article_id>/', views.delete_article, name='delete_article'),
    
    # Commentaire blog
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('ajax/comment/', views.ajax_post_comment, name='ajax_post_comment'),

    # Like blog
    path('article/<int:article_id>/like/', views.like_article, name='like_article'),
    path('like/', views.like_article, name='like_article'),

]
