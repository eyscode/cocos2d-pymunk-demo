from pyglet.window.key import RIGHT, LEFT, DOWN, UP
from os.path import realpath, join, dirname

stoping = '_stoping'
walking = '_walking'
landing = '_landing'
jumping = '_jumping'
atacking = '_atacking'
dying = '_dying'
dying_cut = '_dying_cut'
dying_fire = '_dying_fire'
dying_normal = '_dying_normal'
getingup = '_getingup'
goingtobed = '_goingtobed'

traduction_direction = {RIGHT: 'right', LEFT: 'left', DOWN: 'down', UP: 'up'}

ORIENTACIONES = {0: 'l t r d', 90: 't r d l', 180: 'r d l t', 270: 'd l t r'}

RUTA = realpath(join(realpath(join(dirname(__file__), '..')), 'recursos'))
MUSIC, SOUND = True, True