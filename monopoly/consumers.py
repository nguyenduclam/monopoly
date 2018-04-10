from channels import Group
from django.core import serializers
from django.contrib.auth.decorators import login_required
from channels.auth import http_session_user, channel_session_user, \
    channel_session_user_from_http
from monopoly.models import Profile
from django.contrib.auth.models import User
from core.game import *

import json
from monopoly.ws_handlers.game_handler import *

# Connected to websocket.connect
# @login_required

rooms = {}
games = {}


def ws_message(message):
    print 'message is: ', message.content


# @login_required
@channel_session_user_from_http
def ws_add(message):
    # Accept the connection
    print 'ws_add invoked'
    message.reply_channel.send({"accept": True})
    mypath = message.content['path']
    print 'path is', mypath
    if 'join' in mypath:
        ws_connect_for_join(message)
    # elif 'start' in mypath:
    #     ws_connect_for_start(message)
    elif 'game' in mypath:
        ws_connect_for_game(message, rooms, games)


@channel_session_user_from_http
def ws_connect_for_join(message):
    print 'now is connecting for join'
    print 'client is', message.user.username
    path = message.content['path']
    # hostname = path[1:-2]
    print 'path is: ', path
    fields = path.split('/')

    hostname = fields[-1]
    print 'hostname is', hostname

    message.reply_channel.send({"accept": "True"})

    # Add to the chat group
    room_name = hostname
    player_name = message.user.username
    print 'user is: ', message.user
    print 'player name: ', player_name
    print 'room name: ', room_name
    add_player(room_name, player_name)
    Group(hostname).add(message.reply_channel)

    # # response_text = serializers.serialize('json', Item.objects.all())
    userlist = []
    Group(hostname).send({
        "text": build_join_reply_msg(room_name)
    })
    print 'join finished'


def ws_message(message):
    msg = json.loads(message.content["text"])
    action = msg["action"]
    path = message.content['path']
    fields = path.split('/')
    hostname = fields[-1]
    print 'action is: ', action
    print 'hostname is: ', hostname

    if action == "start":
        handle_start(hostname)
    if action == "roll":
        handle_roll(hostname, games)
    if action == "confirm_decision":
        handle_confirm_decision(hostname, games)
    if action == "cancel_decision":
        handle_cancel_decision(hostname, games)


# @login_required
def ws_disconnect(message):
    Group('5').discard(message.reply_channel)


def ws_connect_for_start(message):
    print 'now is connecting for start'


def build_start_msg():
    ret = {"action": "start"}
    print json.dumps(ret)
    return json.dumps(ret)


def build_join_reply_msg(room_name):
    # todo profile
    players = rooms[room_name]
    print 'players: ', players
    data = []
    for player in players:
        print 'player is: ', player
        profile_user = User.objects.get(username=player)
        print 'profile user: ', profile_user.username
        try:
            profile = Profile.objects.get(user=profile_user)
        except Exception:
            profile = None
        avatar = profile.avatar.url if profile else ""
        data.append({"id": profile_user.id, "name": player, "avatar": avatar})

    ret = {"action": "join",
           "data": data
           }
    print json.dumps(ret)
    return json.dumps(ret)


def add_player(room_name, player_name):
    if room_name not in rooms:
        rooms[room_name] = set()
        rooms[room_name].add(room_name)
    rooms[room_name].add(player_name)


def handle_start(hostname):
    # init game
    if hostname not in games:
        players = rooms[hostname]
        player_num = len(players)
        games[hostname] = Game(player_num)

    Group(hostname).send({
        "text": build_start_msg()
    })
    print len(games)
    print "start finish"