"""x:0, y:0 is generally bottom right"""
from time import ticks_ms, sleep, ticks_diff
from machine import Pin, SPI, ADC, I2C
from xglcd_font import XglcdFont
from ssd1309 import Display
from life import Life
from util import Util
from eeprom import Eeprom
from player import Player
from enemy import Enemy
from projectile import Projectile
from test_code import TestCode
import json
import math
import random


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




def load_sprites():
    with open('sprites.json', 'r') as file:
        data = json.load(file)
    player = data['player']
    enemy = data['enemy']
    objects = data['objects']

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
def test_snowball_fight(player_data, lvl, sprites):
    test_ui(player_data)
    player_values_changed = False
    player, enemy, objects = sprites
    snowball = bytearray(objects['snowball'])

    e = bytearray(enemy['sprite'])
    enemy = Enemy(lvl, 0, 30, e, 14, 255)
    e_snow = []
    e_prev_time = ticks_ms()
    e_move_prev_time = ticks_ms()

    right = bytearray(player['sprite_right'])
    py = 30
    px = 111
    ph = 20
    pw = 16
    player_damage = 2
    move_interval = 3
    snowballs = []
    max_snow = 10
    snowball_interval = 800

    prev_time = ticks_ms()
    for i in range(100):
        curr_time = ticks_ms()
        if ticks_diff(curr_time, prev_time) >= snowball_interval:
            prev_time = curr_time
            if len(snowballs) < max_snow:
                sy = int(py + (ph / 3))
                # projectile class can take in own bytearray to render, but not necessary as they are all snowballs, no need for extra refs
                new_snow = Projectile(px, sy, random.randint(-9999, 9999))
                snowballs.append(new_snow)
        if ticks_diff(curr_time, e_prev_time) >= enemy.at_int:
            e_prev_time = curr_time
            if len(e_snow) < enemy.max_ammo:
                sy = int(enemy.y + (enemy.size / 3))
                new_snow = Projectile(enemy.x, sy, random.randint(-9999, 9999))
                e_snow.append(new_snow)
        if ticks_diff(curr_time, e_move_prev_time) >= enemy.move_int:
            e_move_prev_time = curr_time
            enemy.change_value("y", random.randint(0, H - enemy.size))

        going_up = b1.value() == 1
        going_down = b2.value() == 1

        if going_up:
            py -= move_interval
        elif going_down:
            py += move_interval

        if py >= H - ph:
            py = H - ph
        if py <= 0:
            py = 0

        d2.draw_bitmap_array_raw(right, px, py, pw, ph)
        d2.draw_bitmap_array_raw(enemy.ba, enemy.x, enemy.y, enemy.size, enemy.size)
        snowballs = [s for s in snowballs if s.x >= 0]
        e_snow = [s for s in e_snow if s.x <= W]
        for s in snowballs:
            s.increment_x(-4)
            d2.draw_bitmap_array_raw(snowball, s.x, s.y, 5, 4)
            # minor optimize check, snowball cant contact if not close enough on x axis
            if s.x <= enemy.size:
                if util.check_for_collision(enemy.x, enemy.y, enemy.size, enemy.size, s.x, s.y, 5, 4):
                    enemy.change_value("hp", -player_damage)
                    print(f"HIT EM! {enemy.hp} / {enemy.base_hp}")
                    player_data.change_value("exp", 6)
                    player_values_changed = True

        for s in e_snow:
            s.increment_x(2)
            d2.draw_bitmap_array_raw(snowball, s.x, s.y, 5, 4)
            # minor optimize check, snowball cant contact if not close enough on x axis
            if s.x >= px:
                if util.check_for_collision(px, py, pw, ph, s.x, s.y, 5, 4):
                    print("Health Loss!!")
                    player_data.change_value("hp", -1)
                    player_values_changed = True
                    s.increment_x(200)

        d2.present()
        if player_values_changed:
            d1.clear_buffers()
            test_ui(player_data)
            player_values_changed = False
        sleep(.08)

        d2.clear_buffers()
        if enemy.hp <= 0:
            break

    return

# spawn enemies on map
# when contacted, create a snowball battle with them and render UI above
#     move above test function to something re usable with enemy level and id passed in
# remove them from map when killed and decrement counter above door on map
def test_enemies_present_snowball_kill(player_data):
    enemies_list = [] # spawn calling enemy class?
    require_kills = 3 #len(enemies_list) ?
    battle_running = False
    player, eba, objects = load_sprites()

    (player_ba, xmove, ymove) = player_data.get_dir_profile(player, b1.value(), b2.value())
    #(self, lvl, x, y, ba, size, ide)
    enemy = Enemy(2, 10, 30, eba, 14, 256)
    door_closed_ba = objects['door_closed']

    ''' Refactor fn to take in enemy instead of lvl and sprites

This will be called when needed, make sure we can run it here
'''
    test_snowball_fight(player_data, 2, (player, enemy, objects))
    # if contacted player and enemy
    # get enemy data by position and create snowball fight
    # on victory save player hp (update if level up) and remove enemy from map
    # required_kills -= 1
    d2.draw_bitmap_array_raw(player_ba, px, py, pw, ph)
    d2.draw_bitmap_array_raw(enemy.ba, enemy.x, enemy.y, enemy.size, enemy.size)
    # for now refactor
    # create one enemy on map like test_movement
    # have it check contact for enemy and player
    # start a snowball fight



    d1.draw_bitmap_array_raw(door_closed_ba, 50, 50, 25, 11)
    d1.present()
    d2.present()
    sleep(2)
    return


def save_game_data(data):
    eeprom.eeprom_write(data)
    return

'''
This returns a list of len 255 of ints ranging from 0-255 themselves
255 should be ignored as that is considered empty space
'''
eeprom = Eeprom(0x00, i2c_memory)
read_value = eeprom.eeprom_read()
print(f"Read from eeprom: {read_value}")

save_state_player_data = parse_save_state(read_value)
'''
Needs font, load sprites, draw text...
test_code = TestCode()
test_code.test_life()
test_code.test_movement()
'''
#test_ui(save_state_player_data)
#test_enemy_and_player_render()
#test_snowball_fight(save_state_player_data, 1)


test_enemies_present_snowball_kill(save_state_player_data)

sleep(2)
d1.cleanup()
d2.cleanup()


print('Done.')


'''

get collision detection figured out √
get the UI figured out √
load different levels
kill something √
enemy attack me √ and health decrement
create a parse function and list of readable inventory for save state loading
Load a list of save state data and populate UI elements - player level, inventory √

'''

