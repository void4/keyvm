import webbrowser
import os
import signal
from time import sleep

def start_visualizer():
    import subprocess
    os.system("fuser -n tcp -k 8001")
    os.setpgrp()
    print("Starting debugger interface")
    subprocess.Popen("redis-server".split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    webbrowser.open("http://localhost:8001")
    subprocess.Popen("python server.py".split())
    sleep(1)


def kill(signal_received, frame):
    os.killpg(0, signal.SIGKILL)
    exit(0)

signal.signal(signal.SIGINT, kill)

