# map.py - Sets up the terrain and environment

from ursina import *
import random

def create_map():
    ground = Entity(model='plane', scale=(60, 1, 60), texture='white_cube', texture_scale=(60, 60), color=color.light_gray, collider='box')
    for i in range(10):
        Entity(model='cube', scale=(2,2,2), position=(i*4 - 20,1,random.uniform(-5,5)), color=color.dark_gray, collider='box')

    DirectionalLight(y=3, z=3, shadows=True)
    Sky()
