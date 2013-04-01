from cocos.director import director
from cocos.layer import *
from cocos.scene import Scene
from cocos.scenes.transitions import *
from cocos.actions import *
from cocos.sprite import *
from cocos.menu import *
from cocos.text import *
import cocos

import pyglet
from pyglet.window import key

from controladores import soundex
from controladores import hiscore
from vistas import escenas
from vistas.capas import CapaNivelScrolling

class TitleLayer(Layer):
    def __init__(self):
        super(TitleLayer, self).__init__()

        w, h = director.get_window_size()
        self.font_title = {}

        self.font_title['font_name'] = 'Edit Undo Line BRK'
        self.font_title['font_size'] = 26
        #        self.font_title['color'] = (204,164,164,255)
        self.font_title['color'] = (255, 204, 204, 255)
        self.font_title['anchor_y'] = 'top'
        self.font_title['anchor_x'] = 'right'
        title = Label('Doke.', **self.font_title)
        title.position = (w - 10, 30)
        self.add(title, z=1)


class ScoresLayer(ColorLayer):
    FONT_SIZE = 22

    is_event_handler = True 

    def __init__(self):
        w, h = director.get_window_size()
        super(ScoresLayer, self).__init__(32, 32, 32, 16, width=w, height=h - 97)

        self.font_title = {}

        self.font_title['font_name'] = 'Edit Undo Line BRK'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (255, 255, 255, 255)
        self.font_title['anchor_y'] = 'top'
        self.font_title['anchor_x'] = 'center'

        title = Label('Puntajes', **self.font_title)

        title.position = (w / 2.0, h - 5)

        self.add(title, z=1)

        self.table = None

    def on_enter( self ):
        super(ScoresLayer, self).on_enter()

        scores = hiscore.hiscore.get()
        if self.table:
            self.remove_old()

        self.table = []
        for idx, s in enumerate(scores):
            pos = Label('%d:' % (idx + 1), font_name='Edit Undo Line BRK',
                font_size=self.FONT_SIZE,
                anchor_y='top',
                anchor_x='left',
                color=(255, 255, 255, 255))

            name = Label(s[1], font_name='Edit Undo Line BRK',
                font_size=self.FONT_SIZE,
                anchor_y='top',
                anchor_x='left',
                color=(255, 255, 255, 255))

            score = Label(str(s[0]), font_name='Edit Undo Line BRK',
                font_size=self.FONT_SIZE,
                anchor_y='top',
                anchor_x='right',
                color=(255, 255, 255, 255))

            self.table.append((pos, name, score))

        self.process_table()

    def remove_old( self ):
        for item in self.table:
            pos, name, score = item
            self.remove(pos)
            self.remove(name)
            self.remove(score)
        self.table = None

    def process_table( self ):
        w, h = director.get_window_size()

        for idx, item in enumerate(self.table):
            pos, name, score = item

            posy = h - 100 - ( (self.FONT_SIZE + 15) * idx )

            pos.position = ( 45, posy)
            name.position = ( 78, posy)
            score.position = ( w - 90, posy )

            self.add(pos, z=2)
            self.add(name, z=2)
            self.add(score, z=2)

    def on_key_press( self, k, m ):
        if k in (key.ENTER, key.ESCAPE, key.SPACE):
            self.parent.switch_to(0)
            return True

    def on_mouse_release( self, x, y, b, m ):
        self.parent.switch_to(0)
        return True


class OptionsMenu(Menu):
    def __init__(self):
        super(OptionsMenu, self).__init__('Opciones')
        self.select_sound = soundex.load('move.mp3')

        self.font_title['font_name'] = 'Edit Undo Line BRK'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (255, 255, 255, 255)

        self.font_item['font_name'] = 'Edit Undo Line BRK',
        self.font_item['color'] = (32, 16, 32, 255)
        self.font_item['font_size'] = 32
        self.font_item_selected['font_name'] = 'Edit Undo Line BRK'
        self.font_item_selected['color'] = (32, 16, 32, 255)
        self.font_item_selected['font_size'] = 46

        self.menu_anchor_y = CENTER
        self.menu_anchor_x = CENTER

        items = []

        self.volumes = ['Mute', '10', '20', '30', '40', '50', '60', '70', '80', '90', '100']

        items.append(MultipleMenuItem(
            'Volumen SFX: ',
            self.on_sfx_volume,
            self.volumes,
            int(soundex.sound_vol * 10))
        )
        items.append(MultipleMenuItem(
            'Volumen musica: ',
            self.on_music_volume,
            self.volumes,
            int(soundex.music_player.volume * 10))
        )
        items.append(ToggleMenuItem('Mostrar FPS: ', self.on_show_fps, director.show_FPS))
        items.append(MenuItem('Pantalla Completa', self.on_fullscreen))
        items.append(MenuItem('Atras', self.on_quit))
        self.create_menu(items, shake(), shake_back())

    def on_fullscreen( self ):
        director.window.set_fullscreen(not director.window.fullscreen)

    def on_quit( self ):
        self.parent.switch_to(0)

    def on_show_fps( self, value ):
        director.show_FPS = value

    def on_sfx_volume( self, idx ):
        vol = idx / 10.0
        soundex.sound_volume(vol)

    def on_music_volume( self, idx ):
        vol = idx / 10.0
        soundex.music_volume(vol)


class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__('CAMBIANDOMENTES')

        self.select_sound = soundex.load('move.mp3')

        self.font_title['font_name'] = 'Edit Undo Line BRK'
        self.font_title['font_size'] = 52
        self.font_title['color'] = (255, 255, 255, 255)

        self.font_item['font_name'] = 'Edit Undo Line BRK',
        self.font_item['color'] = (32, 16, 32, 255)
        self.font_item['font_size'] = 32
        self.font_item_selected['font_name'] = 'Edit Undo Line BRK'
        self.font_item_selected['color'] = (32, 16, 32, 255)
        self.font_item_selected['font_size'] = 46

        self.menu_anchor_y = CENTER
        self.menu_anchor_x = CENTER

        items = []

        items.append(MenuItem('Nuevo Juego', self.on_new_game))
        items.append(MenuItem('Opciones', self.on_options))
        items.append(MenuItem('Puntajes', self.on_scores))
        items.append(MenuItem('Salir', self.on_quit))

        self.create_menu(items, shake(), shake_back())

    def on_new_game(self):
        cocos.director.director.push(FadeTransition(
            escenas.get_game_scene(), 1.0))

    def on_options( self ):
        self.parent.switch_to(1)

    def on_scores( self ):
        self.parent.switch_to(2)

    def on_quit(self):
        pyglet.app.exit()


def get_menu_scene():
    scene = Scene()
    scene.add(MultiplexLayer(
        MainMenu(),
        OptionsMenu(),
        ScoresLayer(),
    ), z=2)
    scene.add(TitleLayer(), z=2)
    scene.add(CapaNivelScrolling(demo=True), z=1)

    return scene
