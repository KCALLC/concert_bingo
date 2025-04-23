import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

players = {}  # Maps player name to board and room
boards = {}   # Maps room to list of players

bingo_phrases = [
    "Man with dreadlocks", "Woman with facial tattoo", "Person wearing a band t-shirt",
    "Group selfie", "Someone crowd surfing", "Spontaneous dance circle",
    "Person with a mohawk", "Fan singing along loudly", "Couple kissing",
    "Person on someone's shoulders", "Unexpected cover song", "Trifecta - ear, mouth and nose piercings","Technical difficulties", "Special guest appearance", "Full Goth Wearer",
    "Person with face paint", "Fan holding a sign", "Couple fighting",
    "Drum solo", "Guitar solo", "Parents with kids", "Chunky-Drunky Person", "Someone wearing t-shirt of band that's playing",
    "Confetti or pyrotechnics", "Clearly unshowered groupie"
]

def generate_board():
    phrases = random.sample(bingo_phrases, 25)
    return [phrases[i:i+5] for i in range(0, 25, 5)]

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    name = data['name']
    room = 'concert'
    join_room(room)

    if name not in players:
        board = generate_board()
        players[name] = {'board': board, 'name': name}
        if room not in boards:
            boards[room] = []
        boards[room].append(name)

    emit('player_list', list(boards[room]), room=room)
    emit('board_data', {'board': players[name]['board'], 'name': name}, room=request.sid)

@socketio.on('view_player')
def handle_view_player(data):
    target = data['target']
    if target in players:
        emit('view_board', {'board': players[target]['board'], 'name': target})

@socketio.on('bingo')
def handle_bingo(data):
    name = data['name']
    emit('bingo_winner', {'winner': name}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
