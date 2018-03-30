# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import forms as auth_forms, authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.utils.text import slugify
from django.db.models import Sum
import xml.etree.ElementTree as ET
import requests
from random import randint
from time import sleep
from urlparse import urlparse
from .models import *

# Create your views here.
def login(request):
    if request.method == "POST":
        user = authenticate(username=request.POST["username"], password=request.POST["password"])
        if user is not None:
            auth_login(request, user)
            return redirect(home)
    return redirect(index)

def index(request):
    reg_form = auth_forms.UserCreationForm()
    log_form = LoginForm()
    return render(request, "game_groups/index.html", {"reg_form": reg_form, "log_form": log_form})

def register(request):
    if request.method == "POST":
        form = auth_forms.UserChangeForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.save()
            auth_login(request, new_user)
            return redirect(home)
        messages.error(request, form.non_field_errors())
    return redirect(index)

@login_required(login_url=login)
def edit(request):
    if request.method == "GET":
        info = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email
        }
        edit_form = UserEditForm(instance=request.user, initial=info)
        pw_form = auth_forms.PasswordChangeForm(request.user)
        return render(request, "game_groups/edit.html", {"edit_form": edit_form, "pw_form": pw_form})
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
        return redirect(home)
    return redirect(index)

@login_required(login_url=login)
def change_password(request):
    if request.method != "POST":
        return redirect(edit)
    form = auth_forms.PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password updated")
    else:
        messages.error(request, "Password was not updated")
    return redirect(home)

@login_required(login_url=login)
def logout(request):
    auth_logout(request)
    return redirect(index)

def game_table_data(request, games, filters=None):
    id_list = ""
    for game in games:
        if id_list != "":
            id_list += ","
        id_list += str(game.bgg_id)
    games_xml = requests.get("https://www.boardgamegeek.com/xmlapi2/thing?id="+id_list).content
    games_data = ET.XML(games_xml)
    list_data = []
    for g in games_data.iter("item"):
        g_obj, created = Game.objects.get_or_create(bgg_id=g.attrib["id"])
        thumb_url = g.findtext("thumbnail")
        game_name = g.find("name").attrib["value"]
        bgg_link = "https://www.boardgamegeek.com/boardgame/" + str(g_obj.bgg_id)
        game_rating, created = Rating.objects.get_or_create(user=request.user, game=g_obj)
        min_players = g.find("minplayers").attrib["value"]
        max_players = g.find("maxplayers").attrib["value"]
        player_count = min_players + " - " + max_players
        game_categories = ""
        game_mechanics = ""
        for l in g.iter("link"):
            if l.attrib["type"] == "boardgamecategory":
                game_categories += l.attrib["value"] + ", "
            elif l.attrib["type"] == "boardgamemechanic":
                game_mechanics += l.attrib["value"] + ", "
        if filters:
            if int(max_players) < filters["min_players"] or int(min_players) > filters["max_players"] or filters["category"] not in game_categories.lower() or filters["mechanic"] not in game_mechanics.lower():
                continue
        list_data.append({
            "bgg_id": g_obj.bgg_id,
            "thumb": thumb_url,
            "name": game_name,
            "link": bgg_link,
            "rating": game_rating.rating,
            "owners": g_obj.owners.all(),
            "player_count": player_count,
            "categories": game_categories,
            "mechanics": game_mechanics
        })
    return list_data

@login_required(login_url=login)
def home(request):
    games = game_table_data(request, request.user.owned_games.all())
    games.sort(key=lambda x: x["name"])
    other_users = User.objects.exclude(id=request.user.id)
    return render(request, "game_groups/home.html", {"games": games, "other_users": other_users, "table_type": "home"})

@login_required(login_url=login)
def add_game(request):
    if request.method != "POST":
        return redirect(home)
    bgg_id = request.POST["game_choice"]
    game, created = Game.objects.get_or_create(bgg_id=bgg_id)
    game.owners.add(request.user)
    return redirect(home)

@login_required(login_url=login)
def search_games(request):
    if request.method != "POST":
        return redirect(home)
    search_term = slugify(request.POST["search"])
    url = "https://www.boardgamegeek.com/xmlapi2/search?type=boardgame&query=" + search_term
    print url
    response = requests.get(url).content
    search_data = ET.XML(response)
    if search_data.attrib["total"] == "0":
        messages.error(request, "No results found")
        return render(request, "game_groups/flash_message.html")
    id_list = ""
    for game in search_data.iter("item"):
        if id_list != "":
            id_list += ","
        id_list += game.attrib["id"]
    games_xml = requests.get("https://www.boardgamegeek.com/xmlapi2/thing?id="+id_list).content
    games_data = ET.XML(games_xml)
    result_data = []
    for game in games_data.iter("item"):
        bgg_id = game.attrib["id"]
        name = game.find("name").attrib["value"]
        thumb_url = game.findtext("thumbnail")
        result_data.append({"bgg_id": bgg_id, "name": name, "thumb": thumb_url})
    return render(request, "game_groups/search_table.html", {"results": result_data})

@login_required(login_url=login)
def update_ratings(request):
    if request.method != "POST":
        return redirect(home)
    for key in request.POST.keys():
        if key == "csrfmiddlewaretoken":
            continue
        game = Game.objects.get(bgg_id=key)
        r = Rating.objects.get(game=game, user=request.user)
        r.rating = request.POST[key]
        r.save()
    path = urlparse(request.META["HTTP_REFERER"]).path
    if path[:10] == "/profiles/":
        return redirect(profile, username=path[10:])
    else:
        return redirect(home)

@login_required(login_url=login)
def profile(request, username):
    users = User.objects.filter(username=username)
    if len(users) < 1:
        return redirect(home)
    games = game_table_data(request, users[0].owned_games.all())
    games.sort(key=lambda x: x["name"])
    return render(request, "game_groups/profile.html", {"user": users[0], "games": games, "table_type": "profile"})

