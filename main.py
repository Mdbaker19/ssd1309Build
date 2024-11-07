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
db1 = Pin(6, Pin.IN, Pin.PULL_UP) # make this new menu cycle button (up)
db2 = Pin(7, Pin.IN, Pin.PULL_UP)
db3 = Pin(8, Pin.IN, Pin.PULL_UP) # make this new menu cycle button (down)
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

state_waiting = 'waiting' # render while i am cycling b1C to take an action
state_process = 'process' # handle my attack / defense / magic / run / item
state_update = 'update' # run the above logic and output result
state_end_turn = 'end_turn' # i did something, enemy take turn then waiting for me


# pre load bg ba?
fight_door, shop_door, shop_keep = rpg_start.load_entrences()
bank_door, bank_bg = rpg_start.load_entrences_two()
bg_top = rpg_start.load_bg_sprites()

def pressed(b):
    return b.value() == 0

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
def run_screens(passed_time, clear_one=True, clear_two=True):
    d1.present()
    d2.present()
    time_taken = ticks_ms() - passed_time
    #print(time_taken)
    sleep_amount = 17 - time_taken #60fps is 16.67ms
    if sleep_amount >= 0:
        print("Sleeping for: ", sleep_amount/500)
        sleep(sleep_amount / 500)
    if clear_one:
        d1.clear_buffers()
    if clear_two:
        d2.clear_buffers()
    return

def save_game_data(data):
    print("SAVING GAME")
    eeprom.eeprom_write(data)
    return

def ui_display(player, changed_values, first_draw, in_overworld=False):
    item_string = ', '.join([f'{key}: {value}' for key, value in player.items.items()])
    money_val = int(player.money)
    if money_val >= 1000:
        money_val = f"{money_val / 1000:.2f}K"
    elif money_val >= 1000000:
        money_val = f"{money_val / 1000000:.2f}M"
    clear = not first_draw
    if first_draw:
        changed_values = ["name", "hp", "mana", "lvl", "exp", "items", "money"]
    for value in changed_values:
        if value == "name":
            draw_text(128, 48, f"{player.class_type} . A:{player.attack}/D:{player.defense}", padding=2, clear_first=clear, isOne=False)
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
            draw_text(20, 20, f"Bank: {money_val}", padding=2, clear_first=clear, isOne=False)

    if in_overworld:
        draw_text(0, 55, "Enter ->", padding=2, isOne=False)
    d2.draw_rectangle(0, 0, SW, SH)
    return

def ui_display_battle(player, b1C):
    b1CY = max(b1C, 1)
    item_string = ', '.join([f'{key}: {value}' for key, value in player.items.items()])
    draw_text(128, 50, "Attack", padding=2, isOne=False)
    draw_text(128, 40, "Shield", padding=2, isOne=False)
    draw_text(128, 30, f"Magic: {player.mana}/{player.max_mana}", padding=2, isOne=False)
    draw_text(128, 20, f"Items: {item_string}", padding=2, isOne=False)
    draw_text(128, 10, "Run", padding=2, isOne=False)
    draw_text(0, 10, "Select ->", padding=2, isOne=False)
    draw_text(128, 0, f"HP: {player.hp}", padding=2, isOne=False)
    d2.draw_rectangle(0, b1CY*10 - 2, SW, 12)
    d2.draw_rectangle(0, 0, SW, SH)
    return

def ui_shop(money, b1C):
    b1CY = max(b1C, 1)
    draw_text(128, 50, "Potion: 10", padding=2, isOne=False)
    draw_text(128, 40, "DEF Book: 20", padding=2, isOne=False)
    draw_text(128, 30, "ATK Book: 20", padding=2, isOne=False)
    draw_text(128, 20, "SPEED Book: 20", padding=2, isOne=False)
    draw_text(128, 10, "ACC Book: 20", padding=2, isOne=False)
    draw_text(0, 10, "Select ->", padding=2, isOne=False)
    draw_text(0, 44, "Leave ->", padding=2, isOne=False)
    d2.draw_rectangle(0, b1CY*10 - 2, SW, 12)
    d2.draw_rectangle(0, 0, SW, SH)
    return

def ui_bank(money, rate, lvl, b1C):
    b1CY = max(b1C, 1)
    cost = 10 * lvl
    lvl = 2
    rate = rate % 100 #until it is over 100..
    draw_text(128, 50, f"Interest Rate: {rate}", padding=2, isOne=False)
    draw_text(128, 40, f"Bank Lvl: {lvl}", padding=2, isOne=False)
    draw_text(128, 30, f"Upgrade: {cost}", padding=2, isOne=False)
    draw_text(128, 20, "Withdrawl", padding=2, isOne=False)
    draw_text(128, 10, "Deposit", padding=2, isOne=False)
    draw_text(0, 10, "Select ->", padding=2, isOne=False)
    d2.draw_rectangle(0, b1CY*10 - 2, SW, 12)
    d2.draw_rectangle(0, 0, SW, SH)
    return

