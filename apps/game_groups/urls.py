from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.index, name="index"),
    url(r"^register$", views.register, name="register"),
    url(r"^login$", views.login, name="login"),
    url(r"^logout$", views.logout, name="logout"),
    url(r"^home$", views.home, name="home"),
    url(r"^add_game$", views.add_game, name="add_game"),
    url(r"^search_games$", views.search_games, name="search_games"),
    url(r"^update_ratings$", views.update_ratings, name="update_ratings"),
    url(r"^profiles/(?P<username>[a-zA-Z0-9_@+.-]+)/?$", views.profile, name="profile"),
    url(r"^get_bgg_collection/?$", views.get_bgg_collection, name="get_bgg_collection"),
    url(r"^add_from_collection$", views.add_from_collection, name="add_from_collection"),
    url(r"^new_group$", views.new_group, name="new_group"),
    url(r"^groups/(?P<id>\d+)/?$", views.group, name="group"),
    url(r"^groups/(?P<id>\d+)/add/?$", views.add_to_group, name="add_to_group"),
    url(r"^groups/(?P<id>\d+)/remove/(?P<username>[a-zA-Z0-9_@+.-]+)/?$", views.remove_from_group, name="remove_from_group")
]