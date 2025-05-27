from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import subprocess
import time
import socket
import json
import threading
import os

video_path = "/Users/jianwei/Downloads/2 3.mp4"
mpv_socket_path = "/tmp/mpvsocket"
player = None
last_master_time = 0
last_received_time = time.time()

def launch_mpv():
    print(f"[mpv] launching fresh")
    return subprocess.Popen([
        "mpv",
        "--fs",
        "--no-terminal",
        "--loop",
        f"--input-ipc-server={mpv_socket_path}",
        video_path
    ])

def get_mpv_time():
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(mpv_socket_path)
        client.send(b'{ "command": ["get_property", "playback-time"] }\n')
        response = client.recv(1024)
        data = json.loads(response.decode("utf-8"))
        return data.get("data", None)
    except Exception as e:
        print(f"[mpv error] {e}")
        return None

def seek_to(t):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(mpv_socket_path)
        cmd = {
            "command": ["seek", t, "absolute"]
        }
        client.send((json.dumps(cmd) + "\n").encode("utf-8"))
        print(f"[mpv] seeking to {t:.2f}s")
    except Exception as e:
        print(f"[seek error] {e}")

def set_time(addr, t):
    global player, last_master_time, last_received_time
    t = float(t)
    last_master_time = t
    last_received_time = time.time()
    if player is None:
        player = launch_mpv()
        time.sleep(0.5)
        seek_to(t)

def sync_check():
    global last_master_time, last_received_time
    while True:
        time.sleep(1)
        if player is None:
            continue
        elapsed = time.time() - last_received_time
        expected_position = last_master_time + elapsed
        actual_position = get_mpv_time()
        if actual_position is not None:
            drift = abs(expected_position - actual_position)
            print(f"[sync] expected: {expected_position:.2f}s, actual: {actual_position:.2f}s, drift: {drift:.2f}s")
            if drift > 0.5:
                seek_to(expected_position)

dispatcher = Dispatcher()
dispatcher.map("/time", set_time)

threading.Thread(target=sync_check, daemon=True).start()

server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 5005), dispatcher)
print("Client: Listening for OSC timecode...")
server.serve_forever()
