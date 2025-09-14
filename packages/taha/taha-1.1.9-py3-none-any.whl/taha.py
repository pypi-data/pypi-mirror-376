import builtins
from .core import save_var, load_var, ri, key, click, getcolor, rc, leftclick, middleclick, rightclick, move, randcolor, rgbcolor, getping, mouseX, mouseY, hidecursor, shapecursor, convert_jpg, upload_gif, show_picture, hide_picture, text_to_speech
import pygame
import time
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

now = datetime.now()
hour = now.hour
minute = now.minute
second = now.second
microsecond = now.microsecond
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

def text_to_speech(txt, language, yourMP3name):
    filename = f"{yourMP3name}.mp3"
    tts = gTTS(text=txt, lang=language)
    tts.save(filename)

    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


builtins.save_var = save_var
builtins.load_var = load_var
builtins.ri = ri
builtins.key = key
builtins.click = click
builtins.getcolor = getcolor
builtins.leftclick = leftclick
builtins.middleclick = middleclick
builtins.rightclick = rightclick
builtins.move = move
builtins.randcolor = randcolor
builtins.rgbcolor = rgbcolor
builtins.getping = getping
builtins.mouseX = mouseX
builtins.mouseY = mouseY
builtins.hidecursor = hidecursor
builtins.shapecursor = shapecursor
builtins.convert_jpg = convert_jpg
builtins.upload_gif = upload_gif
builtins.show_picture = show_picture
builtins.hide_picture = hide_picture
builtins.text_to_speech = text_to_speech
