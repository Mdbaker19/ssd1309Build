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
from tower import Tower
from test_code import TestCode
from constants import Constants
import json
import math
import random
from rpg_util import RPG_Util
from rpg import RPG, RPG_Player, RPG_Enemy

ab1 = Pin(5, Pin.IN, Pin.PULL_UP)
ab2 = Pin(4, Pin.IN, Pin.PULL_UP)
db1 = Pin(6, Pin.IN, Pin.PULL_UP)
db2 = Pin(7, Pin.IN, Pin.PULL_UP)
db3 = Pin(8, Pin.IN, Pin.PULL_UP)
db4 = Pin(9, Pin.IN, Pin.PULL_UP)

quit_b = Pin(15, Pin.IN, Pin.PULL_UP)

i2c_memory = I2C(0, scl=Pin(1), sda=Pin(0), freq=50000)

SW = 128
SH = 64
FH = 8
FHS = 4

f8 = XglcdFont('Wendy7x8.c', 7, FH)
#f3 = XglcdFont('Wendy7x8.c', 4, FHS)

spi = SPI(0, baudrate=10000000, sck=Pin(18), mosi=Pin(19))
d1 = Display(spi, dc=Pin(16), cs=Pin(17), rst=Pin(20))
spi2 = SPI(1, baudrate=10000000, sck=Pin(10), mosi=Pin(11))
d2 = Display(spi2, dc=Pin(12), cs=Pin(13), rst=Pin(2))

eeprom = Eeprom(0x00, i2c_memory)
#read_value = eeprom.eeprom_read()

#save_state_player_data = parse_save_state(read_value)
player = RPG_Player(1)
util = Util()
rpg_u = RPG_Util()

rpg_start = RPG()


def draw_text(x, y, text, padding=0, clear_first=False, isOne=True, isNotSmall=True):
    text_width = f8.measure_text(text)
    x = x - padding
    if x < text_width:
        x = text_width + padding
    fh = FH if isNotSmall else FHS
    if isOne:
        if clear_first:
            d1.draw_bitmap_array_raw(bytearray([0] * (128 * FH)), 0, y, 128, fh)
        d1.draw_text(x, y, text, f8, False, 180)
    else:
        if clear_first:
            d2.draw_bitmap_array_raw(bytearray([0] * (128 * FH)), 0, y, 128, fh)
        d2.draw_text(x, y, text, f8, False, 180)
    return


# (self, lvl, hp, acc, defense, attack=None, mana=None, max_mana=None, choice=None, speed=None)
def parse_save_state(e):
#    stats_used_so_far = e[:9]
    player = RPG_Player(1, 10, 5, 3)
    return player

#renders screens and sleeps for 30fps average from time passed in
def run_screens(passed_time):
    d1.present()
    d2.present()
    time_taken = ticks_ms() - passed_time
    #print(time_taken)
    sleep_amount = 17 - time_taken #60fps is 16.67ms
    if sleep_amount >= 0:
        sleep(sleep_amount / 500)
    d1.clear_buffers()
    d2.clear_buffers()
    return

def save_game_data(data):
    print("SAVING GAME")
    eeprom.eeprom_write(data)
    return

def ui_display(player, changed_values, first_draw):
    item_string = ', '.join([f'{key}: {value}' for key, value in player.items.items()])
    money = int(player.money)
    clear = not first_draw
    if first_draw:
        changed_values = ["name", "hp", "mana", "lvl", "exp", "items", "money"]
    for value in changed_values:
        if value == "name":
            draw_text(128, 48, f"{player.class_type}", padding=2, clear_first=clear, isOne=False)
        if value == "hp":
            draw_text(128, 40, f"Health: {player.hp}", padding=2, clear_first=clear, isOne=False)
        if value == "mana":
            draw_text(128, 32, f"Mana: {player.mana}/{player.max_mana}", padding=2, clear_first=clear, isOne=False)
        if value == "lvl":
            draw_text(128, 24, f"Level: {player.lvl}", padding=2, clear_first=clear, isOne=False)
        if value == "exp":
            draw_text(128, 16, f"Exp: {player.exp}/{player.expReq}", padding=2, clear_first=clear, isOne=False)
        if value == "items":
            draw_text(128, 8, f"Items: {item_string}", padding=2, clear_first=clear, isOne=False)
        if value == "money":
            draw_text(20, 54, f"Bank: {money}", padding=2, clear_first=clear, isOne=False)

    d2.draw_rectangle(0, 0, SW, SH)
    return