@login_required(login_url=login)
def new_group(request):
    new_group = Group.objects.create(owner=request.user)
    new_group.members.add(request.user)
    return redirect(group, id=new_group.id)

@login_required(login_url=login)
def group(request, id):
    groups = Group.objects.filter(id=id)
    if len(groups) < 1 or request.user not in groups[0].members.all():
        return redirect(home)
    other_users = User.objects.exclude(game_groups=groups[0])
    sorted_games = Game.objects.filter(owners__game_groups=groups[0]).annotate(total_rating=Sum("ratings__rating")).filter(total_rating__gte=0).order_by("-total_rating")
    games = game_table_data(request, sorted_games)
    return render(request, "game_groups/group.html", {"group": groups[0], "other_users": other_users, "games": games, "table_type": "group"})

@login_required(login_url=login)
def add_to_group(request, id):
    if request.method != "POST":
        return redirect(home)
    groups = Group.objects.filter(id=id)
    if len(groups) < 1:
        return redirect(home)
    if "username" in request.POST:
        users = User.objects.filter(username=request.POST["username"])
        if groups[0].owner == request.user and len(users) > 0:
            groups[0].members.add(users[0])
            other_users = User.objects.exclude(game_groups=groups[0])
    return render(request, "game_groups/group_members.html", {"group": groups[0], "other_users": other_users})

@login_required(login_url=login)
def get_bgg_collection(request):
    if request.method != "POST":
        return redirect(home)
    username = request.POST["username"]
    url = "https://boardgamegeek.com/xmlapi2/collection?excludesubtype=boardgameexpansion&own=1&username="+slugify(username)
    response = requests.get(url)
    while response.status_code == 202:
        sleep(1)
        response = requests.get(url)
    games_data = ET.XML(response.content)
    if games_data.find("error"):
        messages.error(request, games_data.findtext("error/message"))
        return render(request, "game_groups/flash_message.html")
    if games_data.attrib["totalitems"] == "0":
        messages.error(request, "No games found")
        return render(request, "game_groups/flash_message.html")
    result_data = []
    for game in games_data.iter("item"):
        bgg_id = game.attrib["objectid"]
        games = Game.objects.filter(bgg_id=bgg_id, owners=request.user)
        if len(games) > 0:
            continue
        name = game.findtext("name")
        thumb_url = game.findtext("thumbnail")
        result_data.append({"bgg_id": bgg_id, "name": name, "thumb": thumb_url})
    return render(request, "game_groups/collection_table.html", {"results": result_data})

@login_required(login_url=login)
def add_from_collection(request):
    if request.method != "POST":
        return redirect(home)
    choices = request.POST.getlist("game_choices")
    for bgg_id in choices:
        game, created = Game.objects.get_or_create(bgg_id=bgg_id)
        game.owners.add(request.user)
    return redirect(home)

@login_required(login_url=login)
def remove_from_group(request, id, username):
    groups = Group.objects.filter(id=id)
    users = User.objects.filter(username=username)
    if len(groups) > 0 and len(users) > 0 and groups[0].owner == request.user:
        groups[0].members.remove(users[0])
    other_users = User.objects.exclude(game_groups=groups[0])
    return render(request, "game_groups/group_members.html", {"group": groups[0], "other_users": other_users})

@login_required(login_url=login)
def filter_table(request, table_type, username=None, group_id=None):
    context = {"table_type": table_type}
    filters = None
    if request.method != "POST":
        return redirect(home)
    filters = {
        "category": request.POST["category"].lower(),
        "mechanic": request.POST["mechanic"].lower(),
        "min_players": int(request.POST["min_players"]),
        "max_players": int(request.POST["max_players"])
    }
    if table_type == "home":
        game_list = request.user.owned_games.all()
    elif table_type == "profile":
        users = User.objects.filter(username=username)
        if len(users) < 1:
            return redirect(home)
        game_list = users[0].owned_games.all()
    elif table_type == "group":
        groups = Group.objects.filter(id=id)
        if len(groups) < 1:
            return redirect(home)
        context["group"] = groups[0]
        game_list = Game.objects.filter(owners__game_groups=groups[0]).annotate(total_rating=Sum("ratings__rating")).filter(total_rating__gte=0).order_by("-total_rating")
    else:
        return redirect(home)
    games = game_table_data(request, game_list, filters=filters)
    context["games"] = games
    return render(request, "game_groups/owned_games_table.html", context=context)

@login_required(login_url=login)
def remove_game(request, bgg_id):
    games = Game.objects.filter(bgg_id=bgg_id)
    if len(games) > 0:
        request.user.owned_games.remove(games[0])
    return redirect(home)

@login_required(login_url=login)
def edit_group_name(request, id):
    if request.method != "POST":
        return redirect(home)
    groups = Group.objects.filter(id=id)
    if len(groups) < 1 or groups[0].owner != request.user:
        return redirect(home)
    new_name = request.POST["group_name"]
    groups[0].name = new_name
    groups[0].save()
    return HttpResponse(new_name)

@login_required(login_url=login)
def get_random_game(request, id):
    groups = Group.objects.filter(id=id)
    if len(groups) < 1:
        return HttpResponse("")
    game_list = Game.objects.filter(owners__game_groups=groups[0]).annotate(total_rating=Sum("ratings__rating")).filter(total_rating__gte=0).order_by("-total_rating")
    game = [game_list[randint(0, len(game_list))]]
    game_table = game_table_data(request, game)
    context = {
        "table_type": "group",
        "group": groups[0],
        "games": game_table
    }
    return render(request, "game_groups/owned_games_table.html", context=context)