"""x:0, y:0 is generally bottom right"""
from time import sleep
from machine import Pin, SPI, ADC
from xglcd_font import XglcdFont
from ssd1309 import Display
from life import Life
from util import Util
import json
import math


#left -14x22
#right -15x22
#front -16x23
#back -16x21
pot = ADC(Pin(26))
def _map(v, fmin=25, fmax=255, tmin=1, tmax=100):
    return (v - fmin) * (tmax - tmin) // (fmax - fmin) + tmin



W = 128
H = 64
font = XglcdFont('Wendy7x8.c', 7, 8)

spi = SPI(0, baudrate=10000000, sck=Pin(18), mosi=Pin(19))
d1 = Display(spi, dc=Pin(16), cs=Pin(17), rst=Pin(20))


spi2 = SPI(1, baudrate=10000000, sck=Pin(10), mosi=Pin(11))
d2 = Display(spi2, dc=Pin(12), cs=Pin(13), rst=Pin(2))
util = Util()

# when x at 0 is right side of screen == text end position at 0
# x: 128 is left side of screen
# does not erase to just draw screen, can overlay an existing bit map
def draw_text(x, y, text, padding=0, isOne=False):
    text_width = font.measure_text(text)
    if isOne:
        d1.draw_text(text_position_X(x, text_width, padding), y, text, font, False, 180)
    else:
        d2.draw_text(text_position_X(x, text_width, padding), y, text, font, False, 180)

def text_position_X(desiredX, text_w, padding):
    if desiredX < text_w:
        return text_w - desiredX + padding
    else:
        return desiredX - padding

def ui_display(isOne):
    if isOne:
        draw_text(128, 25, "Health: 100", padding=2, isOne=True)
        draw_text(128, 45, "Items: []", padding=2, isOne=True)
        d1.draw_rectangle(0, 0, W, H)
    else:
        d2.draw_rectangle(0, 0, W, H)


def test_life():

    text_width = font.measure_text("All dead!")

    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]
    lifeGens = 29
    life = Life(grid, lifeGens, len(grid), 1, len(grid), len(grid[0]))
    ba, lw, lh = life.show_self(grid)
    d2.draw_bitmap_array_raw(ba, 50, 26, lw, lh)
    # need to draw a bouding box around the life sim
    d2.clear()
    ui_display(True)
    ui_display(False)
    d1.present()
    d2.present()

    for i in range(lifeGens):
        d2.present()
        grid = life.update_grid(grid)
        ba2, live_count = life.show_self(grid, nextGen=True)
        d2.draw_bitmap_array_raw(ba2, 50, 26, lw, lh)
        sleep(.005)
        if live_count <= 0:
            draw_text(128, 35, "All dead!")
            d2.present()
            sleep(2)
            break
    return

def test_movement():

    with open('sprites.json', 'r') as file:
        data = json.load(file)
    left = bytearray(data['player_sprite_left'])
    right = bytearray(data['player_sprite_right'])
    front = bytearray(data['player_sprite_front'])
    back = bytearray(data['player_sprite_back'])
    raw_test = [left, right, front, back]
    # x 0 is right side here..
    x = 2

    d1.present()
    sleep(2)

    for i in range(150):
        # >> 8 -> 65535 to 255
        pot_value = pot.read_u16() >> 8
#        print(f"pot_value: {pot_value}")
        mover = 5
        sprite_arr = raw_test[0]

        # somehow use these to determine if dir change should show front or back profile
        going_left = True
        switched_dir = False
        spriteW = 14

        # this is screen flicker like crazy.. -> clear_buffers is way faster than clear()
        if pot_value > 180:
            mover = 5
            sprite_arr = raw_test[0]
            spriteW = 14
            print("Going left")
        else:
            mover = -5
            sprite_arr = raw_test[1]
            spriteW = 15
            print("Going right")

        d1.draw_bitmap_array_raw(sprite_arr, x, 30, spriteW, 22)

        d1.present()
        x += mover
        d1.clear_buffers()
        sleep(1)
    d1.clear()
    return

def test_better():
    ui_display(True)
    d1.present()
    return

#test_life()
test_movement()
test_better()

sleep(2)
d1.cleanup()
d2.cleanup()
print('Done.')



