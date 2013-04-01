import cocos.sprite
from cocos.actions import RotateBy
import pyglet
import pymunk as pm
from modelos import constantes
from controladores.utilitarios import *
from controladores import soundex
from os.path import join
import math
import random

class Player(object):
    def __init__(self, layer_mundo, position=None, direction=constantes.RIGHT):
        self.mundo = layer_mundo
        self.direction = direction
        self.state = constantes.walking
        self.velocity = 200.
        self.player_air_accel_time = 0.50
        self.player_air_accel = self.velocity / self.player_air_accel_time
        self.jump_height = 40. * 3
        self.jump_cutoff_velocity = 100
        self.player_ground_accel_time = 0.05
        self.player_ground_accel = (self.velocity / self.player_ground_accel_time)
        self.fall_velocity = 250.
        #Animacion de imagen del personaje
        sheet = pyglet.image.load(join(constantes.RUTA, 'xmasgirl1.png'))
        sequence = pyglet.image.ImageGrid(sheet, 2, 4)
        self.animations = dict()
        self.animations['right_walking_human'] = pyglet.image.Animation.from_image_sequence(sequence[0:4], period=0.1)
        self.animations['right_landing_human'] = pyglet.image.Animation.from_image_sequence([sequence[1]], period=1)
        self.animations['right_stoping'] = pyglet.image.Animation.from_image_sequence([sequence[0]], period=1)
        self.animations['right_walking'] = self.animations['right_walking_human']
        self.animations['right_landing'] = self.animations['right_landing_human']
        sheet = pyglet.image.load(join(constantes.RUTA, 'xmasgirl2.png'))
        sequence = pyglet.image.ImageGrid(sheet, 1, 2)
        self.animations['right_walking_dog'] = pyglet.image.Animation.from_image_sequence(sequence[0:2], period=0.05)
        self.animations['right_landing_dog'] = pyglet.image.Animation.from_image_sequence([sequence[0]], period=0.05)
        del sheet, sequence
        self.position = position if position else (300, 400)
        self.sprite = cocos.sprite.Sprite(
            self.animations[constantes.traduction_direction[self.direction] + self.state])
        self.sprite.position = self.position
        self.body = pm.Body(10, pm.inf)
        self.body.position = self.position
        self.feet = pm.Circle(self.body, 20, (0, -6))
        self.head = pm.Circle(self.body, 20, (0, 13))
        self.head2 = pm.Circle(self.body, 20, (0, 26))
        self.feet.collision_type = 2
        self.head.collision_type = 2
        self.target_vx = 0
        self.ground_velocity = pm.vec2d.Vec2d.zero()
        self.well_grounded = True
        self.remaining_jumps = 2
        self.grounding = {
            'normal': pm.vec2d.Vec2d.zero(),
            'penetration': pm.vec2d.Vec2d.zero(),
            'impulse': pm.vec2d.Vec2d.zero(),
            'position': pm.vec2d.Vec2d.zero(),
            'body': None
        }
        self.alive = True
        self.dog = False

    def matar(self):
        self.alive = False

    def cerca(self, enemigo):
        if abs(self.position[1] - enemigo.position[1]) < 150:
            if self.position[0] < enemigo.position[0] and enemigo.position[0] - self.position[0] < 200:
                return constantes.LEFT
            elif self.position[0] > enemigo.position[0] and self.position[0] - enemigo.position[0] < 200:
                return constantes.RIGHT
        return None

    def montar(self):
        self.animations['right_walking'] = self.animations['right_walking_dog']
        self.animations['right_landing'] = self.animations['right_landing_dog']
        self.velocity *= 1.2
        self.dog = True
        soundex.play('ladrido.wav')

    def desmontar(self):
        self.animations['right_walking'] = self.animations['right_walking_human']
        self.animations['right_landing'] = self.animations['right_landing_human']
        self.velocity /= 1.2
        self.dog = False
        soundex.play('ladrido.wav')

    def add_to_space(self, space):
        space.add(self.body, self.feet, self.head)

    def update_sprite(self, direction, state):
        if direction is self.direction and state is self.state: return
        self.direction = direction
        self.state = state
        self.sprite.image = self.animations[constantes.traduction_direction[self.direction] + self.state]
        self.sprite.position = self.position

    def corregir_stados(self):
        if self.alive:
            self.well_grounded = True
            if self.state == constantes.walking or self.state == constantes.stoping:
                return
            self.update_sprite(self.direction, constantes.walking)

    def update_object(self, dt):
        self.grounding = {
            'normal': pm.vec2d.Vec2d.zero(),
            'penetration': pm.vec2d.Vec2d.zero(),
            'impulse': pm.vec2d.Vec2d.zero(),
            'position': pm.vec2d.Vec2d.zero(),
            'body': None
        }

        def f(arbiter):
            n = -arbiter.contacts[0].normal
            if n.y > self.grounding['normal'].y:
                self.corregir_stados()
                self.grounding['normal'] = n
                self.grounding['penetration'] = -arbiter.contacts[0].distance
                self.grounding['body'] = arbiter.shapes[1].body
                self.grounding['impulse'] = arbiter.total_impulse
                self.grounding['position'] = arbiter.contacts[0].position

        self.well_grounded = False
        self.body.each_arbiter(f)
        try:
            if self.grounding['body'] is not None and abs(
                self.grounding['normal'].x / self.grounding['normal'].y) < self.feet.friction:
                self.well_grounded = True
                self.remaining_jumps = 2
            else:
                pass
        except Exception, ex:
            print "una division entre cero se evito"
        self.ground_velocity = pm.vec2d.Vec2d.zero()

        if self.well_grounded:
            self.ground_velocity = self.grounding['body'].velocity
        self.target_vx = 0

    def update_object_past(self, dt):
        if not self.alive:
            self.update_sprite(constantes.RIGHT, constantes.stoping)
        if self.grounding['body'] is None:
            self.body.velocity.x = cpflerpconst(self.body.velocity.x, self.target_vx + self.ground_velocity.x,
                self.player_air_accel * dt)
            self.well_grounded = False
        self.body.velocity.y = max(self.body.velocity.y, -self.fall_velocity) # clamp upwards as well?
        self.sprite.position = self.body.position
        self.position = self.sprite.position

    def ia(self, nivel):
        pass


