"""x:0, y:0 is generally bottom right"""
from time import ticks_ms, sleep, ticks_diff
from machine import Pin, SPI, ADC, I2C
from xglcd_font import XglcdFont
from ssd1309 import Display
from life import Life
from util import Util
from eeprom import Eeprom
from player import Player
from projectile import Projectile
import json
import math
import random

#left -14x22
#right -15x22
#front -16x23
#back -16x21

b1 = Pin(5, Pin.IN, Pin.PULL_UP)
b2 = Pin(4, Pin.IN, Pin.PULL_UP)

i2c_memory = I2C(0, scl=Pin(1), sda=Pin(0), freq=50000)


W = 128
H = 64
font_H = 8
'''Create another font, smaller to show enemy lvl values and required kill counts above doors on map?'''
font = XglcdFont('Wendy7x8.c', 7, font_H)

spi = SPI(0, baudrate=10000000, sck=Pin(18), mosi=Pin(19))
d1 = Display(spi, dc=Pin(16), cs=Pin(17), rst=Pin(20))


spi2 = SPI(1, baudrate=10000000, sck=Pin(10), mosi=Pin(11))
d2 = Display(spi2, dc=Pin(12), cs=Pin(13), rst=Pin(2))
util = Util()


'''
MOVE TO xglcdFont
'''
# when x at 0 is right side of screen == text end position at 0
# x: 128 is left side of screen
# does not erase to just draw screen, can overlay an existing bit map
# can take f strings for text
''' Need to return total text height especially for next line wrapping'''
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
'''
'''


def test_ui(player):
    ui_display(player)
    d1.present()
    return

'''Get all text width to normalize the position they are drawn at?
Level:    19
Health:   100
Items:    []
(self, lvl, exp, expReq, hp, attack, defense, speed, mana, money)
'''
def ui_display(player, isOne=True):
    ui_rows = 5
    level = 19

    if isOne:
        draw_text(128, 52, "Makadee", padding=2, isOne=True)
        draw_text(128, 43, f"Mana: {player.mana}", padding=2, isOne=True)
        draw_text(128, 34, f"Health: {player.hp}", padding=2, isOne=True)
        draw_text(128, 25, f"Level: {player.lvl}", padding=2, isOne=True)
        draw_text(128, 16, "Items: []", padding=2, isOne=True)
        draw_text(128, 7, f"Exp: {player.exp}/{player.expReq}", padding=2, isOne=True)
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
    player, enemy, objects = load_sprites()
    door = bytearray(objects['door_closed'])
    e = bytearray(enemy['sprite'])
    left = bytearray(player['sprite_left'])
    right = bytearray(player['sprite_right'])
    front = bytearray(player['sprite_front'])
    back = bytearray(player['sprite_back'])
    raw_test = [left, right, front, back]
    # x 0 is right side here..
    spriteX = 2
    spriteY = 25
    onTopScreen = True
    hasFlipped = False
    spriteW = 16
    spriteH = 20

    for i in range(150):
        mover = 0
        ymover = 0
        sprite_arr = raw_test[0]

        going_left = b1.value() == 1 and b2.value() == 0
        going_right = b2.value() == 1 and b1.value() == 0
        going_up = b2.value() == 1 and b1.value() == 1
        going_down = b2.value() == 0 and b1.value() == 0

        if going_down:
            sprite_arr = raw_test[3]
            ymover = 4
            mover = 0
        elif going_up:
            sprite_arr = raw_test[2]
            ymover = -4
            mover = 0
        elif going_left:
            mover = 5
            sprite_arr = raw_test[0]
            ymover = 0
        elif going_right:
            mover = -5
            sprite_arr = raw_test[1]
            ymover = 0

        if onTopScreen:
            if hasFlipped:
                d2.clear_buffers()
                d2.present()
                hasFlipped = False

            d1.draw_bitmap_array_raw(sprite_arr, spriteX, spriteY, spriteW, spriteH)
            d1.present()
            sleep(.10)
            d1.clear_buffers()
        else:
            if hasFlipped:
                d1.clear_buffers()
                d1.present()
                hasFlipped = False

            d2.draw_bitmap_array_raw(sprite_arr, spriteX, spriteY, spriteW, spriteH)
            d2.present()
            sleep(.10)
            d2.clear_buffers()

        spriteX += mover
        #spriteY += ymover

        spriteAtTop = spriteY > H - spriteH
        spriteAtLeft = spriteX >= W - spriteW

        if spriteAtLeft:
            spriteX = W - spriteW
        elif spriteX <= 0:
            spriteX = 0

        if spriteAtTop and onTopScreen: # bound to top screen top
            spriteY = H - spriteH
        elif spriteY <= 0 and onTopScreen: # move from top screen to bottom screen
            spriteY = H - spriteH
            onTopScreen = False
            hasFlipped = True
        elif spriteAtTop and not onTopScreen: # move from bottom screen to top screen
            spriteY = 0
            onTopScreen = True
            hasFlipped = True
        elif spriteY <= 0 and not onTopScreen: # bound to bottom of bottom screen
            spriteY = 0

        d1.draw_bitmap_array_raw(e, 50, 38, 14, 14)
        print(util.check_for_collision(spriteX, spriteY, spriteW, spriteH, 50, 38, 14, 14))

    d1.clear()
    d2.clear()
    return


