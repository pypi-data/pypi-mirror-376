
from DenoEngine import Game, Cube, HUDText

player=Cube(pos=[0,0,0],size=1,color=(0,1,0))
enemy=Cube(pos=[2,0,2],size=1,color=(1,0,0))

def update():
    player.draw()
    enemy.draw()

def overlay():
    HUDText("Sağlık: 100",10,550).draw()

game=Game(width=800,height=600,camera_mode="FPS")
game.run(update_fn=update,overlay_fn=overlay)
