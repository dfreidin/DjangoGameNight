from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.index, name="index"),
    url(r"^register$", views.register, name="register"),
    url(r"^login$", views.login, name="login"),
    url(r"^logout$", views.logout, name="logout"),
    url(r"^edit$", views.edit, name="edit"),
    url(r"^pw_change$", views.change_password, name="pw_change"),
    url(r"^home$", views.home, name="home"),
    url(r"^add_game/?$", views.add_game, name="add_game"),
    url(r"^search_games$", views.search_games, name="search_games"),
    url(r"^update_ratings$", views.update_ratings, name="update_ratings"),
    url(r"^profiles/(?P<username>[a-zA-Z0-9_@+.-]+)/?$", views.profile, name="profile"),
    url(r"^get_bgg_collection/?$", views.get_bgg_collection, name="get_bgg_collection"),
    url(r"^add_from_collection/?$", views.add_from_collection, name="add_from_collection"),
    url(r"^remove_game/(?P<bgg_id>\d+)/?$", views.remove_game, name="remove_game"),
    url(r"^new_group$", views.new_group, name="new_group"),
    url(r"^groups/(?P<id>\d+)/?$", views.group, name="group"),
    url(r"^groups/(?P<id>\d+)/edit_name/?$", views.edit_group_name, name="edit_group_name"),
    url(r"^groups/(?P<id>\d+)/random/?$", views.get_random_game, name="get_random_game"),
    url(r"^groups/(?P<id>\d+)/add/?$", views.add_to_group, name="add_to_group"),
    url(r"^groups/(?P<id>\d+)/remove/(?P<username>[a-zA-Z0-9_@+.-]+)/?$", views.remove_from_group, name="remove_from_group"),
    url(r'^filter_table/(?P<table_type>\w+)/(?P<group_id>\d+)?/(?P<username>[a-zA-Z0-9_@+.-]+)?', views.filter_table, name="filter_table")
]