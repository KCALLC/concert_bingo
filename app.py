import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

players = {}  # name -> {board, marked, sid}
boards = {}   # room -> [names]
room = 'concert'

default_phrases = [
    "Man with dreadlocks", "Woman with facial tattoo", "Person wearing a band t-shirt",
    "Group selfie", "Someone crowd surfing", "Spontaneous dance circle",
    "Person with a mohawk", "Fan singing along loudly", "Couple kissing",
    "Person on someone's shoulders", "Unexpected cover song", "Trifecta - ear, mouth and nose piercings",
    "Technical difficulties", "Special guest appearance", "Full Goth Wearer",
    "Person with face paint", "Fan holding a sign", "Couple fighting",
    "Drum solo", "Guitar solo", "Parents with kids", "Chunky-Drunky Person",
    "Someone wearing t-shirt of band that's playing", "Confetti or pyrotechnics", "Clearly unshowered groupie"
]

custom_phrases = []

def generate_board():
    all_phrases = default_phrases + custom_phrases
    phrases = random.sample(all_phrases, 25)
    return [phrases[i:i+5] for i in range(0, 25, 5)]

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    name = data['name']
    join_room(room)

    if name not in players:
        board = generate_board()
        players[name] = {
            'board': board,
            'marked': [],
            'sid': request.sid
        }
        if room not in boards:
            boards[room] = []
        boards[room].append(name)

    emit('player_list', list(boards[room]), room=room)
    emit('board_data', {
        'board': players[name]['board'],
        'marked': players[name]['marked'],
        'name': name
    }, room=request.sid)

@socketio.on('mark_square')
def handle_mark_square(data):
    name = data['name']
    row = data['row']
    col = data['col']
    if name in players:
        if (row, col) not in players[name]['marked']:
            players[name]['marked'].append((row, col))

@socketio.on('view_player')
def handle_view_player(data):
    target = data['target']
    if target in players:
        emit('view_board', {
            'board': players[target]['board'],
            'marked': players[target]['marked'],
            'name': target
        })

@socketio.on('bingo')
def handle_bingo(data):
    name = data['name']
    emit('bingo_winner', {'winner': name}, room=room)

@socketio.on('start_new_game')
def handle_start_new_game():
    for name in players:
        new_board = generate_board()
        players[name]['board'] = new_board
        players[name]['marked'] = []
        emit('board_data', {
            'board': new_board,
            'marked': [],
            'name': name
        }, room=players[name]['sid'])

@socketio.on('reset_game')
def handle_reset_game():
    players.clear()
    boards[room] = []
    emit('reset_client', room=room)
    emit('player_list', [], room=room)

@socketio.on('add_tile')
def handle_add_tile(data):
    new_tile = data['phrase'].strip()
    if new_tile and new_tile not in custom_phrases and new_tile not in default_phrases:
        custom_phrases.append(new_tile)
    handle_reset_game()

if __name__ == '__main__':
    socketio.run(app, debug=True)