class Palanca(object):
    def __init__(self, position, callback, args):
        self.sprite = cocos.sprite.Sprite('palanca.png')
        self.state = constantes.LEFT
        self.sprite.position = position
        self.callback = callback if callback else None
        self.llamar = False
        self.args = args

    def mover_palanca(self):
        #self.state = constantes.RIGHT if self.state == constantes.LEFT else constantes.LEFT
        if self.state == constantes.LEFT:
            self.state = constantes.RIGHT
            self.sprite.actions = []
            self.sprite.do(RotateBy(90, 1))
            self.llamar = True

    def update_object(self, dt):
        if not self.sprite.actions and self.llamar:
            self.callback(*self.args)
            self.llamar = False


class BolaDemoledora(object):
    def __init__(self, posicion, radio=50, masa=500, impulso=6000):
        momento = pm.moment_for_circle(masa, 0, radio, (0, 0))
        self.body = pm.Body(masa, momento)
        self.body.position = posicion
        self.body.apply_impulse((impulso, 0))
        self.sprite = cocos.sprite.Sprite('bola.png')
        self.sprite.scale = radio / 50.
        self.sprite.position = posicion
        self.shape = pm.Circle(self.body, radio)
        self.shape.elasticity = 0.99
        self.shape.collision_type = 1
        self.pinjoint = pm.PinJoint(pm.Body(), self.body, (posicion[0], 400), (0, 0))
        self.sprite_cuerda = cocos.sprite.Sprite('cuerda.png')
        self.sprite_cuerda.scale = (400 - posicion[1]) / 310.
        self.sprite_cuerda.position = posicion[0], 400
        self.position = self.body.position

    def agregar_al_juego(self, nivel):
        nivel.space.add(self.body, self.shape, self.pinjoint)
        nivel.add(self.sprite_cuerda, z=1)
        nivel.add(self.sprite, z=2)
        nivel.obstaculos.append(self)

    def eliminar_del_juego(self, nivel):
        nivel.space.remove(self.body, self.shape, self.pinjoint)
        nivel.remove(self.sprite)
        nivel.remove(self.sprite_cuerda)

    def update(self, dt):
        self.sprite.position = self.body.position
        tg = (self.sprite_cuerda.position[1] - self.sprite.position[1]) / (
            self.sprite_cuerda.position[0] - self.sprite.position[0])
        rotacion = 90 - math.atan(tg) * 180 / math.pi
        self.sprite_cuerda.rotation = rotacion if rotacion < 90 else -(180 - rotacion)
        self.position = self.body.position