def load_sprites():
    with open('sprites.json', 'r') as file:
        data = json.load(file)
    player = data['player']
    # sitting - 15x11
    # jumping - 12x12
    enemy = data['enemy']
    objects = data['objects'] # door: 25x11

    return (player, enemy, objects)


def test_enemy_and_player_render():
    player, enemy, objects = load_sprites()
    door_open = bytearray(objects['door_open'])
    door = bytearray(objects['door_closed'])
    grave = bytearray(objects['grave'])
    e = bytearray(enemy['sprite'])
    left = bytearray(player['sprite_left'])
    right = bytearray(player['sprite_right'])
    front = bytearray(player['sprite_front'])
    back = bytearray(player['sprite_back'])
    raw_test = [left, right, front, back]


    d2.draw_bitmap_array_raw(front, 30, 30, 16, 20)
    d2.draw_bitmap_array_raw(e, 50, 30, 14, 14)
    d2.draw_bitmap_array_raw(grave, 20, 20, 13, 11)
    d1.draw_bitmap_array_raw(door, 50, 50, 25, 11)
    d1.draw_bitmap_array_raw(door_open, 50, 10, 25, 11)
    d1.present()
    d2.present()
    sleep(10)


    return

# (self, lvl, exp, expReq, hp, attack, defense, speed, mana, money):
def parse_save_state(e):
    player = Player(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8])
    return player


# need a list of snowballs for rendering
# when one off screen, take out of list
# when enemy hit, spawn new on at new randome y
# player can move up and down at fixed x based on btns pushed
# snowball thrown every 250ms at given rate
def test_snowball_fight():
    player, enemy, objects = load_sprites()
    snowball = bytearray(objects['snowball'])
    e = bytearray(enemy['sprite'])
    right = bytearray(player['sprite_right'])
    py = 30
    px = 111
    ph = 20
    pw = 16
    ey = 30
    es = 14
    move_interval = 3
    snowballs = []
    max_snow = 10
    snowball_interval = 500
    prev_time = ticks_ms()
    for i in range(180):
        curr_time = ticks_ms()
        if ticks_diff(curr_time, prev_time) >= snowball_interval:
            prev_time = curr_time
            if len(snowballs) < max_snow:
                sy = int(py + (ph / 3))
                new_snow = Projectile(px, sy)
                snowballs.append(new_snow)

        going_up = b1.value() == 1
        going_down = b2.value() == 1

        if going_up:
            py -= move_interval
        elif going_down:
            py += move_interval

        if py >= H - 16:
            py = H - 16
        if py <= 0:
            py = 0

        d2.draw_bitmap_array_raw(right, px, py, pw, ph)
        d2.draw_bitmap_array_raw(e, 0, ey, es, es)
        snowballs = [s for s in snowballs if s.x >= 0]
        for s in snowballs:
            s.increment_x(-4)
            d2.draw_bitmap_array_raw(snowball, s.x, s.y, 5, 4)
            # minor optimize check, snowball cant contact if not close enough on x axis
            if s.x <= 15:
                if util.check_for_collision(0, ey, es, es, s.x, s.y, 5, 4):
                    ey = random.randint(0, 49)
                    print("HIT EM!")
        d2.present()
        sleep(.08)

        d2.clear_buffers()

    sleep(1)
    return


'''
This returns a list of len 255 of ints ranging from 0-255 themselves
255 should be ignored as that is considered empty space

eeprom = Eeprom(0x00, i2c_memory)
#eeprom.eeprom_write([1, 0, 1, 10, 3, 2, 1, 2, 0])
read_value = eeprom.eeprom_read()
print(f"Read from eeprom: {read_value}")

save_state_player_data = parse_save_state(read_value)
'''
#test_life()
#test_movement()
#test_ui(save_state_player_data)
#test_enemy_and_player_render()
test_snowball_fight()

sleep(2)
d1.cleanup()
d2.cleanup()


print('Done.')


'''

get collision detection figured out √
get the UI figured out √
load different levels
kill something
create a parse function and list of readable inventory for save state loading
Load a list of save state data and populate UI elements - player level, inventory √

'''

