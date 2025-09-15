import pygame
import pyttsx3
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import builtins
import tkinter as tk
from PIL import Image
import requests
from tkinter import colorchooser
import turtle as t
import random as ra
from datetime import datetime
import time
import playsound
from pydub import AudioSegment
import os
from PIL import Image, Image
from gtts import gTTS
import os
from pathlib import Path
from gtts import gTTS, lang as gtts_langs
import pygame
import time
from pathlib import Path
import os
from gtts import gTTS, lang as gtts_langs
from pathlib import Path
def get_downloads_dir():
    return Path(os.path.expanduser("~/Downloads"))

now = datetime.now()
hour = now.hour
minute = now.minute
second = now.second
microsecond = now.microsecond
def system(action):
    """action :
            sleep
            shut_down
            log_out
            restart
            """
    if action == "shut_down":
        os.system("shutdown /s /t 0")
    elif action == "restart":
        os.system("shutdown /r /t")
    elif action == "log_out":
        os.system("shutdown -1")
    elif action == "sleep":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
def save_var(local_or_name, value):
    with open (local_or_name, "w") as f:
        f.write(str(value))
def load_var(local_or_name, default=None):
    try:
        with open(local_or_name, "r") as f:
            data = f.read().strip()
            if data == "":
                return default
            return data
    except FileNotFoundError:
        return default
def ri (a, b):
    return ra.randint(a, b)
def key (a, b):
    t.listen()
    t.onkeypress(a, b)
def click(a):
    t.onscreenclick(a)
def getcolor(tit):
    return colorchooser.askcolor(title = tit)
def rc (a):
    return ra.choice(a)

def leftclick (a):
    t.onscreenclick(a, btn = 1)
def middleclick (a):
    t.onscreenclick(a, btn = 2)
def rightclick (a):
    t.onscreenclick(a, btn = 3)
def move (x, y):
    t.goto(x, y)
def randcolor():
    t.colormode(255)
    r = ra.randint(1, 255)
    g = ra.randint(1, 255)
    b = ra.randint(1, 255)
    t.color ((r, g, b))
def rgbcolor(r, g, b):
    t.colormode(255)
    t.color ((r, g, b))
def getping(url):
    start = time.time()
    requests.get(url)
    end = time.time()
    return round((end - start)* 1000)
def mouseX ():
    screen = t.Screen()
    return screen.cv.winfo_pointerx() - screen.cv.winfo_rootx() - screen.window_width() // 2
def mouseY():
    screen = t.Screen()
    return screen.window_height() // 2 - (screen.cv.winfo_pointery() - screen.cv.winfo_rooty())
def hidecursor():
    root = tk.Tk()
    root.config(cursor = "none")
    root.mainloop()
def shapecursor(a):
    root = tk.Tk()
    root.config (cursor = a)
    root.mainloop()
def convert_jpg(your_format, your_picture_name, your_image_path_or_name):
    img = Image.open(your_image_path_or_name)
    img.save(f"{your_picture_name}.{your_format}")
def upload_gif(NameOrPath, sizeWidth, sizeHight):
    screen = t.Screen()
    screen.register_shape(NameOrPath)
    img = Image.open(NameOrPath)
    img = img.resize((sizeWidth, sizeHight))
    img_turtle = t.Turtle()
    img_turtle.shape(NameOrPath)
    img_turtle.penup()
    img_turtle.goto(0, 0)
    return img_turtle
def show_picture():
    img_turtle.showturtle()
def hide_picture():
    img_turtle.hideturtle()

def play_mp3(path):
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def text_to_speech(txt, language, yourMP3name):
    downloads = get_downloads_dir()
    downloads.mkdir(parents=True, exist_ok=True)
    filename = downloads / f"{yourMP3name}.mp3"

    tts = gTTS(text=txt, lang=language)
    tts.save(str(filename))

    pygame.mixer.init()
    pygame.mixer.music.load(str(filename))
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def get_downloads_dir():
    return Path(os.path.expanduser("~/Downloads"))

def get_downloads_dir():
    return Path(os.path.expanduser("~/Downloads"))

def get_unique_filename(base_name="voice", ext=".mp3", folder=None):
    folder = folder or get_downloads_dir()
    i = 0
    while True:
        filename = folder / f"{base_name}_{i}{ext}"
        if not filename.exists():
            return filename
        i += 1

def speak(text, lang="auto"):
    # تشخیص زبان
    if lang == "auto":
        lang = "fa" if any('\u0600' <= ch <= '\u06FF' for ch in text) else "en"

    # بررسی پشتیبانی gTTS
    supported_langs = gtts_langs.tts_langs()
    if lang not in supported_langs:
        fallback = "ar" if lang == "fa" else "en"
        print(f"[!] زبان '{lang}' توسط gTTS پشتیبانی نمی‌شود. استفاده از جایگزین: '{fallback}'")
        lang = fallback

    # ساخت فایل با نام جديد
    downloads = get_downloads_dir()
    downloads.mkdir(parents=True, exist_ok=True)
    filename = get_unique_filename(base_name="voice", ext=".mp3", folder=downloads)

    tts = gTTS(text=text, lang=lang)
    tts.save(str(filename))
    pygame.mixer.init()
    pygame.mixer.music.load(str(filename))
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
def clock(unit):
    now = datetime.now()
    if unit == "hour":
        return now.hour
    elif unit == "minute":
        return now.minute
    elif unit == "second":
        return now.second
    elif unit == "microsecond":
        return now.microsecond
    else:
        return "Invalid unit"
__all__ = [
    "text_to_speech", "randcolor", "rgbcolor", "upload_gif",
    "save_var", "load_var", "getping", "clock", "mouseX", "mouseY",
    "key", "click", "getcolor", "rc", "ri", "leftclick", "middleclick", "rightclick", "play_mp3", "system"
]
