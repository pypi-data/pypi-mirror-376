from __init__ import *

def task1():
    move('A',2,10,1)
    light(1,2,5,"red")
    playSound(9,1)

def task2():
    move('B',2,4,1)
    light(2,2,5,"green")
    playSound(3,1)
  
algopython_init()

move('C',4,10,1)
start_task(task1)
start_task(task2)


algopython_exit()




# move(port='A', duration=2.0, power=5, direction=1)
# move(port='AB', duration=1.5, power=8, direction=-1)
# rotations(port='C', rotations=3, power=10, direction=1)
# light(port=1, duration=2.0, power=5, color="red")
# light(port=1, duration=FOREVER, power=7, color="green", is_blocking=False)
# lightStop(1)
# light(port=2, duration=3.0, power=10, color="cyan")
# light(port=1, duration=FOREVER, power=7, color="green", is_blocking=False)
# lightStop(1)
# wait_sensor(sensor_port=1, min=2, max=8)
# move(port='A', duration=2.0, power=5, direction=1)