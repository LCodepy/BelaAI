import os
from _thread import start_new_thread as start

import pyautogui as pyautogui
import win32gui


scr_w, scr_h = pyautogui.size()

path = r"C:\Users\jojog\Desktop\Lovro\BelaAI"
if not os.path.exists(path):
    path = r"C:\Users\SKECPC\Desktop\ROOT\Private[id=0]\Programming[id=0,class=PROG]\Big_projects[type=group]\Python[type=group]\BelaAI"
path = ""

start(os.system, (os.path.join(path, "server_launcher.py"), ))
for i in range(4):
    start(os.system, (os.path.join(path, "client_launcher.py"), ))

while not (win32gui.FindWindow(None, "Bela - Client 0 | Game 0")
           and win32gui.FindWindow(None, "Bela - Client 1 | Game 0")
           and win32gui.FindWindow(None, "Bela - Client 2 | Game 0")
           and win32gui.FindWindow(None, "Bela - Client 3 | Game 0")
           ):
    pass


hwnd1 = win32gui.FindWindow(None, "Bela - Client 0 | Game 0")
hwnd2 = win32gui.FindWindow(None, "Bela - Client 1 | Game 0")
hwnd3 = win32gui.FindWindow(None, "Bela - Client 2 | Game 0")
hwnd4 = win32gui.FindWindow(None, "Bela - Client 3 | Game 0")

_, _, w, h = win32gui.GetWindowRect(hwnd1)

win32gui.MoveWindow(hwnd1, -scr_w, 0, w, h, 0)
win32gui.MoveWindow(hwnd2, -scr_w, h//2, w, h, 0)
win32gui.MoveWindow(hwnd3, -scr_w+w//2+200, h//2, w, h, 0)
win32gui.MoveWindow(hwnd4, -scr_w+w//2+200, 0, w, h, 0)
