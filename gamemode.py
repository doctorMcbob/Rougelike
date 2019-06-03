from __future__ import print_function, unicode_literals
import sys
if sys.version_info[0] > 2: raw_input = input
import os
import pygame
from pygame.locals import *
from time import sleep
import LURD
from LURD import *
import pdb
PW = 32
WIDTH, HIGHT = (640, 480)
# tokens
L = "L"; U = "U"; R = "R"; D = "D"
S = "S"; C = "C"; E = "E"; P = "P"; I = "I"
Q = "Q"; H = "H"; T = "T"

DIR = { L: (-1, 0), U: (0, -1), R: (1, 0), D: (0, 1) }
KEYS = {
    "0":K_0, "1":K_1, "2":K_2, "3":K_3, "4":K_4, "5":K_5, "6":K_6, "7":K_7, "8":K_8, "9":K_9,
    "a":K_a, "b":K_b, "c":K_c, "d":K_d, "e":K_e, "f":K_f, "g":K_g, "h":K_h, "i":K_i, "j":K_j,
    "l":K_l, "m":K_m, "n":K_n, "o":K_o, "p":K_p, "q":K_q, "r":K_r, "s":K_s, "t":K_t, "u":K_u,
    "v":K_v, "w":K_w, "x":K_x, "y":K_y, "z":K_z
}
DIRKEYS = { 
    K_l: (-1, 0), K_LEFT: (-1, 0),
    K_u: (0, -1), K_UP: (0, -1),
    K_r: (1, 0), K_RIGHT: (1, 0),
    K_d: (0, 1), K_DOWN: (0, 1),
}

