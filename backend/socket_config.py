from flask_socketio import SocketIO

socket_io = SocketIO()

@socket_io.on("client_connected")
def connect_test():
  print("SocketIO connected")