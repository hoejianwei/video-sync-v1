from pythonosc.udp_client import SimpleUDPClient
import time
import subprocess
import socket
import json

video_path = "/Users/donottouch/Downloads/1.mp4"
mpv_socket_path = "/tmp/mastersocket"
client_ip = "192.168.50.118" #client IP, not master
client_port = 5005

# Launch mpv
player = subprocess.Popen([
    "/opt/homebrew/bin/mpv",
    "--fs",
    "--no-terminal",
    "--loop",
    f"--input-ipc-server={mpv_socket_path}",
    video_path
])

# OSC client
client = SimpleUDPClient(client_ip, client_port)

def get_mpv_time():
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(mpv_socket_path)
        s.send(b'{ "command": ["get_property", "playback-time"] }\n')
        response = s.recv(1024)
        data = json.loads(response.decode("utf-8"))
        return data.get("data", None)
    except Exception as e:
        print(f"[master mpv error] {e}")
        return None

# Send real video time
while True:
    current_time = get_mpv_time()
    if current_time is not None:
        client.send_message("/time", current_time)
    time.sleep(0.05)