class Columpio(object):
    def __init__(self, posicion, obstaculo=False, impulso=50000):
        self.body = pm.Body(10, 10000)
        self.body.position = posicion
        self.body.apply_impulse((0, impulso), r=(-0.5, 0))
        self.shape = pm.Poly.create_box(self.body, (200, 10))
        self.shape.friction = 0.9
        self.shape.collision_type = 1
        self.body_centro_rotacion = pm.Body()
        self.body_centro_rotacion.position = posicion
        self.pivotjoint = pm.PivotJoint(self.body, self.body_centro_rotacion, (0, 0), (0, 0))
        self.obstaculo = obstaculo
        self.sprite = cocos.sprite.Sprite('tabla2.png') if self.obstaculo else cocos.sprite.Sprite('tabla.png')
        self.sprite.position = posicion
        self.position = self.body.position

    def agregar_al_juego(self, nivel):
        nivel.space.add(self.body, self.shape, self.pivotjoint)
        nivel.add(self.sprite, z=2)
        if self.obstaculo:
            nivel.obstaculos.append(self)
        else:
            nivel.no_obstaculos.append(self)

    def eliminar_del_juego(self, nivel):
        nivel.space.remove(self.body, self.shape, self.pivotjoint)
        nivel.remove(self.sprite)

    def update(self, dt):
        self.sprite.rotation = 180 - self.body.angle * 180 / math.pi
        self.position = self.body.position


class PlataformaMovil(object):
    def __init__(self, posicion_inicial, ruta, speed=1, obstaculo=False):
        self.obstaculo = obstaculo
        self.speed = speed
        self.rutas = ruta
        self.ruta_index = 0
        self.body = pm.Body(pm.inf, pm.inf)
        self.body.position = posicion_inicial
        self.shape = pm.Segment(self.body, (-80, 0), (80, 0), 10)
        self.sprite = cocos.sprite.Sprite('tabla4.png') if self.obstaculo else cocos.sprite.Sprite('tabla3.png')
        self.sprite.position = posicion_inicial
        self.shape.friction = 1.
        self.shape.collision_type = 1
        self.position = self.body.position

    def agregar_al_juego(self, nivel):
        nivel.space.add(self.shape)
        nivel.add(self.sprite, z=2)
        if self.obstaculo:
            nivel.obstaculos.append(self)
        else:
            nivel.no_obstaculos.append(self)

    def eliminar_del_juego(self, nivel):
        nivel.space.remove(self.shape)
        nivel.remove(self.sprite)

    def update(self, dt):
        destination = self.rutas[self.ruta_index]
        current = pm.Vec2d(self.body.position)
        distance = current.get_distance(destination)
        if distance < self.speed:
            self.ruta_index += 1
            self.ruta_index = self.ruta_index % len(self.rutas)
            t = 1
        else:
            t = self.speed / distance
        new = current.interpolate_to(destination, t)
        self.body.position = new
        self.body.velocity = (new - current) / dt
        self.sprite.position = new
        self.position = self.body.position


