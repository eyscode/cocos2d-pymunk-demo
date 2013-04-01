from copy import copy
import cocos.sprite
import cocos.layer
from cocos.actions import *
import math
import pyglet
from pyglet.gl.gl import glPushMatrix, glPopMatrix
from modelos.gameobjects import Player, BolaDemoledora, Columpio, PlataformaMovil, DisparadorPelotas, Bandera, Objeto, TablaSolido, Hueso
import pymunk as pm

from cocos.euclid import Point2
from modelos import constantes
from modelos.gameobjects import Palanca

from controladores import  soundex, hiscore
from controladores.state import state

import random

pyglet.resource.path = [constantes.RUTA]
pyglet.resource.reindex()

class GameOver(cocos.layer.ColorLayer):
    is_event_handler = True 

    def __init__( self):
        super(GameOver, self).__init__(32, 32, 32, 64)
        w, h = cocos.director.director.get_window_size()
        soundex.play('no.mp3')
        msg = 'GAME OVER'
        label = cocos.text.Label(msg,
            font_name='Edit Undo Line BRK',
            font_size=54,
            anchor_y='center',
            anchor_x='center')
        label.position = ( w / 2.0, h / 2.0 )
        self.add(label)
        angle = 5
        duration = 0.05
        accel = 2
        rot = Accelerate(Rotate(angle, duration // 2), accel)
        rot2 = Accelerate(Rotate(-angle * 2, duration), accel)
        effect = rot + (rot2 + Reverse(rot2)) * 4 + Reverse(rot)

        label.do(Repeat(Delay(5) + effect))

        if hiscore.hiscore.is_in(state.score):
            self.hi_score = True

            label = cocos.text.Label('Escribe tu nombre:',
                font_name='Edit Undo Line BRK',
                font_size=36,
                anchor_y='center',
                anchor_x='center',
                color=(32, 32, 32, 255),
            )
            label.position = ( w / 2.0, h / 2.0 )
            label.position = (w // 2, 130)
            self.add(label)

            self.name = cocos.text.Label('',
                font_name='Edit Undo Line BRK',
                font_size=36,
                anchor_y='center',
                anchor_x='center',
                color=(32, 32, 32, 255),
            )
            self.name.position = (w // 2, 80)
            self.add(self.name)
        else:
            self.hi_score = False
            label = cocos.text.Label("Presione 'R' para jugar otra vez",
                font_name='Edit Undo Line BRK',
                font_size=18,
                anchor_y='center',
                anchor_x='center')
            label.position = ( w / 2.0, 20 )
            self.add(label)

    def on_key_press( self, k, m ):
        if not self.hi_score and (k == pyglet.window.key.ENTER or k == pyglet.window.key.ESCAPE):
            cocos.director.director.pop()
            return True

        if not self.hi_score and (k == pyglet.window.key.R):
            self.parent.remove(self)
            self.parent.get('capa_juego_control').restart_level()
            return True

        if self.hi_score:
            if k == pyglet.window.key.BACKSPACE:
                self.name.element.text = self.name.element.text[0:-1]
                return True
            elif k == pyglet.window.key.ENTER:
                hiscore.hiscore.add(state.score, self.name.element.text)
                cocos.director.director.pop()
                return True
        return False

    def on_text( self, t ):
        if not self.hi_score:
            return False

        if t == '\r':
            return True

        self.name.element.text += t


class ScoreLayer(cocos.layer.Layer):
    def __init__(self):
        w, h = cocos.director.director.get_window_size()
        super(ScoreLayer, self).__init__()

        self.add(cocos.layer.ColorLayer(32, 32, 32, 32, width=w, height=48), z=-1)

        self.position = (0, h - 48)

        self.score = cocos.text.Label('Puntaje: ', font_size=20,
            font_name='Edit Undo Line BRK',
            color=(255, 255, 255, 255),
            anchor_x='left',
            anchor_y='bottom')
        self.score.position = (50, 0)
        self.add(self.score)

        self.metros = cocos.text.Label('Distancia: ', font_size=20,
            font_name='Edit Undo Line BRK',
            color=(255, 255, 255, 255),
            anchor_x='left',
            anchor_y='bottom')

        self.metros.position = (480, 0)
        self.add(self.metros)

    def draw(self):
        super(ScoreLayer, self).draw()
        self.score.element.text = 'Puntaje: %d' % state.score
        self.metros.element.text = 'Distancia: %d m' % state.metros


class MessageLayer(cocos.layer.Layer):
    def show_message( self, msg, callback=None ):
        w, h = cocos.director.director.get_window_size()

        self.msg = cocos.text.Label(msg,
            font_size=42,
            font_name='Edit Undo Line BRK',
            color=(64, 64, 64, 255),
            anchor_y='center',
            anchor_x='center')
        self.msg.position = (w / 2.0, h)

        self.msg2 = cocos.text.Label(msg,
            font_size=42,
            font_name='Edit Undo Line BRK',
            color=(255, 255, 255, 255),
            anchor_y='center',
            anchor_x='center')
        self.msg2.position = (w / 2.0 + 2, h + 2)

        self.add(self.msg, z=1)
        self.add(self.msg2, z=0)

        actions = Accelerate(MoveBy((0, -h / 2.0), duration=0.5)) +\
                  Delay(1) +\
                  Accelerate(MoveBy((0, -h / 2.0), duration=0.5)) +\
                  Hide()

        if callback:
            actions += CallFunc(callback)

        self.msg.do(actions)
        self.msg2.do(actions)


class HUD(cocos.layer.Layer):
    def __init__( self ):
        super(HUD, self).__init__()
        self.add(ScoreLayer())
        self.add(MessageLayer(), name='msg')

    def show_message( self, msg, callback=None ):
        self.get('msg').show_message(msg, callback)


class CapaControl(cocos.layer.Layer):
    is_event_handler = True     

    def __init__(self, model):
        super(CapaControl, self).__init__()
        self.model = model
        self.on_keys = {'direction': set(), 'jumps': set()}
        self.schedule(self.update_keys)
        state.state = state.STATE_PLAY

    def game_over(self):
        if state.state == state.STATE_PLAY and not self.model.demo:
            state.state = state.STATE_OVER
            self.parent.add(GameOver(), z=20)

    def restart_level( self ):
        state.score = 0
        state.metros = 0
        self.parent.remove(self.model)
        self.model = CapaNivelScrolling()
        self.parent.add(self.model)
        state.state = state.STATE_PLAY
        self.on_keys = {'direction': set(), 'jumps': set()}

    def on_key_press(self, key, modifiers):
        if not self.model.demo:
            if key == pyglet.window.key.UP:
                self.on_keys['jumps'].add(key)
                return True
        return False

    def on_key_release(self, key, modifiers):
        if not self.model.demo:
            if key == pyglet.window.key.UP:
                self.model.player.body.velocity.y = min(self.model.player.body.velocity.y,
                    self.model.player.jump_cutoff_velocity)
                try:
                    self.on_keys['jumps'].pop()
                    return True
                except  Exception, ex:
                    pass
        return False

    def update_keys(self, dt):
        if len(self.on_keys['jumps']) and self.model.player.alive:
            if self.model.player.well_grounded or self.model.player.remaining_jumps > 0:
                jump_v = math.sqrt(2.0 * self.model.player.jump_height * abs(self.model.space.gravity.y))
                self.model.player.body.velocity.y = self.model.player.ground_velocity.y + jump_v
            self.model.player.remaining_jumps -= 1
            try:
                self.on_keys['jumps'].pop()
            except  Exception, ex:
                pass


class CapaNivelScrolling(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self, atras=None, mapa=None, mundo=None, centro=(1800, 200), position_player=(50, 150), demo=False):
        super(CapaNivelScrolling, self).__init__()
        self.demo = demo
        self.mapa = mapa
        self.mundo = cocos.sprite.Sprite(mundo) if mundo else cocos.sprite.Sprite('fondo3.png')
        self.mundo_post = None
        self.mundo.position = centro
        self.add(self.mundo, z=0)
        self.player = Player(self, position=position_player)
        self.add(self.player.sprite, z=3)
        self.space = pm.Space()
        self.space.gravity = 0, -900
        self.space.damping = 0.99
        #self.cargar_mapa(self.mapa)
        self.cargar_mapa_alt()
        self.player.add_to_space(self.space)
        self.schedule(self.update)
        self.enemigos = []
        self.palancas = []
        self.obstaculos = []
        self.no_obstaculos = []
        self.banderas = []
        self.huesos = []
        self.atras = atras
        self.limite = 0
        self.a_quitar = []
        soundex.set_music('Sick Ted.mp3')
        soundex.play_music()

        def muerte(space, arbiter):
            if not self.demo and self.player.alive:
                self.obstaculos = list((set(self.obstaculos) - set(self.a_quitar)))
                for o in self.obstaculos:
                    if isinstance(o, DisparadorPelotas):
                        if arbiter.shapes[0] in (self.player.head, self.player.feet) and arbiter.shapes[1] in [
                        slot[2] for slot in o.pelotas]:
                            if not self.player.dog:
                                self.player.matar()
                                self.parent.get('capa_juego_control').game_over()
                            else:
                                self.player.desmontar()
                                self.parent.get('hud').show_message("Auuuu!")
                        elif arbiter.shapes[1] in (self.player.head, self.player.feet) and arbiter.shapes[0] in [
                        slot[2] for slot in o.pelotas]:
                            if not self.player.dog:
                                self.player.matar()
                                self.parent.get('capa_juego_control').game_over()
                            else:
                                self.player.desmontar()
                                self.parent.get('hud').show_message("Auuuu!")
                if arbiter.shapes[0] in (self.player.head, self.player.feet) and arbiter.shapes[1] in [
                slot.shape for slot in self.obstaculos]:
                    for slot in self.obstaculos:
                        if slot.shape == arbiter.shapes[1]:
                            if not self.player.dog:
                                self.player.matar()
                                self.parent.get('capa_juego_control').game_over()
                            else:
                                self.player.desmontar()
                                self.a_quitar.append(slot)
                                self.parent.get('hud').show_message("Auuuu!")
                                break
                elif arbiter.shapes[1] in (self.player.head, self.player.head2, self.player.feet) and arbiter.shapes[
                                                                                                      0] in [
                     slot.shape for slot in self.obstaculos]:
                    for slot in self.obstaculos:
                        if slot.shape == arbiter.shapes[1]:
                            if not self.player.dog:
                                self.player.matar()
                                self.parent.get('capa_juego_control').game_over()
                            else:
                                self.player.desmontar()
                                self.a_quitar.append(slot)
                                self.parent.get('hud').show_message("Auuuu!")
                                break
            return True

        def recoger_bandera(space, arbiter):
            if arbiter.shapes[0] in (self.player.head, self.player.feet) and arbiter.shapes[1] in [b.shape for b in
                                                                                                   self.banderas]:
                for b in self.banderas:
                    if b.shape == arbiter.shapes[1] and not b.recogida:
                        b.recoger()
                        state.score += 1
            return False

        def recoger_hueso(space, arbiter):
            if arbiter.shapes[0] in (self.player.head, self.player.feet) and arbiter.shapes[1] in [b.shape for b in
                                                                                                   self.huesos]:
                for b in self.huesos:
                    if b.shape == arbiter.shapes[1] and not self.player.dog:
                        self.parent.get('hud').show_message("Arre gringa!")
                        self.player.montar()
                        self.remove(b.sprite)
                        del b
                        break
            return False


        self.space.add_collision_handler(2, 1, begin=muerte)
        self.space.add_collision_handler(2, 3, begin=recoger_bandera)
        self.space.add_collision_handler(1, 3, begin=lambda space, arbiter: False)
        self.space.add_collision_handler(1, 5, begin=lambda space, arbiter: False)
        self.space.add_collision_handler(2, 5, begin=recoger_hueso)

    def cargar_mapa(self, mapa):
        from os.path import join

        if mapa:
            nombreFile = join(join(constantes.RUTA, 'mapas'), mapa)
        else:
            nombreFile = join(join(constantes.RUTA, 'mapas'), 'mapa.land')
        fil = open(nombreFile, 'r')
        static_pisos = eval(fil.read())
        for static in static_pisos:
            static.friction = 0.5
            static.collision_type = 2
            self.space.add(static)
        del static_pisos

    def cargar_mapa_alt(self):
        lista = []
        b = 30
        subida = True
        contador = 0
        aumento = {0: 100, 1: 150, 2: 100, 3: 150, 4: 100}
        a = 0
        while a < 500000:
            if (b == 50 and subida) or (b == 10 and not subida):
                lista.append(pm.Segment(self.space.static_body, (a, b), (a + aumento[contador], b), 10))
                subida = False if b == 50 else True
            elif subida:
                lista.append(pm.Segment(self.space.static_body, (a, b), (a + aumento[contador], b + 10), 10))
                subida = True
                b += 10
            else:
                lista.append(pm.Segment(self.space.static_body, (a, b), (a + aumento[contador], b - 10), 10))
                subida = False
                b -= 10
            a += aumento[contador]
            contador += 1
            if contador == 5: contador = 0
        for static in lista:
            static.friction = 0.5
            static.collision_type = 4
            self.space.add(static)
        del lista

    def cargar_obstaculos(self):
        if self.demo and self.player.position[0] > self.limite:
            self.agregar_bola_demoledora((600, 100), radio=30, impulso=300000)
            self.agregar_plataforma_movil((1000, 200), [(1000, 200), (1200, 130), (1400, 300)])
            self.agregar_columpio((2300, 200))
            self.agregar_columpio((2000, 100))
            self.agregar_columpio((1700, 200), obstaculo=True)
            self.agregar_disparador_pelotas((1100, 400))
            self.agregar_bola_demoledora((2600, 90), radio=25, impulso=300000)
            self.agregar_bola_demoledora((2600, 190), radio=25, impulso=-200000)
            self.agregar_bola_demoledora((3000, 190), radio=25, impulso=-200000)
            self.agregar_bola_demoledora((3200, 90), radio=25, impulso=200000)
            self.agregar_columpio((4000, 150), obstaculo=True)
            self.agregar_bandera((2100, 100))
            self.limite = 40000000
        elif self.player.position[0] > self.limite - 400:
            if self.limite == 0:
                self.agregar_hueso((1000, 100))
                self.limite += 3600
                for i in range(1):
                    for j in range(4):
                        self.agregar_bandera((1490 + i * 50, 160 + j * 40))
                for i in range(2):
                    for j in range(2):
                        self.agregar_bandera((900 + i * 50, 250 + j * 40))
                self.agregar_bandera((300, 100))
                self.agregar_bandera((340, 150))
                self.agregar_bandera((380, 250))
                self.agregar_columpio((700, 100), impulso=-20000)
                self.agregar_bola_demoledora((950, 200), 20, 500, 300000)
                self.agregar_bola_demoledora((1500, 100), 30, 500, -300000)
                self.agregar_columpio((2000, 150), obstaculo=True, impulso=50000)
                self.agregar_bandera((2000, 250))
                self.agregar_bandera((1950, 100))
                self.agregar_bandera((2050, 100))
                self.agregar_columpio((2400, 350), obstaculo=True, impulso=-50000)
                self.agregar_bola_demoledora((3100, 250), 25, 500, -300000)
                self.agregar_tabla_solido((3300, 200), 80)
                self.agregar_bandera((range(1000, 3600, 100)[random.randint(0, 20)], 100))
                self.agregar_bandera((range(1000, 3600, 100)[random.randint(0, 20)], 100))
                self.agregar_bandera((range(1000, 3600, 100)[random.randint(0, 20)], 100))
                for i in range(3):
                    for j in range(1):
                        self.agregar_bandera((2600 + i * 50, 150 + j * 40))
                for i in range(2):
                    for j in range(1):
                        self.agregar_bandera((3000 + i * 50, 150 + j * 40))
            else:
                self.generar_cuerpos_random()
                self.limite += 3600

    def generar_cuerpos_random(self):
        self.agregar_hueso((self.limite + 1000, 100))
        self.agregar_bola_demoledora((self.limite + 200, 200), 20, 500, -200000)
        self.agregar_bola_demoledora((self.limite + 200, 100), 30, 500, -300000)
        x = random.randint(800, 900)
        y = random.randint(50, 100)
        self.agregar_disparador_pelotas((self.limite + 800, 400))
        self.agregar_tabla_solido((self.limite + x, y), -30)
        self.agregar_bandera((self.limite + 850, 200))
        self.agregar_bandera((self.limite + 1250, 150 ))
        self.agregar_bandera((self.limite + 1250, 150 ))
        if random.randint(0, 2) == 1:
            x = random.randint(1200, 1500)
            self.agregar_bola_demoledora((self.limite + x, 90), 25, 500, 300000)
        else:
            x = random.randint(1200, 1500)
            self.agregar_columpio((self.limite + x, 350), obstaculo=True, impulso=-50000)
        for i in range(3):
            for j in range(1):
                self.agregar_bandera((self.limite + 1600 + i * 50, 150 + j * 40))

        if random.randint(0, 1) == 1:
            posicion_x = random.randint(2100, 2200)
            posicion_y = random.randint(100, 200)
            radio = random.randint(20, 40)
            self.agregar_bola_demoledora((self.limite + posicion_x, posicion_y), radio, 500, 300000)
        else:
            posicion_x = random.randint(2100, 2200)
            posicion_y = random.randint(120, 200)
            self.agregar_columpio((self.limite + posicion_x, posicion_y))
        posicion_x = random.randint(2400, 2500)
        self.agregar_bandera((self.limite + posicion_x, 260))
        self.agregar_bandera((self.limite + posicion_x, 290))
        self.agregar_bandera((self.limite + posicion_x, 320))
        self.agregar_plataforma_movil((self.limite + posicion_x, 150),
            [(self.limite + posicion_x, 150), (self.limite + posicion_x, 300)])
        for i in range(3):
            for j in range(1):
                self.agregar_bandera((self.limite + 2800 + i * 50, 150 + j * 40))

        x = random.randint(3200, 3300)
        self.agregar_columpio((self.limite + x, 350), obstaculo=True, impulso=-50000)
        if random.randint(0, 2) == 1:
            x = random.randint(3600, 3700)
            self.agregar_bola_demoledora((self.limite + x, 100), radio=30)
        else:
            x = random.randint(3100, 3300)
            self.agregar_disparador_pelotas((self.limite + x, 400))
    def agregar_objeto(self, posicion_x, tipo):
        Objeto(posicion_x, tipo).agregar_al_juego(self)

    def agregar_tabla_solido(self, posicion, angulo):
        TablaSolido(posicion, angulo).agregar_al_juego(self)

    def agregar_enemigo(self, cls, posicion, name):
        insecto = cls(position=posicion)
        self.enemigos.append(insecto)
        self.add(insecto.sprite, z=10, name=name)
        del insecto

    def agregar_bandera(self, posicion):
        Bandera(posicion).agregar_al_juego(self)

    def agregar_hueso(self, posicion):
        Hueso(posicion).agregar_al_juego(self)

    def agregar_palanca(self, position=None, callback=None, args=None):
        pal = Palanca(position, callback, args)
        self.palancas.append(pal)
        self.add(pal.sprite, z=4)

    def agregar_disparador_pelotas(self, position, impulso=(-2000, 0), loop=False, periodo=0):
        DisparadorPelotas(position, impulso, loop, periodo).agregar_al_juego(self)

    def agregar_bola_demoledora(self, position, radio=50, masa=500, impulso=60000):
        BolaDemoledora(position, radio, masa, impulso).agregar_al_juego(self)

    def agregar_columpio(self, posicion, obstaculo=False, impulso=50000):
        Columpio(posicion, obstaculo, impulso).agregar_al_juego(self)

    def agregar_plataforma_movil(self, posicion, rutas, velocidad=1, obstaculo=False):
        PlataformaMovil(posicion, rutas, velocidad, obstaculo).agregar_al_juego(self)

    def update_viewpoint(self):
        if 400 < self.player.position[0]:
            self.position = self.translate_vewpoint_location(self.player.sprite.position)[0], self.position[1]
        if self.player.position[0] - self.mundo.position[0] > 1300 and not self.mundo_post:
            self.mundo_post = cocos.sprite.Sprite('fondo4.png') if random.randint(0, 1) else cocos.sprite.Sprite(
                'fondo3.png')
            #self.mundo_post = cocos.sprite.Sprite('fondo3.png')
            self.mundo_post.position = 1800 * (self.mundo.position[0] / 1800 + 2), 200
            self.add(self.mundo_post, z=0)
            self.player.velocity = self.player.velocity + 3 * (self.player.position[0] / 2000)
            for f in self.player.animations['right_walking'].frames:
                f.duration /= 1.1
        if self.player.position[0] - self.mundo.position[0] > 2300 and self.mundo_post:
            self.remove(self.mundo)
            self.mundo = self.mundo_post
            self.mundo_post = None

    def translate_vewpoint_location(self, point):
        centerPoint = cocos.euclid.Point2(400, 200)
        viewPoint = centerPoint - point
        return viewPoint

    def limpiar_obstaculos_tocados(self):
        for slot in self.a_quitar:
            slot.eliminar_del_juego(self)
        self.obstaculos = list(set(self.obstaculos) - set(self.a_quitar))
        del self.a_quitar
        self.a_quitar = []

    def update(self, dt):
        if state.STATE_PLAY:
            self.cargar_obstaculos()
            self.limpiar_obstaculos_tocados()
            if self.demo:
                self.player.ia(self)
            state.metros = self.player.position[0] / 40
            dt = 1.0 / 35.
            self.space.step(dt)
            self.limpiar_memoria(dt)
            for p in self.palancas:
                p.update_object(dt)
            for enemigo in self.enemigos:
                enemigo.update_object(dt)
            self.player.update_object(dt)
            if self.player.alive:
                if self.player.well_grounded:
                    self.player.update_sprite(self.player.direction, constantes.walking)
                else:
                    self.player.update_sprite(self.player.direction, constantes.landing)
                self.player.target_vx += self.player.velocity
            else:
                self.player.update_sprite(constantes.RIGHT, constantes.stoping)
            self.player.feet.surface_velocity = self.player.target_vx, 0
            try:
                if self.player.grounding['body'] is not None:
                    self.player.feet.friction = -self.player.player_ground_accel / self.space.gravity.y
                else:
                    self.player.feet.friction = 0
            except Exception, ex:
                self.player.feet.friction = 0
            self.player.update_object_past(dt)
            self.update_viewpoint()

    def limpiar_memoria(self, dt):
        a_eliminar = []
        for i in range(len(self.obstaculos)):
            ob = self.obstaculos[i]
            ob.update(dt)
            if ob.position[0] + 800 < self.player.body.position[0]:
                ob.eliminar_del_juego(self)
                a_eliminar.append(ob)
        self.obstaculos = list(set(self.obstaculos) - set(a_eliminar))
        a_eliminar = []
        for i in range(len(self.no_obstaculos)):
            ob = self.no_obstaculos[i]
            ob.update(dt)
            if ob.position[0] + 600 < self.player.body.position[0]:
                ob.eliminar_del_juego(self)
                a_eliminar.append(ob)
        self.no_obstaculos = list(set(self.no_obstaculos) - set(a_eliminar))
        a_eliminar = []
        for i in range(len(self.banderas)):
            ob = self.banderas[i]
            if ob.position[0] + 400 < self.player.body.position[0]:
                ob.eliminar_del_juego(self)
                a_eliminar.append(ob)
        self.banderas = list(set(self.banderas) - set(a_eliminar))


class CapaFondo(cocos.layer.Layer):
    def __init__(self, image):
        super(CapaFondo, self).__init__()
        self.img = pyglet.resource.image(image) if image else None

    def agregar_objeto(self, objeto, z=0, nombre=None, posicion=None):
        objeto = cocos.sprite.Sprite(objeto)
        self.add(objeto, z=z, name=nombre)
        if posicion and nombre:
            self.children_names[nombre].position = posicion

    def draw( self ):
        if self.img:
            glPushMatrix()
            self.transform()
            self.img.blit(0, 0)
            glPopMatrix()
