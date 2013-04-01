import sys
from os.path import realpath, dirname, join
from modelos import constantes

sys.path.append(realpath(join(dirname(__file__), '..')))
from vistas import menu_scene
import cocos.director
import pyglet

def main():
    pyglet.resource.path.append('recursos')
    pyglet.resource.reindex()
    pyglet.font.add_directory('recursos')
    cocos.director.director.init(800, 400, vsync=True, caption="- CAMBIANDO MENTES -")
    pyglet.clock.set_fps_limit(100)
    cocos.director.director.run(menu_scene.get_menu_scene())