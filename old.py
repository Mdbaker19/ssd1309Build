class TestCode:
    def __init__(self):
        pass
    def test_life(self, w, h, odds=91):

        text_width = f8.measure_text("All dead!")

        grid = []

        for i in range(h):
            row = []
            for j in range(w):
                r = 1 if random.randint(0, 100) >= odds else 0
                row.append(r)
            grid.append(row)

        lifeGens = 50
        life = Life(grid, lifeGens, len(grid), 1, len(grid), len(grid[0]))
        ba, lw, lh = life.show_self(grid)

        for i in range(lifeGens):
            d2.present()
            grid = life.update_grid(grid)
            ba2, live_count = life.show_self(grid, nextGen=True)
            d2.draw_bitmap_array_raw(ba2, 128 - w, 64 - h, w, h)
            if live_count <= 0:
                draw_text(128, 35, "All dead!")
                d2.present()
                sleep(2)
                break
        return



    def test_movement(self):
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
            # spriteY += ymover

            spriteAtTop = spriteY > H - spriteH
            spriteAtLeft = spriteX >= W - spriteW

            if spriteAtLeft:
                spriteX = W - spriteW
            elif spriteX <= 0:
                spriteX = 0

            if spriteAtTop and onTopScreen:  # bound to top screen top
                spriteY = H - spriteH
            elif spriteY <= 0 and onTopScreen:  # move from top screen to bottom screen
                spriteY = H - spriteH
                onTopScreen = False
                hasFlipped = True
            elif spriteAtTop and not onTopScreen:  # move from bottom screen to top screen
                spriteY = 0
                onTopScreen = True
                hasFlipped = True
            elif spriteY <= 0 and not onTopScreen:  # bound to bottom of bottom screen
                spriteY = 0

            d1.draw_bitmap_array_raw(e, 50, 38, 14, 14)
            print(util.check_for_collision(spriteX, spriteY, spriteW, spriteH, 50, 38, 14, 14))

        d1.clear()
        d2.clear()
        return


# need a list of snowballs for rendering
# when one off screen, take out of list
# when enemy hit, spawn new on at new randome y
# player can move up and down at fixed x based on btns pushed
# snowball thrown every 250ms at given rate
def test_snowball_fight(player_data, player_profile, enemy, objects):
    test_ui(player_data)
    player_values_changed = False
    snowball = bytearray(objects['snowball'])

    e_snow = []
    e_prev_time = ticks_ms()
    e_move_prev_time = ticks_ms()

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
    while enemy.hp >= 0:
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
            enemy.change_value("y", random.randint(0, H - enemy.size), True)

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

        d2.draw_bitmap_array_raw(player_profile, px, py, pw, ph)
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
                    #print(f"HIT EM! {enemy.hp} / {enemy.base_hp}")
                    player_data.change_value("exp", 6)
                    player_values_changed = True

        for s in e_snow:
            s.increment_x(2)
            d2.draw_bitmap_array_raw(snowball, s.x, s.y, 5, 4)
            # minor optimize check, snowball cant contact if not close enough on x axis
            if s.x >= px:
                if util.check_for_collision(px, py, pw, ph, s.x, s.y, 5, 4):
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

    return

    # spawn enemies on map
    # when contacted, create a snowball battle with them and render UI above
    #     move above test function to something re usable with enemy level and id passed in
    # remove them from map when killed and decrement counter above door on map
    def test_enemies_present_snowball_kill(player):
        enemies_list = [] # spawn calling enemy class?
        require_kills = 3 #len(enemies_list) ?
        battle_running = False
        player_ba_list, eba, objects = load_sprites()

        eba = bytearray(eba['sprite'])

        #(self, lvl, x, y, ba, size, ide)
        enemy = Enemy(2, 100, 40, eba, 14, 256)
        door_closed_ba = bytearray(objects['door_closed'])

        right_side_player = bytearray(player_ba_list['sprite_right'])
        #test_snowball_fight(player_data, right_side_player, enemy, objects)

        px = 0
        py = 0

        ph = 20
        pw = 16



        # if contacted player and enemy
        # get enemy data by position and create snowball fight
        # on victory save player hp (update if level up) and remove enemy from map
        # required_kills -= 1

        for i in range(75):
            b1v = b1.value()
            b2v = b2.value()
            profile, px, py, crossed_screens, on_top_screen = player.handle_movement(px, py, ph, pw, player_ba_list, b1v, b2v, starting_on_top_screen=False)
            d2.draw_sprite(profile, px, py, pw, ph)
            d2.draw_sprite(enemy.ba, enemy.x, enemy.y, enemy.size, enemy.size)
            d2.present()
            if util.check_for_collision(px, py, pw, ph, enemy.x, enemy.y, enemy.size, enemy.size):
                enemy.x = 0 # maybe move this to a start_fn?
                test_snowball_fight(player, right_side_player, enemy, objects)
                px = random.randint(0, Constants.max_x(pw))
                py = random.randint(0, Constants.max_y(ph))
                enemy.x = random.randint(0, Constants.max_x(enemy.size))
                enemy.y = random.randint(0, Constants.max_y(enemy.size))

                '''DO something about restore enemy health and level up'''

            sleep(.20)
            d1.clear_buffers()
            d2.clear_buffers()
            sleep(.05)

        # for now refactor
        # create one enemy on map like test_movement
        # have it check contact for enemy and player
        # start a snowball fight


        #d1.clear_buffers()
        #d2.clear_buffers()
        d1.draw_bitmap_array_raw(door_closed_ba, 50, 50, 25, 11)
        d1.present()
        d2.present()
        sleep(5)
    return
def test_pong(objects):
    score = 0
    score_changed = False
    draw_text(128, 52, f"Score: {score}", padding=2, clear_first=False)
    paddle_sprite = bytearray(objects['pong_paddle'])
    paddle_ball = bytearray(objects['tower_ammo'])
    pw = 3
    ph = 19
    px = W - pw
    py = 0
    aix = 0
    aiy = 64
    ball_size = 2
    ballx = W / 2
    bally = H / 2
    ballyv = 2
    ballxv = 2
    passed_side = False
    while not passed_side:
        loop_time = ticks_ms()
        b1v = b1.value()
        b2v = b2.value()

        if b1v == 1:
            py += 2
        elif b2v == 1:
            py -= 2
        py = int(py)
        py = Constants.constrained_between(py, ph)
        ballx += ballxv
        bally += ballyv
        bally = int(bally)
        ballx = int(ballx)
        aiy = random.randint(bally - 10, bally + 5)
        if bally <= 0 or bally >= H - ball_size:
            ballyv *= -1
        if util.check_for_collision(ballx, bally, ball_size, ball_size, px, py, pw, ph, hit_box_mult=.2):
            ballxv *= -1
            ballyv *= -1
        elif ballx >= W:
            passed_side = True

        if util.check_for_collision(ballx, bally, ball_size, ball_size, aix, aiy, pw, ph, hit_box_mult=1):
            ballxv *= -1
            ballyv *= -1
        elif ballx <= 0:
            ballx = int(W / 2)
            bally = int(H / 2)
            score += 1
            score_changed = True
        if score_changed:
            draw_text(128, 52, f"Score: {score}", padding=2, clear_first=True)
            score_changed = False

        d2.draw_bitmap_array_raw(paddle_sprite, px, py, pw, ph)
        d2.draw_bitmap_array_raw(paddle_ball, ballx, bally, ball_size, ball_size)
        d2.draw_bitmap_array_raw(paddle_sprite, aix, aiy, pw, ph)
        run_screens(loop_time)
    return

