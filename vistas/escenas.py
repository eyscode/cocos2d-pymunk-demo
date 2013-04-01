import cocos.scene
from controladores.state import state
import capas

def get_game_scene():
    state.reset()
    s = cocos.scene.Scene()
    capa_juego_modelo = capas.CapaNivelScrolling(atras=None, demo=False)
    capa_juego_control = capas.CapaControl(capa_juego_modelo)
    hud = capas.HUD()
    s.add(hud, z=1, name='hud')
    s.add(capa_juego_modelo, z=0, name='capa_juego_modelo')
    s.add(capa_juego_control, z=0, name='capa_juego_control')
    hud.show_message("A cambiar las ideas!")
    return s