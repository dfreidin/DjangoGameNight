# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import forms as auth_forms, authenticate, login as auth_login, logout as auth_logout
from django.utils.text import slugify
from django.db.models import Sum
import xml.etree.ElementTree as ET
import requests
from time import sleep
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
    reg_form = UserRegForm()
    log_form = LoginForm()
    return render(request, "game_groups/index.html", {"reg_form": reg_form, "log_form": log_form})

def register(request):
    if request.method == "POST":
        form = UserRegForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.save()
            auth_login(request, new_user)
            return redirect(home)
        messages.error(request, form.non_field_errors())
    return redirect(index)

@login_required(login_url=login)
def edit(request):
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
        return redirect(home)
    return redirect(index)

@login_required(login_url=login)
def logout(request):
    auth_logout(request)
    return redirect(index)

def game_table_data(request, games):
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
        list_data.append({
            "bgg_id": g_obj.bgg_id,
            "thumb": thumb_url,
            "name": game_name,
            "link": bgg_link,
            "rating": game_rating.rating,
            "owners": g_obj.owners.all()
        })
    return list_data

@login_required(login_url=login)
def home(request):
    games = game_table_data(request, request.user.owned_games.all())
    other_users = User.objects.exclude(id=request.user.id)
    return render(request, "game_groups/home.html", {"games": games, "other_users": other_users})

@login_required(login_url=login)
def add_game(request):
    if request.method == "GET":
        return render(request, "game_groups/add_game.html")
    elif request.method == "POST":
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
    return redirect(home)

@login_required(login_url=login)
def profile(request, username):
    users = User.objects.filter(username=username)
    if len(users) < 1:
        return redirect(home)
    games = game_table_data(request, users[0].owned_games.all())
    return render(request, "game_groups/profile.html", {"user": users[0], "games": games})

@login_required(login_url=login)
def new_group(request):
    new_group = Group.objects.create(owner=request.user)
    new_group.members.add(request.user)
    return redirect(group, id=new_group.id)

@login_required(login_url=login)
def group(request, id):
    groups = Group.objects.filter(id=id)
    if len(groups) < 1:
        return redirect(home)
    other_users = User.objects.exclude(game_groups=groups[0])
    sorted_games = Game.objects.filter(owners__game_groups=groups[0]).annotate(total_rating=Sum("ratings__rating")).order_by("-total_rating")
    games = game_table_data(request, sorted_games)
    return render(request, "game_groups/group.html", {"group": groups[0], "other_users": other_users, "games": games})

@login_required(login_url=login)
def add_to_group(request, id):
    if request.method != "POST":
        return redirect(home)
    groups = Group.objects.filter(id=id)
    if len(groups) < 1:
        return redirect(home)
    if "username" not in request.POST:
        return redirect(group, id=groups[0].id)
    users = User.objects.filter(username=request.POST["username"])
    if groups[0].owner != request.user or len(users) < 1:
        return redirect(group, id=groups[0].id)
    groups[0].members.add(users[0])
    return redirect(group, id=groups[0].id)

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
        messages.error(request, "No results found")
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
    if request.method == "GET":
        return render(request, "game_groups/collection.html")
    elif request.method == "POST":
        choices = request.POST.getlist("game_choices")
        for bgg_id in choices:
            game, created = Game.objects.get_or_create(bgg_id=bgg_id)
            game.owners.add(request.user)
        return redirect(home)

@login_required(login_url=login)
def remove_from_group(request, id, username):
    groups = Group.objects.filter(id=id)
    users = User.objects.filter(username=username)
    if len(groups) == 0 or len(users) == 0 or groups[0].owner != request.user:
        return redirect(home)
    groups[0].members.remove(users[0])
    return redirect(group, id=id)