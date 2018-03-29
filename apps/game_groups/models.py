# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django import forms

# Create your models here.
class Game(models.Model):
    bgg_id = models.IntegerField()
    owners = models.ManyToManyField(User, related_name="owned_games")
    rated_users = models.ManyToManyField(User, related_name="rated_games", through="Rating")

class Group(models.Model):
    name = models.CharField(max_length=255, default="Unnamed Group")
    owner = models.ForeignKey(User, related_name="owned_groups")
    members = models.ManyToManyField(User, related_name="game_groups")

class Rating(models.Model):
    user = models.ForeignKey(User, related_name="ratings")
    game = models.ForeignKey(Game, related_name="ratings")
    rating = models.IntegerField(default=1)
    RATING_CHOICES = (
        (10, "Definitely!"),
        (1, "Sure"),
        (-1, "I'd Rather Not"),
        (-100, "Absoultely Not!")
    )

class UserRegForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "confirm_password"
        ]
    def clean(self):
        cleaned_data = super(UserRegForm, self).clean()
        pw = cleaned_data.get("password")
        pc = cleaned_data.get("confirm_password")
        if pw != pc:
            raise forms.ValidationError("Password does not match")
        return cleaned_data

class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = [
            "username",
            "password"
        ]