def run_rpg_battle_ui(player, b1C, ab1v, can_move_cursor):
    if can_move_cursor:
        if ab1v == 0:
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
        loop_time = ticks_ms()
        if pressed(quit_b):
            print("ending early!")
            break

        x, y = util.get_button_dir(db1, db2, db3, db4, 2)
        ab1v = ab1.value()
        selection_made = ab1v == 0

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

        d1.draw_bitmap_array_raw(w, 6, 0, ww, wh)
        d1.draw_bitmap_array_raw(r, 0 + ww + 20, 0, rw, rh)
        d1.draw_bitmap_array_raw(k, 0 + ww + rw + 38, 0, kw, kh)
        d1.draw_bitmap_array_raw(cba, cx, cy, 14, 14)
        draw_text(128, 48, "Choose class", padding=4, clear_first=False, isOne=False, isNotSmall=True)
        draw_text(118, 28, "Knight", padding=4, clear_first=False, isOne=False, isNotSmall=True)
        draw_text(74, 28, "Rouge", padding=4, clear_first=False, isOne=False, isNotSmall=True)
        draw_text(38, 28, "Wizard", padding=4, clear_first=False, isOne=False, isNotSmall=True)
        draw_text(0, 10, "-->", padding=2, isOne=False)
        run_screens(loop_time)
    return choice, atk_ba


# is everything really needed here along with b1C? or can i clean and trim up
def check_input(b1C, can_move_cursor, player, ab1v):
    b1C, can_move_cursor = run_rpg_battle_ui(player, b1C, ab1v, can_move_cursor)
    selections = ['Run', 'Items', 'Magic', 'Shield', 'Attack']
    selection = None
    if ab2v == 0:
        selection = selections[b1C-1]
    return selection


def is_in(v1, v2, value):
    return value >= v1 and value <= v2

def rpg_world(player):
    show_fight_door = True
    d_sx = 18 # door start x and below end x's
    sd_ex = 76
    fd_ex = 85
    bd_ex = 69
    d_values = [fd_ex, sd_ex, bd_ex]
    d_check_value = 0
    ui_display(player, [], True, True)
    door_words = ["Fight", "Store", "Bank"]
    curr_door = door_words[d_check_value]
    while True:
        loop_time = ticks_ms()

        if pressed(quit_b):
            print("ending early!")
            break

        x, y = util.get_button_dir(db1, db2, db3, db4, 5)
        player.x += x
        if player.x >= 95:
            player.x = 0
            d_check_value += 1
            d_check_value %= 3
            curr_door = door_words[d_check_value]
        player.x = Constants.constrained_between(player.x, 0, SW - player.w)

        if curr_door == "Fight":
            d1.draw_bitmap_array_raw(fight_door, d_sx, 0, 67, 51)
        elif curr_door == "Store":
            d1.draw_bitmap_array_raw(shop_door, d_sx, 0, 58, 54)
        elif curr_door == "Bank":
            d1.draw_bitmap_array_raw(bank_door, d_sx, 0, 51, 63)
        next_door = door_words[(d_check_value + 1) % 3]
        draw_text(128, 50, f"<- {next_door}", padding=2, isOne=True)

        d1.draw_bitmap_array_raw(player.choice, player.x, 0, player.w, player.h)
        if pressed(ab2):
            if is_in(d_sx, d_values[d_check_value], player.x):
                if curr_door == "Fight":
                    print("launching battle")
                    return "Battle"
                elif curr_door == "Store":
                    print("Go to store")
                    return "Store"
                elif curr_door == "Bank":
                    print("Go to bank")
                    return "Bank"

        # Not good for later im sure, need to preserve d2 UI... save time
        run_screens(loop_time, True, False)
    return