def ui_display_battle(player, b1C):
    print(b1C)
    item_string = ', '.join([f'{key}: {value}' for key, value in player.items.items()])
    draw_text(128, 50, "Attack", padding=2, isOne=False)
    draw_text(128, 40, "Shield", padding=2, isOne=False)
    draw_text(128, 30, f"Magic: {player.mana}/{player.max_mana}", padding=2, isOne=False)
    draw_text(128, 20, f"Items: {item_string}", padding=2, isOne=False)
    draw_text(128, 10, "Run", padding=2, isOne=False)
    d2.draw_rectangle(0, b1C*10 - 2, SW, 12)
    d2.draw_rectangle(0, 0, SW, SH)
    return



def run_rpg_battle_ui(player, b1C, ab1v, can_move_cursor):
    if can_move_cursor:
        if ab1v == 1:
            b1C -= 1
        if b1C < 0:
            b1C = 5
        can_move_cursor = False
    ui_display_battle(player, b1C)
    return b1C, can_move_cursor

def rpg_start_screen():
    screen_ba = rpg_start.load_start_screen()
    d1.draw_bitmap_array_raw(screen_ba, 0, 0, 117, 54)
    d1.present()
    return

def pick_character_type():
    choice_made = False
    cba, fire, daggers, sword = rpg_start.load_obj_sprites()
    (w, r, k) = rpg_start.psprites
    ww, wh = rpg_start.wizard_s
    rw, rh = rpg_start.rouge_s
    kw, kh = rpg_start.knight_s
    cx = 70
    cy = 42
    choice = None
    while not choice_made:
        x, y = util.get_button_dir(db1, db2, db3, db4, 2)

        ab1v = ab1.value()
        selection_made = ab1v == 1

        if selection_made:
            if cx < 24:
                choice = (w, 'w')
                atk_ba = fire
            elif cx < 66 and cx > 40:
                choice = (r, 'r')
                atk_ba = daggers
            elif cx < 114 and cx > 80:
                choice = (k, 'k')
                atk_ba = sword
            if not choice is None:
                choice_made = True

        cx += x
        cy += y

        cy = Constants.constrained_between(cy, 0, SH-14)
        cx = Constants.constrained_between(cx, 0, SW-14)

        loop_time = ticks_ms()
        d1.draw_bitmap_array_raw(w, 6, 0, ww, wh)
        d1.draw_bitmap_array_raw(r, 0 + ww + 20, 0, rw, rh)
        d1.draw_bitmap_array_raw(k, 0 + ww + rw + 38, 0, kw, kh)
        d1.draw_bitmap_array_raw(cba, cx, cy, 14, 14)
        draw_text(128, 48, "Choose class", padding=4, clear_first=False, isOne=False, isNotSmall=True)
        draw_text(118, 28, "Knight", padding=4, clear_first=False, isOne=False, isNotSmall=True)
        draw_text(74, 28, "Rouge", padding=4, clear_first=False, isOne=False, isNotSmall=True)
        draw_text(38, 28, "Wizard", padding=4, clear_first=False, isOne=False, isNotSmall=True)
        run_screens(loop_time)
    return choice, atk_ba