pygame.init()
dig_dungeon()
FONT = pygame.font.SysFont("Ubuntu", PW)
SCREEN = pygame.display.set_mode((WIDTH, HIGHT))
pygame.display.set_caption("The Temple of LURD")
LOG = pygame.Surface((WIDTH, HIGHT))
LOG.fill((200, 200, 200))
LOGFONT = pygame.font.SysFont("Ubuntu", PW//2)
SPRITES = {
    PLAYER: pygame.image.load("bin/player.png").convert(),
    DWNSTR: pygame.image.load("bin/downstairs.png").convert(),
    UPSTAIR: pygame.image.load("bin/upstairs.png").convert(),
    WALL: pygame.image.load("bin/wall.png").convert(),
    STONE: pygame.image.load("bin/stone.png").convert(),
    DOOR: pygame.image.load("bin/door.png").convert(),
    EMPTY: pygame.image.load("bin/empty.png").convert(),
    FLOOR: pygame.image.load("bin/floor.png").convert(),
    STAFF: pygame.image.load("bin/sword.png").convert(),
    ARMOR: pygame.image.load("bin/armor.png").convert(),
    GOLD: pygame.image.load("bin/gold.png").convert(),
    FIGHTABLE: pygame.image.load("bin/enemy.png").convert(),
    PICKAXE: pygame.image.load("bin/pickaxe.png").convert(),
    GETTABLE: pygame.image.load("bin/potion.png").convert(),
    DARK: pygame.image.load("bin/dark.png").convert(),
}
for key in SPRITES.keys():
    SPRITES[key].set_colorkey((255, 0, 220))
for piece in FIGHTABLE: COLORS[piece] = (255, 0, 0)
for piece in GETTABLE: COLORS[piece] = (0, 255, 0)
def neg(col): return ((col[0] + 127) % 255, (col[1] + 127) % 255, (col[2] + 127) % 255)
BTNS = {
    L: [K_LEFT, K_l],
    U: [K_UP, K_u],
    R: [K_RIGHT, K_r],
    D: [K_DOWN, K_d],
    S: [K_SPACE, K_s], C: [K_c], E: [K_e], P: [K_p],
    I: [K_i], H: [K_h], Q: [K_q], T: [K_t],
}
def get_inputs(btns=BTNS):
    inputs = []
    for event in pygame.event.get():
        if event.type == QUIT:
            quit()
        if event.type == KEYDOWN:
            for key in btns.keys():
                if event.key in btns[key]:
                    inputs.append(key)
    return inputs

def draw(destination, piece, position, PW=PW):
    x, y = position
    if piece not in SPRITES:
        for key in SPRITES.keys():
            if piece in key:
                piece = key
                break
    destination.blit(SPRITES[piece], (x * PW, y * PW))

def get_dungeon():
    dungeon = pygame.Surface((len(LEVELS[LEVEL][0]) * PW, len(LEVELS[LEVEL]) * PW))
    for y, line in enumerate(getlit([(find(ACTLAYER[LEVEL], PLAYER), 10)], LEVEL)):
        for x, piece in enumerate(line):
            draw(dungeon, piece, (x, y))
            act = get(ACTLAYER[LEVEL], (x, y))
            if act != EMPTY and (x, y) in get_inlight()[LEVEL]: 
                draw(dungeon, act, (x, y))
    return dungeon

def update_log(new):
    global LOG
    if not new: return
    log = pygame.Surface((WIDTH, HIGHT))
    log.fill((200, 200, 200))

    log.blit(LOG, (0, (PW/2) * len(new.splitlines())))
    for i, line in enumerate(new.splitlines()):
        log.blit(LOGFONT.render(line, 0, (0, 0, 0)), (0, PW/2 * i))
    LOG = log

def expect_input(expectlist=[]):
    while True:
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == QUIT: quit()
            if e.type == KEYDOWN:
                if expectlist:
                    if e.key in expectlist: return e.key
                else: return e.key

def show_inv(dest=SCREEN, test=None):
    inv = pygame.Surface((WIDTH/3, HIGHT/3 * 2))
    inv.fill((100, 100, 255))
    idx = "0123456789abcdefghijklmnopqrstuvwxyz"
    for i, item in enumerate(INV):
        if test and test in item:
            inv.blit(LOGFONT.render(idx[i] + " : " + item["name"], 0, (100, 255, 100)), (0, PW/2 * i))
        else:
            inv.blit(LOGFONT.render(idx[i] + " : " + item["name"], 0, (0, 0, 0)), (0, PW/2 * i))
    dest.blit(inv, (WIDTH/3 * 2, 0))
    btn = expect_input()
    for i, item in enumerate(INV):
        if idx[i] in KEYS and KEYS[idx[i]] == btn:
            return item
    return None

def get_stats_page():
    stats_page = pygame.Surface((PW * 5, HIGHT/3))
    stats_page.fill((100, 100, 255))
    stats = get_stats()
    stats_page.blit(LOGFONT.render("HP : " + str(stats["HP"]), 0, (0, 0, 0)), (PW/3, 0))
    stats_page.blit(LOGFONT.render("GOLD : " + str(stats["GOLD"]), 0, (0, 0, 0)), (PW/3, (PW/3*2)))
    stats_page.blit(LOGFONT.render("ATK : " + str(stats["ATK"]), 0, (0, 0, 0)), (PW/3, (PW/3*2)*2))
    stats_page.blit(LOGFONT.render("Weapon :", 0, (0, 0, 0)), (PW/3, (PW/3*2)*3))
    if stats["Weapon"]: stats_page.blit(LOGFONT.render(stats["Weapon"]["name"], 0, (0, 0, 0)), (PW/3, (PW/3*2)*4))
    stats_page.blit(LOGFONT.render("DEF : " + str(stats["DEF"]), 0, (0, 0, 0)), (PW/3, (PW/3*2)*5))
    stats_page.blit(LOGFONT.render("Armor :", 0, (0, 0, 0)), (PW/3, (PW/3*2)*6))
    if stats["Armor"]: stats_page.blit(LOGFONT.render(stats["Armor"]["name"], 0, (0, 0, 0)), (PW/3, (PW/3*2)*7))
    return stats_page

def get_enemy_page(enemy):
    page = pygame.Surface((PW * 5, HIGHT/3))
    page.fill((255, 100, 100))
    if enemy is None: return page
    page.blit(LOGFONT.render(enemy["name"], 0, (0, 0, 0)), (PW/3, 0))
    page.blit(LOGFONT.render("HP : " + str(enemy["HP"]), 0, (0, 0, 0)), (PW/3, (PW/3*2)))
    page.blit(LOGFONT.render("ATK : " + str(enemy["ATK"]), 0, (0, 0, 0)), (PW/3, (PW/3*2)*2))
    page.blit(LOGFONT.render("DEF : " + str(enemy["DEF"]), 0, (0, 0, 0)), (PW/3, (PW/3*2)*3))
    return page

def throw(pos, item, direction):
    x, y = pos
    hold = get(ACTLAYER[LEVEL], pos)
    put(ACTLAYER[LEVEL], pos, item["char"])
    LURD.ACTORS[LEVEL][pos] = item
    ret = step((x, y), d, LEVEL)
    put(ACTLAYER[LEVEL], pos, hold)
    while not ret:
        x, y = x + direction[0], y + direction[1]
        dungeon = get_dungeon()
        _x, _y = find(ACTLAYER[LEVEL], PLAYER)
        SCREEN.fill((55, 55, 55))
        SCREEN.blit(dungeon, (WIDTH/2 - (_x*PW),HIGHT/3 - (_y*PW)))
        SCREEN.blit(LOG, (0, (HIGHT/4)*3))
        SCREEN.blit(get_stats_page(), (WIDTH - PW * 5, (HIGHT/3)*2))
        SCREEN.blit(get_enemy_page(get_nme()), (WIDTH - PW * 10, (HIGHT/3)*2))
        pygame.display.update()
        sleep(0.05)
        get_inputs()
        ret = step((x, y), d, LEVEL)
    return ret

inputs = []; log = "The Journey Begins"
update_log(log)
while get_stats()["HP"] > 0:
    dungeon = get_dungeon()
    log = ""
    if not inputs:
        inputs = get_inputs()
    else:
        cmd = inputs.pop()
        if cmd in DIR: log += step(find(ACTLAYER[LEVEL], PLAYER), DIR[cmd], LEVEL)
        if cmd == S:
            pos = find(ACTLAYER[LEVEL], PLAYER)
            under = get(LEVELS[LEVEL], pos)
            if under == UPSTAIR:
                put(ACTLAYER[LEVEL], pos, EMPTY)
                LURD.LEVEL -= 1
                LEVEL = LURD.LEVEL
                if LEVEL < 0:
                    break
            elif under == DWNSTR:
                LURD.LEVEL += 1
                LEVEL = LURD.LEVEL
                put(ACTLAYER[LEVEL], pos, PLAYER)
                if LEVEL == len(LEVELS) - 1:
                    break
            log += "Floor " + str(LEVEL) + "..."
        if cmd == H:
            update_log(HELP+"\n===================")
            SCREEN.blit(LOG, (0, 10))
            expect_input()
        if cmd == I:
            show_inv(SCREEN)
        if cmd == E:            
            update_log("What would you like to equip? ")
            SCREEN.blit(LOG, (0, 10))
            item = show_inv(test='stat')
            if item is None: update_log("No item selected")
            elif "stat" not in item: update_log("Thats not equipable")
            else: log += str(equip(item))
        if cmd == C:
            update_log("What would you like to consume?")
            SCREEN.blit(LOG, (0, 10))
            item = show_inv(test='fn')
            if item is None: update_log("No item selected")
            elif "fn" not in item: update_log("Thats not consumable")
            else: 
                INV.remove(item)
                log += str(applypotion(item))
        if cmd == P:
            for item in INV:
                if item['name'] == "Pickaxe":
                    axe = item
                    break
            else:
                log += "No  pickaxe found\n"
                continue
            update_log("What direction?")
            SCREEN.blit(LOG, (0, (HIGHT/3)*2))
            d = DIRKEYS[expect_input([K_l, K_u, K_r, K_d, K_LEFT, K_UP, K_RIGHT, K_DOWN])]
            pos = find(ACTLAYER[LEVEL], PLAYER)
            delt = (pos[0] + d[0], pos[1] + d[1])
            item = get(LEVELS[LEVEL], delt)
            if item == WALL: put(LEVELS[LEVEL], delt, EMPTY)
            if item == STONE: put(LEVELS[LEVEL], delt, WALL)
            if item != EMPTY:
                if axe['uses']: axe['uses'] -= 1
                else:
                    if randint(0, 2) == 0:
                        INV.remove(axe)
                        log += "The pickaxe broke"
        if cmd == T:
            update_log("What would you like to throw?")
            SCREEN.blit(LOG, (0, 10))
            item = show_inv()
            if item is None: continue
            update_log("What direction?")
            _x, _y = find(ACTLAYER[LEVEL], PLAYER)
            SCREEN.fill((55, 55, 55))
            SCREEN.blit(dungeon, (WIDTH/2 - (_x*PW),HIGHT/3 - (_y*PW)))
            SCREEN.blit(LOG, (0, (HIGHT/4)*3))
            d = DIRKEYS[expect_input([K_l, K_u, K_r, K_d, K_LEFT, K_UP, K_RIGHT, K_DOWN])]
            INV.remove(item)
            log += throw(find(ACTLAYER[LEVEL], PLAYER), item, d)

        if cmd == Q: pdb.set_trace()
        bt = boardsturn(LEVEL).splitlines()
        for line in bt: 
            if line != "Bump": log += line
        update_log(log)
    _x, _y = find(ACTLAYER[LEVEL], PLAYER)
    SCREEN.fill((55, 55, 55))
    SCREEN.blit(dungeon, (WIDTH/2 - (_x*PW),HIGHT/3 - (_y*PW)))
    SCREEN.blit(LOG, (0, (HIGHT/4)*3))
    SCREEN.blit(get_stats_page(), (WIDTH - PW * 5, (HIGHT/3)*2))
    SCREEN.blit(get_enemy_page(get_nme()), (WIDTH - PW * 10, (HIGHT/3)*2))
    pygame.display.update()
pygame.quit()
clear()
print("You made it to level " + str(LEVEL))
if LEVEL == len(LEVELS) - 1: print("Wow! You won!")
print("You got " + str(get_stats()["GOLD"]) + " gold")
NAME = raw_input("Name?: ")
clear()
update_scoreboard(NAME, LEVEL)