def rpg_battle_test(player, enemy_level):
    b1C = 0
    selections = ['Run', 'Items', 'Magic', 'Shield', 'Attack']
    selection = None

    e_ba = None
    e_sizes = None
    name = None
    e_has_attacked = False
    eatkbaw = 9
    eatkbah = 10

    if enemy_level % 3 == 0:
        e_ba, e_sizes, name, e_atk_ba = rpg_start.gen_ran_enemy_h() #atk ba is 13x10
        eatkbaw = 13
    else:
        e_ba, e_sizes, name, e_atk_ba = rpg_start.gen_ran_enemy_e() #atk ba is 9x10

    e_projectiles = []

    ew, eh = e_sizes
    e_atk_move = 5
    ex = SW-ew-e_atk_move-2 # little room for not off screen
    current_enemy = RPG_Enemy(enemy_level, ew, eh, name)
    # p_waiting, attack_made, enemy_attack_made, end? exit : go again
    battle_state = 1

    p_atk_miss = False

    while True:
        if pressed(quit_b):
            print("ending early!")
            break
        lt = ticks_ms()

        x, _ = util.get_button_dir(db1, db2, db3, db4, 3)
        player.x += x
        player.x = Constants.constrained_between(player.x, 0, SW - player.w - (ew - 3)) # cant walk on enemy


        '''Waiting for player input'''
        if battle_state == 1:
            if pressed(db1):
                b1C += 1
                b1C %= 6
            elif pressed(db3):
                b1C -= 1
                b1C = max(0, b1C)

            if pressed(ab1):
                selection = selections[b1C-1]
                battle_state += 1

        ''''''

        '''Handle Player Turn'''
        # for now to wait till bad ass art attack is done showing
        if len(e_projectiles) == 0:
            if battle_state == 2:
                p_atk_miss = False
                if selection == 'Attack':
                    player.attack_list.append(Projectile(player.x, player.y + int(player.h *.4), random.randint(-99999, 99999), player.atk_w, player.atk_h, ba=player.atk_ba, speed=player.speed))
                    p_atk_turn = rpg_u.attack_calc(player.attack, current_enemy.defense, current_enemy.speed, player.acc, 1.15, 1, player.lvl, current_enemy.lvl, False, False, True, player.items)
                    print(f"Player Atk made: {p_atk_turn}")
                    if p_atk_turn <= 0:
                        p_atk_miss = True
                    battle_state += 1
                    current_enemy.hp -= p_atk_turn
                    print(f"E health left: {current_enemy.hp}")
        ''''''

        # for now to wait till bad ass art attack is done showing
        if len(player.attack_list) == 0:
            '''Handle E Turn'''
            if battle_state == 3:
                battle_state = 4
                if current_enemy.hp >= 0:
                    e_has_attacked = True
                    e_projectiles.append(Projectile(SW, int(SH-eh), random.randint(-99999, 99999), eatkbaw, eatkbah, ba=e_atk_ba, speed=int(max(current_enemy.speed, 8))))
                    ex -= e_atk_move
                    e_atk_turn = rpg_u.attack_calc(current_enemy.attack, player.defense, player.speed, current_enemy.acc, 1.15, 1, current_enemy.lvl, player.lvl, False, False, False)
                    print(f"Enemy Atk made: {e_atk_turn}")
                    player.hp -= e_atk_turn
                    print(f"P health left: {player.hp}")
                else:
                    print("You win! looting")
                    loot = current_enemy.loot_table()
                    player.loot_victory(loot, current_enemy.lvl)
            ''''''

            '''Handle If Death'''
            if battle_state == 4:
                if player.hp <= 0 or current_enemy.hp <= 0:
                    print("Done!")
                    battle_state = 0
                else:
                    battle_state = 1
            ''''''

        ui_display_battle(player, b1C)
        d1.draw_bitmap_array_raw(bg_top, 0, 0, 128, 14)
        d1.draw_bitmap_array_raw(e_ba, ex, 0, ew, eh)
        if e_has_attacked:
            e_has_attacked = False
            ex += e_atk_move
        if p_atk_miss:
            draw_text(SW, 50, "Miss!", padding=2, isOne=True)
        else:
            draw_text(SW, 50, f"{current_enemy.hp:.2f}", padding=2, isOne=True)
        d1.draw_bitmap_array_raw(player.choice, player.x, player.y, player.w, player.h)

        player.attack_list = [p for p in player.attack_list if p.x < SW]
        for projectile in player.attack_list:
            d1.draw_bitmap_array_raw(projectile.ba, projectile.x, projectile.y, projectile.w, projectile.h)
            projectile.x += int(projectile.shot_speed_mult * 2) # for now

        e_projectiles = [p for p in e_projectiles if p.x > 0]
        for projectile in e_projectiles:
            d1.draw_bitmap_array_raw(projectile.ba, projectile.x, projectile.y, projectile.w, projectile.h)
            projectile.x -= int(projectile.shot_speed_mult * 2) # ^

        run_screens(lt)

        if battle_state == 0:
            break
    return