class DisparadorPelotas(object):
    def __init__(self, posicion, impulso=(-2000, 0), loop=False, periodo=0):
        self.position = posicion
        self.loop = loop
        self.periodo = periodo
        self.pelotas = []
        self.impulso = impulso
        self.fin = False
        self.shape = None
        self.tiempo = 0

    def agregar_al_juego(self, nivel):
        self.nivel = nivel
        self.nivel.obstaculos.append(self)

    def eliminar_del_juego(self, nivel):
        for i in range(len(self.pelotas)):
            self.nivel.remove(self.pelotas[i][0])
            self.nivel.space.remove(self.pelotas[i][1], self.pelotas[i][2])

    def update(self, dt):
        if abs(self.nivel.player.position[0] - self.position[0]) < 300 and not self.fin:
            mass = 10
            r = 10
            moment = pm.moment_for_circle(mass, 0, r, (0, 0))
            body = pm.Body(mass, moment)
            body.position = self.position
            sprite = cocos.sprite.Sprite('pelota.png')
            sprite.position = self.position
            shape = pm.Circle(body, r, (0, 0))
            self.nivel.space.add(body, shape)
            self.nivel.add(sprite, z=2)
            self.pelotas.append((sprite, body, shape))
            body.apply_impulse(self.impulso, (0, 0))
            shape.collision_type = 1
            shape.friction = 0.5
            if not self.loop: self.fin = True
        for i in range(len(self.pelotas)):
            p = self.pelotas[i]
            p[0].position = p[1].position
            p[0].rotation = int(p[1].angle * 180 / math.pi)


class Bandera(object):
    def __init__(self, posicion):
        self.body = pm.Body()
        self.shape = pm.Poly.create_box(self.body, (40, 20))
        self.sprite = cocos.sprite.Sprite('bandera.png') if random.randint(0, 1) == 1 else cocos.sprite.Sprite(
            'bandera2.png')
        self.blanca = pyglet.resource.image('blanca.png') if random.randint(0, 1) == 1 else pyglet.resource.image(
            'blanca2.png')
        self.body.position = posicion
        self.sprite.position = posicion
        self.shape.collision_type = 3
        self.recogida = False
        self.position = posicion

    def agregar_al_juego(self, nivel):
        nivel.space.add(self.shape)
        nivel.add(self.sprite, z=1)
        nivel.banderas.append(self)

    def eliminar_del_juego(self, nivel):
        nivel.space.remove(self.shape)
        nivel.remove(self.sprite)

    def recoger(self):
        if not self.recogida:
            self.sprite.image = self.blanca
            self.recogida = True
        return False


class Hueso(object):
    def __init__(self, posicion):
        self.body = pm.Body()
        self.shape = pm.Poly.create_box(self.body, (60, 30))
        self.sprite = cocos.sprite.Sprite('hueso.png')
        self.body.position = posicion
        self.sprite.position = posicion
        self.shape.collision_type = 5
        self.position = posicion

    def agregar_al_juego(self, nivel):
        nivel.space.add(self.shape)
        nivel.add(self.sprite, z=1)
        nivel.huesos.append(self)

    def eliminar_del_juego(self, nivel):
        nivel.space.remove(self.shape)
        nivel.remove(self.sprite)


class Objeto(object):
    def __init__(self, posicion_x, tipo="carpeta"):
        self.body = pm.Body()
        posicion_y = 55 if tipo == "carpeta" else 129
        self.body.position = posicion_x, posicion_y
        tamanio = (180, 50) if tipo == "carpeta" else (280, 198)
        self.shape = pm.Poly.create_box(self.body, tamanio)
        self.shape.collision_type = 1
        self.sprite = cocos.sprite.Sprite(tipo + '.png')
        self.sprite.position = posicion_x, posicion_y
        self.position = posicion_x, posicion_y

    def agregar_al_juego(self, nivel):
        nivel.space.add(self.shape)
        nivel.add(self.sprite, z=2)
        nivel.no_obstaculos.append(self)

    def eliminar_del_juego(self, nivel):
        nivel.space.remove(self.shape)
        nivel.remove(self.sprite)

    def update(self, dt):
        pass


class TablaSolido(object):
    def __init__(self, posicion, angulo):
        self.body = pm.Body()
        self.body.position = posicion
        self.shape = pm.Poly.create_box(self.body, (160, 16))
        self.shape.friction = 0
        self.shape.collision_type = 1
        self.sprite = cocos.sprite.Sprite('tabla4.png')
        self.sprite.position = posicion
        self.sprite.rotation = angulo
        self.body.angle = math.pi - angulo * math.pi / 180
        self.position = posicion

    def agregar_al_juego(self, nivel):
        nivel.space.add(self.shape)
        nivel.add(self.sprite, z=2)
        nivel.obstaculos.append(self)

    def eliminar_del_juego(self, nivel):
        nivel.space.remove(self.shape)
        nivel.remove(self.sprite)

    def update(self, dt):
        pass