def run_battle_sequence(player, enemy, b1C, can_move_cursor):
    player_ran = False # does nothing right now
    ab1v = ab1.value()
    ab2v = ab2.value() # need to make it the decision button
    b1C, can_move_cursor = run_rpg_battle_ui(player, b1C, ab1v, can_move_cursor)
    if ab2v == 1:
        selections = ['Run', 'Items', 'Magic', 'Shield', 'Attack']
        print(selections[b1C-1])
        # how to wait and handle this... while not decision?
    e_atk_turn = rpg_u.attack_calc(enemy.attack, player.defense, player.speed, enemy.acc, 1.15, 1, enemy.lvl, player.lvl, False, False)
    player_rare_drops = player.items.get('RD')
    p_atk_turn = rpg_u.attack_calc(player.attack, enemy.defense, enemy.speed, player.acc, 1.15, 1, player.lvl, enemy.lvl, False, False, player_rare_drops)

    enemy.hp -= p_atk_turn
    player.hp -= e_atk_turn
    #print(f"Enemy LVL {enemy.lvl}: {e_atk_turn} and You: {p_atk_turn} HP: E: {enemy.hp} and P: {player.hp}")
    if player.hp <= 0 or enemy.hp <= 0:
        print("ENDING BATTLE")
        return False, b1C
    return True, b1C


def rpg_battle_one(player):
    battle_start = False
    start_ms = ticks_ms()
    bg = rpg_start.load_bg_sprites()
    first_e_s, first_e_sizes, name = rpg_start.gen_ran_enemy_e()
    ew, eh = first_e_sizes
    enemy_one = RPG_Enemy(180, ew, eh, name)
    b1C = 0
    can_move_cursor = False
    ui_shift_delay = 100
    prev_ui_shift_time = start_ms
    p_atk_delay = 1000
    prev_player_atk_int = start_ms
    while True:

        loop_time = ticks_ms()

        quit_bv = quit_b.value()
        if quit_bv == 1:
            print("ending early!")
            break

        ui_shift_time = loop_time
        if ticks_diff(ui_shift_time, prev_ui_shift_time) >= ui_shift_delay:
            prev_ui_shift_time = ui_shift_time
            can_move_cursor = True

        p_atk_time = loop_time
        x, y = util.get_button_dir(db1, db2, db3, db4, 5)
        if x == 0:
           draw_text(128, 50, "Go on.. walk", padding=0, clear_first=False, isOne=True, isNotSmall=True)


        player.x += x
        player.x = Constants.constrained_between(player.x, 0, SW - player.w)

        if player.x >= 80:
            player.x = 0
            battle_start = True

        if battle_start:
            d1.draw_bitmap_array_raw(bg, 0, 0, SW-1, SH-1)
            d1.draw_bitmap_array_raw(first_e_s, SW-enemy_one.w, 0, enemy_one.w, enemy_one.h)
            battle_start, b1C = run_battle_sequence(player, enemy_one, b1C, can_move_cursor)
            print(enemy_one.hp)
            for projectile in player.attack_list:
                d1.draw_bitmap_array_raw(projectile.ba, projectile.x, projectile.y, projectile.w, projectile.h)
                projectile.x += projectile.shot_speed_mult

            if ticks_diff(p_atk_time, prev_player_atk_int) >= p_atk_delay:
                prev_player_atk_int = p_atk_time
                player.attack_list.append(Projectile(player.x, player.y + int(player.h *.4), random.randint(-99999, 99999), player.atk_w, player.atk_h, ba=player.atk_ba, speed=player.speed))

        else:
            ui_display(player, [], True)
            player.attack_list = [p for p in player.attack_list if p.x < SW]
        d1.draw_bitmap_array_raw(player.choice, player.x, player.y, player.w, player.h)

        run_screens(loop_time)
    return


rpg_start_screen()
sleep(1)
d1.clear_buffers()
rpg_choice, atk_ba = pick_character_type()
choice, letter = rpg_choice

d2.clear_buffers()
player.be_born(choice, letter, atk_ba)
d1.clear_buffers()
draw_text(128, 28, 'Hello There, let us begin', padding=0)
d1.present()
d2.present()
sleep(1)
d1.clear_buffers()
rpg_battle_one(player)
sleep(.5)
d1.cleanup()
d2.cleanup()


print('Done.')

'''

battle victory and loot, next battle
show atk ba
print what decision ab2v makes when clicked based on b1C position
'''