def rpg_shop_test(money):
    print("Shop WIP")
    b1C = 0
    selection = None
    selections = ["Acc", "Speed", "Atk", "Def", "Potion"]
    shop_k_y = 0
    shop_k_x = 30
    bought = True
    while True:
        if bought:
            shop_text = "please buy.. im hungry"
        if pressed(quit_b):
            print("ending early!")
            break
        if pressed(ab2):
            print("leaving shop")
            sleep(.5)
            return
        lt = ticks_ms()
        if pressed(db1):
            b1C += 1
            b1C %= 5
        elif pressed(db3):
            b1C -= 1
            b1C = max(0, b1C)
        ui_shop(money, b1C+1) # re use so need to add 1?
        print(f"B1C: {b1C}")
        if pressed(ab1):
            selection = selections[b1C]
        if selection != None:
            cost = 20
            if selection == "Potion":
                cost = 10
            bought = handle_shop_choice(selection, player, cost)
            if not bought:
                shop_text = "nothing for me or you.."
            selection = None
        d1.draw_bitmap_array_raw(shop_keep, shop_k_x, shop_k_y, 63, 47)
        draw_text(max(shop_k_x + 63, SW), max(shop_k_y - 5, 0), f"{shop_text}", padding=2, isOne=True)
        shop_k_y += random.randint(-2, 2)
        shop_k_x += random.randint(-2, 2)
        shop_k_x = Constants.constrained_between(shop_k_x, 0, SW - 63)
        shop_k_y = Constants.constrained_between(shop_k_y, 0, SH - 47)
        run_screens(lt)
    return

def handle_shop_choice(selection, player, cost):
    money = player.money
    print(f"You have {money} and cost is {cost}")
    if money >= cost:
        player.get_item(selection)
        player.money -= cost
        print("Buying : ", selection)
    else:
        print("sorry, can not afford")
        return False
    return True

def bank_deposit_withdrawl_ui(player):
    b1C = 0
    total = 0
    while True:
        if pressed(quit_b):
            print("ending early!")
            break
        b1CY = max(b1C, 1)
        if pressed(db3):
            b1C += 1
            b1C %= 3
        if pressed(db1):
            b1C -= 1
            b1C = max(0, b1C)

        if pressed(ab1): # 2 or 1?
            # get b1C and add to total
            total += 10
        draw_text(128, 20, "+10", padding=2, isOne=False)
        draw_text(128, 40, "-10", padding=2, isOne=False)
        draw_text(0, 44, "Leave", padding=2, isOne=False)
        draw_text(0, 10, "Select ->", padding=2, isOne=False)
        d2.draw_rectangle(0, b1CY*20 - 2, SW, 12)
        d2.draw_rectangle(0, 0, SW, SH)

        draw_text(128, 50, f"{total}", padding=2, isOne=False)
    return total

def handle_bank_choice(choice, player):
    if choice == 'u':
        cost = player.bank_level * 10
        if player.money >= cost:
            player.bank_level += 1
            player.bank_interest += 3
            # TODO: need to modify UI changed value to reflect new bank_level, intrest rate and upgrade cost....
        #check player money is enough for curr_player_bank_cost <- base it on curr bank level?
    elif choice == 'd':
        d2.clear_buffers()
        # get some kind of amount *_;
        deposit_amount = bank_deposit_withdrawl_ui(player)
        # add to player bank amount, decrement player money
    elif choice == 'w':
        d2.clear_buffers()
        withdrawl_amount = bank_deposit_withdrawl_ui(player)
        # another UI.... with some amount to enter ;_*
        # inverse above
    return

def rpg_bank(player):
    b1C = 0
    # TODO: upon loading bank, handle days past and accrue interest
    options = ["d", "w", "u"]
    while True:
        lt = ticks_ms()
        if pressed(quit_b):
            print("ending early!")
            break
        if pressed(db1):
            b1C += 1
            b1C %= 3
        elif pressed(db3):
            b1C -= 1
            b1C = max(0, b1C)
        elif pressed(ab2):
            print("Bank action")
            choice = options[b1C] # why is it named b1C? wakademasen
            handle_bank_choice(choice, player)
        ui_bank(player.money, player.bank_intrest, player.bank_level, b1C+1) # re use so need to add 1?
        d1.draw_bitmap_array_raw(bank_bg, 0, 0, 113, 64)
        run_screens(lt)
    return

def run_the_sequence():
    enemy_level = 1
    while True:
        if pressed(quit_b):
            print("ending early!")
            break
        choice = rpg_world(player)
        sleep(.5)
        if choice == "Battle":
            rpg_battle_test(player, enemy_level)
            enemy_level += 1
            player.handle_money_intrest()
        elif choice == "Store":
            rpg_shop_test(player.money)
        elif choice == "Bank":
            rpg_bank(player)
        else:
            print("Hmm how did you do this?")
            break
        print("Enemy level up: ", enemy_level)
    return


rpg_choice, atk_ba = pick_character_type()
choice, letter = rpg_choice

d2.clear_buffers()
player.be_born(choice, letter, atk_ba)
d1.clear_buffers()
sleep(.5)
run_the_sequence()
d1.cleanup()
d2.cleanup()




print('Done.')



