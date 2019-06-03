#rlike.py redux
"""
am i really going to re write this whole thing again? yes, problably
"""
from __future__ import print_function, unicode_literals
import os
import sys
from random import randint, choice
from time import sleep
from math import sqrt
import pdb
DEBUG = "-d" in sys.argv
#convinience
D = {"l": (-1, 0),
    "u": (0, -1),
    "r": (1, 0),
    "d": (0, 1)} 

### ---- SPRITES ----
PLAYER = "@"; DWNSTR = ">"; UPSTAIR = "<"; STONE = "#"
WALL = "+"; DOOR = "="; EMPTY = " "; FLOOR = "."; DARK = "\\"
GOLD = "*"; STAFF = "/"; PICKAXE = "{"
BATTERY = "%"; ARMOR = "["
# groups
POT = "bcdfghjklmnprstvwxyz"
CONSUME = POT + BATTERY + PICKAXE
WEAP = STAFF 
FIGHTABLE = "BCDFGHJKLMNPRSTVWXYZ"
TANG = STONE + WALL + DOOR  # Tangible
ACT = PLAYER + DOOR + FIGHTABLE + GOLD
GETTABLE = WEAP + ARMOR + CONSUME
COLORS = {
    PLAYER: "\033[1;45;93m",
    DWNSTR: "\033[1;45;33m",
    UPSTAIR: "\033[1;45;33m",
    WALL: "\033[1;94;40m",
    STONE: "\033[1;90;40m",
    DOOR: "\033[1;43;40m",
    EMPTY: "\033[45m",
    FLOOR: "\033[1;45;35m",
    STAFF: "\033[1;45;96m",
    ARMOR: "\033[1;45;96m",
    GOLD: "\033[1;33;35m",
    "ENEMY": "\033[1;45;91m",
    "CONSUME": "\033[1;45;92m",

    DARK: "\033[0m",
    "\n": "\033[0m",
    "footer": "\033[0m",
}

### ---- GAME GLOBALS ----
INLIGHT = [set()]
LEVELS = []
ACTLAYER = []
ACTORS = [{}]
LEVEL = 0
SCORE = 0
INV = []
HP = 50
ATK = 5
DEF = 5
EQUIP = {
    "weapn": None,
    "armor": None
}
NME = None
# the RNG picks randomly from:
# bbbcdddfffggghjklllmmnnppprstttvwwxyyyyz
POTIONS = {
    "bf": "+ HP",
    "gkl": "+ STR",
    "mns": "+ DEF",
    "twv": "- STR",
    "jpr": "- DEF",
    "d": "PSN",
    "hxzc": "VIS",
    "y": "WARP",
}

#some set up
LEVELS.append("""###########
#         #
#  <   >  #
#         #
#         #
###########""".splitlines())
ACTLAYER.append(["           ",
"           ",
"           ",
"     @     ",
"           ",
"           "])
END = """##########
#        #
#  <     #
#        #
#        #
##########""".splitlines()
HELP = """
COMMANDS:
. l: Left  . s: Stairs      . q: Quit
. u: Up    . i: Inventory   . c: Consume(potions)
. r: Right . e: Equip       . p: Pickaxe
. d: Down  . h: Help (thats this)

SPRITES:
. @: You   . >: Downward   . /: Weapon
. #: Stone . <: Upward     . [: Armor
. +: Wall  . {: Pickaxe    .  : Empty
. =: Door  . *: Gold       . .: Floor

""" # thanks pal
### ---- DISPLAY FUNCTIONS ----
def clear(): os.system("clear || cls")
def colored(ch): 
    if ch == DARK: return EMPTY + COLORS['footer']
    elif ch in COLORS: return COLORS[ch] + ch + COLORS['footer']
    elif ch in FIGHTABLE: return COLORS["ENEMY"] + ch + COLORS['footer']
    elif ch in CONSUME: return COLORS["CONSUME"] + ch + COLORS['footer'] 
    else: return COLORS[EMPTY] + ch + COLORS['footer']
def printb(b, layer2=None):
    s = ""
    for y, line in enumerate(b):
        for x, piece in enumerate(line):
            if layer2 is not None and get(layer2, (x, y)) != EMPTY and piece != DARK:
                s += colored(get(layer2, (x, y)))
            else:
                s += colored(piece)
        s += "\n"
    print(s)
def animate(b, t, layer2=None, debug=False, data=False):
    if debug and not DEBUG: return
    clear(); printb(b, layer2=layer2)
    if data: print(data)
    sleep(t)
### ---- SPLITLINES TOOLKIT ----
def get(b, pos): return b[pos[1]][pos[0]]
def getsub(b, pos, dim): return [b[pos[1]+y][pos[0]:pos[0]+dim[0]] for y in range(dim[1])]
def put(b, pos, piece): b[pos[1]] = b[pos[1]][:pos[0]] + piece + b[pos[1]][pos[0]+1:]
def getdist(p1, p2): return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
def nbrs(x, y): return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
def find(b, piece):
    y = 0
    while piece not in b[y]:
        y += 1
        if y >= len(b): return False
    return b[y].index(piece), y
def allof(b, piece):
    for y, line in enumerate(b):
        for x, pce in enumerate(line):
            if pce == piece: yield x, y
def insert(board, sub, position):
    for y, line in enumerate(sub):
        for x, piece in enumerate(line):
            put(board, (position[0] + x, position[1] + y), sub[y][x])
def bisequal(b1, b2):
    if len(b1) != len(b2):return False
    for i in range(len(b1)): 
        if b1[i] != b2[i]: return False
    return True
def findsub(b, sub):
    checklist = allof(b, sub[0][0])
    ret = []
    for pos in checklist:
        try:
            if bisequal(getsub(b, pos, (len(sub[0]), len(sub))), sub):
                ret.append(pos)
        except IndexError: continue
    return ret
### ---- GAME PIECE TOOLKIT ----
def makename():
    vowel = "aeiou"
    const = "bbbcdddfffggghjklllmmnnppprstttvwwxyyyz"
    special = "bdfglp"
    roll = randint(0, 100)
    if roll < 15: return choice(const) + choice(vowel) + (choice(special) * 2) + "y"
    if roll < 50: return choice(const) + choice(vowel) + choice(special) + (choice(special) * 2) + choice(vowel) + choice(special) + "y"
    if roll < 65: return choice(const) + choice(vowel) + choice(const) + choice(vowel) + "ly"
    if roll < 80: return choice(const) + choice(special) + choice(vowel) + choice(vowel) + choice(special) + choice(special)
    return choice(special) + choice(vowel) + choice(special) + choice(special)
def makeitem(ch, lvl):
    if ch == STAFF: name = "Sword of " + makename()
    elif ch == ARMOR: name = "Suit of " + makename() + " Armor"
    return {
        "name": name,
        "stat": lvl + randint(-2, 10),
        "char": ch,
    }
def makepickaxe():
    return {
        "name": "Pickaxe",
        "uses": randint(2, 10),
        "char": PICKAXE
    }
def makepotion(name=None):
    if name is None: name = makename()
    for key in POTIONS:
        if name[0] in key: fn = POTIONS[key]
    return {
        "name": "A potion marked " + name,
        "fn": fn,
        "char": name[0],
    }
def makeenemy(lvl):
    name = makename()
    return {
        "name": name,
        "state": choice(["agg", "hide", "sleep"]),
        "HP": max(randint(lvl, lvl + 5), randint(lvl + 10, lvl + 20)),
        "ATK": max(randint(max(1, lvl), lvl + 3), randint(lvl + 4, lvl + 6)),
        "DEF": max(randint(max(1, lvl), lvl + 3), randint(lvl + 4, lvl + 6)),
        "char": name[0].upper()
    }

### ---- GAME FUNCTIONALITY ----
def step(pos, direction, lvl):
    global LEVELS, ACTLAYER
    x2, y2 = pos[0] + direction[0], pos[1] + direction[1]
    if 0 > x2 or x2 >= len(LEVELS[lvl][0]) or 0 > y2 or y2 >= len(LEVELS[lvl]): return "Bump\n" 
    piece = get(ACTLAYER[lvl], pos)
    nxt = get(ACTLAYER[lvl], (x2, y2))
    floor = get(LEVELS[lvl], (x2, y2))
    if floor in TANG: return "Bump\n"
    if nxt != EMPTY:
        return collide(pos, (x2, y2), lvl)
    put(ACTLAYER[lvl], pos, EMPTY)
    put(ACTLAYER[lvl], (x2, y2), piece)
    if piece != PLAYER:
        ACTORS[lvl][(x2, y2)] = ACTORS[lvl].pop(pos)
    return ""

def collide(pos1, pos2, lvl): #pos1 is moving onto pos2
    global LEVELS, ACTLAYER, SCORE, HP, ACTORS, INV, NME
    data = ""
    p1, p2 = get(ACTLAYER[lvl], pos1), get(ACTLAYER[lvl], pos2)
    if p1 == PLAYER and p2 in [DOOR, GOLD]: # note to slef, door on actlayer
        put(ACTLAYER[lvl], pos2, EMPTY)
    if p1 == PLAYER and p2 == GOLD:
        SCORE += 10
        data += "Got 10 gold\n"
        put(ACTLAYER[lvl], pos1, EMPTY)
        put(ACTLAYER[lvl], pos2, p1)
    if p1 == PLAYER and p2 in ARMOR + STAFF + CONSUME:
        item = ACTORS[lvl][pos2]
        data += "Got " + item["name"]
        INV.append(item)
        put(ACTLAYER[lvl], pos1, EMPTY)
        put(ACTLAYER[lvl], pos2, p1)
    if p1 == PLAYER and p2 in FIGHTABLE:
        enemy = ACTORS[lvl][pos2]
        enemy['state'] = 'agg'
        NME = enemy
        roll = randint(0, 100)
        if roll < 15:
            data += "You miss the " + enemy['name']
            data += "[ " + str(enemy['HP']) + " ]\n"
        else:
            data += "You hit the " + enemy['name']
            data += "[ " + str(enemy['HP']) + " ]\n"
            if randint(0, 80):
                dmg = max(ATK - enemy['DEF'], 1)
            else:
                data += "critical hit!\n"
                dmg = 100
            enemy['HP'] -= dmg
    if p1 in FIGHTABLE and p2 == PLAYER:
        enemy = ACTORS[lvl][pos1]
        NME = enemy
        roll = randint(0, 100)
        if roll < 15:
           data += "The " + enemy['name'] + " misses you\n"
        else:
           data += "The " + enemy['name'] + " hits you\n"
           dmg = max(enemy['ATK'] - DEF, 1)
           HP -= dmg
    if p1 in POT and p2 in FIGHTABLE:
        data += applypotion(ACTORS[LEVEL][pos1], enemy=ACTORS[LEVEL][pos2])
        ACTORS[LEVEL].pop(pos1)
        put(ACTLAYER[LEVEL], pos1, EMPTY)
    elif p1 in GETTABLE and p2 in FIGHTABLE:
        item, enemy = ACTORS[LEVEL][pos1], ACTORS[LEVEL][pos2]
        if "stat" in item: enemy["HP"] -= item["stat"]
        elif "uses" in item: enemy["HP"] -= item["uses"]
        ACTORS[LEVEL].pop(pos1)
        put(ACTLAYER[LEVEL], pos1, EMPTY)
    return data

def directto(pos1, pos2):
    """the direction you should go to be closer from point 1 to point 2"""
    x1, y1 = pos1
    x2, y2 = pos2
    if x1 - x2 == 0: return (0, 1) if (y1 - y2) < 0 else (0, -1)
    elif y1 - y2 == 0: return (1, 0) if (x1 - x2) < 0 else (-1, 0)
    else:
        slope = max(abs(x1 - x2), abs(y1 - y2)) / min(abs(x1 - x2), abs(y1 - y2))
        if abs(x1 - x2) > abs(y1 - y2):
            if (x1 - x2) % slope: return (1, 0) if (x1 - x2) < 0 else (-1, 0)
            else: return (0, 1) if (y1 - y2) < 0 else (0, -1)
        elif abs(x1 - x2) <= abs(y1 - y2):
            if (y1 - y2) % slope: return (0, 1) if (y1 - y2) < 0 else (0, -1)
            else: return (1, 0) if (x1 - x2) < 0 else (-1, 0)

def insight(lvl, position1, position2, dist=10):
    if False in [position1, position2]: return False
    if getdist(position1, position2) > dist: return False
    x1, y1 = position2; x2, y2 = position1
    flag = False
    while (x1, y1) != (x2, y2):
        d = directto((x1, y1), (x2, y2))
        if d[0] and (get(LEVELS[lvl], (x1 + d[0], y1)) in TANG or get(ACTLAYER[lvl], (x1 + d[0], y1)) in TANG):
            d = (0, 1) if (y1 - y2) < 0 else (0, -1)
            if not flag: flag = True
            else: return False
        elif d[1] and (get(LEVELS[lvl], (x1, y1 + d[1])) in TANG or get(ACTLAYER[lvl], (x1, y1 + d[1])) in TANG):
                d = (1, 0) if (x1 - x2) < 0 else (-1, 0)
                if not flag: flag = True
                else: return False
        x1, y1 = x1 + d[0], y1 + d[1]
        if (get(LEVELS[lvl], (x1, y1)) in TANG or get(ACTLAYER[lvl], (x1, y1)) in TANG) and (x1, y1) != (x2, y2):
            return False
    return True

def getlit(lights, lvl):  # 420 blaze it
    global INLIGHT
    s = ""
    for y, line in enumerate(LEVELS[lvl]):
        for x, piece in enumerate(line):
            if (x, y) not in INLIGHT[lvl]:
                for light, dis in lights:
                    if insight(lvl, light, (x, y), dis):
                        INLIGHT[lvl].add((x, y))
            if (x, y) in INLIGHT[lvl]: s += piece
            else: s += DARK
        s += "\n"
    return s.splitlines()

def solvable(board):
    try:
        entry = find(board, UPSTAIR)
        exit = find(board, DWNSTR)
        infected = [entry, ]
        check = [entry, ]
        while check:
            if exit in infected: return infected
            x, y = check.pop()
            for nbr in nbrs(x, y):
                if nbr not in infected and get(board, nbr) not in TANG:
                    infected.append(nbr)
                    check.append(nbr)
        return False
    except IndexError:
        return False

def newfloor(entry, lvl):
    board = (STONE * max(min(randint(20, 20 + (3 * lvl)), 110), entry[0] + 2) + "\n") * max(min(randint(15, 15 + (1 * lvl)), 37), entry[1] + 2)
    board = board.splitlines()
    insert(board, [EMPTY * (len(board[0]) - 2)] * (len(board)-2), (1, 1))
    exit = randint(1, len(board[0])-2), randint(2, len(board)-2)
    while getdist(entry, exit) < len(board[0]) / 2:
        exit = randint(1, len(board[0])-2), randint(2, len(board)-2)
    put(board, exit, DWNSTR)
    put(board, entry, UPSTAIR)
    return board

def makeroom(board, layer2, position, dimensions, lvl):
    w, h = dimensions
    room = (((WALL * w) + "\n") * h).splitlines()
    room_layer2 = (((EMPTY * w) + "\n") * h).splitlines()
    insert(room, [FLOOR * (w - 2)] * (h - 2), (1, 1))
    for x in range(randint(2, 4)):
        dor = choice([n for n in allof(room, WALL)])
        put(room, dor, FLOOR)
        put(room_layer2, dor, DOOR)
    insert(board, room, position)
    insert(layer2, room_layer2, position)

def pathfind(board):
    empties = [x for x in allof(board, EMPTY)]
    while empties:
        solv = solvable(board)
        if solv:
            for emp in empties:
                if emp not in solv: 
                    empties.remove(emp)
                    put(board, emp, STONE)
            pos = choice(empties)
            put(board, pos, STONE)
        solv = solvable(board)
        if not solv: put(board, pos, FLOOR)
        animate(board, 0.001, data=pos, debug=True)
        empties = [x for x in allof(board, EMPTY)]

    for pos in allof(board, FLOOR): put(board, pos, EMPTY)
    return board

def scrub(board, limit=3):
    slots = findsub(board, [STONE * limit] * limit)
    while slots:
        x, y = choice(slots)
        slot = getsub(board, (x, y), (limit, limit))
        for n in range(6): put(slot, choice([stone for stone in allof(slot, STONE)],), EMPTY)
        insert(board, slot, (x, y))
        animate(board, 0.001, debug=True)
        slots = findsub(board, [STONE * limit] * limit)
    return board

def refine(board, layer2, lvl):
    room = findsub(board, [STONE * 6] * 6)
    if room: makeroom(board, layer2, choice(room), (6, 6), lvl)
    sub = getsub(board, (1, 1), (len(board[0]) - 2, len(board) - 2))
    b = scrub(sub)
    for stone in allof(b, STONE):
        try:
            if get(b, (stone[0] + 1, stone[1])) == get(b, (stone[0] - 1, stone[1])) == EMPTY:
                put(b, stone, "+")
            if get(b, (stone[0], stone[1] + 1)) == get(b, (stone[0], stone[1] - 1)) == EMPTY:
                put(b, stone, "+")
        except IndexError: continue
    insert(board, b, (1, 1))
    return board

def populate(board, lvl):
    global ACTLAYER, ACTORS
    empties = [x for x in allof(board, EMPTY)]
    # place enemies
    enemies = [makeenemy(lvl) for x in range(randint(min(3+lvl, 15), min(5+lvl, 25)))]
    for enemy in enemies:
        if not empties: return board
        pos = empties.pop(randint(0, len(empties)-1))
        ACTORS[lvl][pos] = enemy
        put(ACTLAYER[lvl], pos, enemy['char'])
        animate(board, .001, layer2=ACTLAYER[lvl], data=len(ACTORS[lvl]), debug=True)
    # place gold
    for x in range(5+lvl, 20+lvl):
        if not empties: return board
        pos = empties.pop(randint(0, len(empties)-1))
        put(ACTLAYER[lvl], pos, GOLD)
        animate(board, .001, layer2=ACTLAYER[lvl], debug=True)
    # fill room
    items = []; roll = randint(0, 100)
    room = [x for x in allof(board, FLOOR)]
    for pos in room:
        if get(ACTLAYER[lvl], pos) != EMPTY: room.remove(pos)
    if roll > 45: items.append(makeitem(STAFF, lvl))
    if roll < 55: items.append(makeitem(ARMOR, lvl))
    if 50 <= roll <= 51: items = []
    for item in items:
        if not room: break
        pos = choice(room)
        room.remove(pos)
        put(ACTLAYER[lvl], pos, item["char"])
        ACTORS[lvl][pos] = item
    for pos in room:
        if not randint(0, 5):
            pot = makepotion()
            put(ACTLAYER[lvl], pos, pot['char'])
            ACTORS[lvl][pos] = pot
    # potions
    for pos in empties:
        if get(ACTLAYER[lvl], pos) != EMPTY: 
            empties.remove(pos)
            continue
        if not randint(0, 50):
            pot = makepotion()
            put(ACTLAYER[lvl], pos, pot['char'])
            ACTORS[lvl][pos] = pot
        elif not randint(0, 250):
            axe = makepickaxe()
            put(ACTLAYER[lvl], pos, axe['char'])
            ACTORS[lvl][pos] = axe
    return board

def dequip(item):
    global ATK, DEF
    if EQUIP["weapn"] is item:
        INV.append(item)
        EQUIP["weapn"] = None
        ATK -= item['stat']
    elif EQUIP["armor"] is item:
        INV.append(item)
        EQUIP["armor"] = None
        DEF -= item['stat']
    else:
        return "not equipted"

def equip(item):   
    global ATK, DEF, INV
    if item not in INV:
        return "do not have " + item["name"]
    if item['char'] not in WEAP + ARMOR:
        return item['name'] + " not equipable"
    elif item['char'] in WEAP:
        if EQUIP["weapn"]: dequip(EQUIP['weapn'])
        INV.remove(item)
        EQUIP["weapn"] = item
        ATK += item["stat"]
    elif item['char'] in ARMOR:
        if EQUIP["armor"]:
            dequip(EQUIP['armor'])
        INV.remove(item)
        EQUIP["armor"] = item
        DEF += item["stat"]
    return "Equipted " + item["name"]

def applypotion(pot, enemy=None):
    global INV, ATK, DEF, HP, INLIGHT, LEVEL
    ret = "It was a potion of "
    fn = pot['fn']
    if fn == "+ STR":
        if enemy:
            enemy["ATK"] += randint(1, 2)
        else:
            ATK += randint(1, 2)
        return ret + "power!"
    elif fn == "+ DEF":
        if enemy:
            enemy["DEF"] += randint(1, 2)
        else:
            DEF += randint(1, 2)
        return ret + "fortitude!"
    elif fn == "+ HP":
        if enemy:
            enemy['HP'] += randint(5, 15)
        else:
            HP += randint(5, 15)
        return ret + "healing!"
    elif fn == "- STR":
        if enemy:
            enemy["ATK"] = max(1, enemy["ATK"] - randint(1, 2))
        else:
            ATK = max(1, ATK - randint(1, 2))
        return ret + "weakness!"
    elif fn == "- DEF":
        if enemy:
            enemy["DEF"] = max(1, enemy["DEF"] - randint(1, 2))
        else:
            DEF = max(1, DEF - randint(1, 2))
        return ret + "flimsyness!"
    elif fn == "PSN":
        if enemy:
            enemy['HP'] -= randint(5, 15)
        else:
            HP -= randint(5, 15)
        return ret + "poison! Yowch!"
    elif fn == "VIS":
        if enemy:
            enemy["state"] = "sleep"
        else:
            for x in range(len(LEVELS[LEVEL][0])):
                for y in range(len(LEVELS[LEVEL])):
                    INLIGHT[LEVEL].add((x, y))
        return ret + "vision!"
    elif fn == "WARP":
        if enemy:
            for pos in ACTORS[LEVEL]:
                if enemy is ACTORS[pos]:
                    put(ACTLAYER[LEVEL], pos, EMPTY)
                    put(ACTLAYER[LEVEL], find(LEVELS[LEVEL], DWNSTR), enemy["char"])
                    break
        else:
            put(ACTLAYER[LEVEL], find(ACTLAYER[LEVEL], PLAYER), EMPTY)
            put(ACTLAYER[LEVEL], find(LEVELS[LEVEL], DWNSTR), PLAYER)
        return ret + "teleportation!"

def boardsturn(lvl):
    ret = ""
    actors = ACTORS[lvl].keys()
    for pos in actors:
        actor = ACTORS[lvl][pos]
        if "state" in actor:
            if actor['HP'] <= 0:
                ACTORS[lvl].pop(pos)
                put(ACTLAYER[lvl], pos, EMPTY)
                ret += "The "+actor["name"]+" dies\n"
                continue
            if actor["state"] == "sleep": pass
            elif actor['state'] == "agg" and pos in INLIGHT[lvl]:
                ret += step(pos, directto(pos, find(ACTLAYER[lvl], PLAYER)), lvl)
            elif actor['state'] == 'hide': pass
    return ret

def get_stats(): #for the sake of gamemode.py
    return {
        "HP": HP, "ATK": ATK, "DEF": DEF, "GOLD": SCORE,
        "Weapon": EQUIP["weapn"], "Armor": EQUIP["armor"]
    }
def get_inlight(): return INLIGHT
def get_nme(): return NME if NME is not None and NME["HP"] > 0 else None

def dig_dungeon(floors=15):
    global ACTLAYER, INLIGHT, ACTORS, LEVELS, END
    LEVEL = 0
    for x in range(floors + 1):
        ACTORS.append({})
    for x in range(floors + 1):
        INLIGHT.append(set())

    axe = makepickaxe()
    ACTORS[LEVEL][(5, 2)] = axe
    put(ACTLAYER[LEVEL], (5, 2), axe['char']) 
    while floors:
        animate(["Digging Dungeon...", "floor " + str(LEVEL)], 0)
        floors -= 1
        entry = find(LEVELS[LEVEL], DWNSTR)
        LEVEL += 1
        board = newfloor(entry, LEVEL)
        board = pathfind(board)
        ACTLAYER.append([" " * len(board[0])] * len(board))
        board = refine(board, ACTLAYER[LEVEL], LEVEL)
        board = populate(board, LEVEL)
        LEVELS.append(board)
    entry = find(LEVELS[-1], DWNSTR)
    LEVELS.append([" " * (entry[0] + len(END[0]))] * (entry[1] + len(END)))
    insert(LEVELS[-1], END, (entry[0] - 3, entry[1] - 2))
    ACTLAYER.append([" " * len(LEVELS[-1][0])] * len(LEVELS[-1]))

def update_scoreboard(NAME, lvl):
    if len(NAME) > 10:
        NAME = NAME[0:10]
    if not NAME:
        NAME = "You"
    myentry = [NAME, str(lvl), str(SCORE)]
    try:
        with open("scoreboard.pyon", "r") as SCOREBOARD:
            scoreboard = eval(SCOREBOARD.read())
    except IOError:
        scoreboard = []
    idx = 0
    for entry in scoreboard:
        if int(entry[1]) < int(myentry[1]):
            break
        elif int(entry[1]) == int(myentry[1]) and int(entry[2]) < int(myentry[2]):
            break
        idx += 1
    scoreboard.insert(idx, myentry)
    with open("scoreboard.pyon", "w") as SCOREBOARD:
        SCOREBOARD.write(repr(scoreboard[:10]))
    print("   ### HALL OF FAME ###")
    print("  Name    |  Level, Score")
    print("----------+---------------")
    for entry in scoreboard[:10]:
        s = entry[0] + " " * (10 - len(entry[0])) + "| "
        s += entry[1] + " " * (5 - len(entry[1])) + ", " + entry[2]
        print(s)

if __name__ == """__main__""": #Badly needs cleaning...
    board = LEVELS[LEVEL]
    clear()
    floors = raw_input(colored("""Welcome to the Dungeon of LURD                   ,
COMMANDS:                                        ,
. l: Left  . s: Stairs      . q: Quit            ,
. u: Up    . i: Inventory   . c: Consume(potions),
. r: Right . e: Equip       . p: Pickaxe         ,
. d: Down  . h: Help (thats this)                ,
                                                 ,
SPRITES:                                         ,
. @: You   . >: Downward   . /: Weapon           ,
. #: Stone . <: Upward     . [: Armor            ,
. +: Wall  . {: Pickaxe    .  : Empty            ,
. =: Door  . *: Gold       . .: Floor            ,
                                                 ,
Time to build the dungeon.                       ,
How many levels deep? (blank for 15): """))
    if floors:
        dig_dungeon(int(floors))
    else:
        dig_dungeon()
    data = "The Jeorney Begins"
    animate(getlit([(find(ACTLAYER[LEVEL], PLAYER), 10)], LEVEL), .300, layer2=ACTLAYER[LEVEL], data=data)
    while HP > 0:
        if LEVEL > len(LEVELS): break
        cmds = raw_input(": ").split()[::-1]
        while cmds:
            data = "LEVEL: " + str(LEVEL) + " GOLD: " + str(SCORE)
            data += "\nHP: " + str(HP) + " Weapon: "
            if EQUIP['weapn']:
                data += EQUIP['weapn']['name']
            else:
                data += "None"
            if EQUIP['armor']:
                data += " Armor: " + EQUIP['armor']['name'] + "\n"
            else:
                data += " Armor: None\n"
            cmd = cmds.pop()
            if cmd == "DEBUG": pdb.set_trace()
            if cmd in ["q", "quit"]: 
                if raw_input("are you sure? you will die...") in ["y", "yes"]: HP = 0
            if cmd in ["h", "help"]: data += HELP
            if cmd in D: data += step(find(ACTLAYER[LEVEL], PLAYER), D[cmd], LEVEL)
            if cmd in ["i", "inv"]:
                if INV: data += "refrence by number\n"
                for n, item in enumerate(INV): data += str(n) + ": " + item["name"] + "\n"
            if cmd in ["e", "equip"]:
                if cmds: eq = cmds.pop()
                else: eq = raw_input("equip what? : ")
                for n, item in enumerate(INV):
                    if eq in [item['name'], str(n)]: 
                        if "stat" not in item: data += "thats not equipable"
                        else: data += str(equip(item))
                        break
                else: data += "Nothing found under " + eq 
            if cmd in ["c", "consume"]:
                if cmds: c = cmds.pop()
                else: c = raw_input("consume what : ")
                for n, item in enumerate(INV):
                    if c in [item['name'], str(n)]:
                        if "fn" not in item: data += "thats not consumable"
                        else:
                            INV.remove(item) 
                            data += str(applypotion(item))
                        break
                else: data += "Nothing found under " + c
            if cmd in ["p", "pickaxe"]:
                for item in INV:
                    if item['name'] == "Pickaxe":
                        axe = item
                        break
                else:
                    data += "No  pickaxe found\n"
                if cmds: d = cmds.pop()
                else: d = raw_input("What direction? :")
                if d in D:
                    pos = find(ACTLAYER[LEVEL], PLAYER)
                    delt = (pos[0] + D[d][0], pos[1] + D[d][1])
                    item = get(LEVELS[LEVEL], delt)
                    if item == WALL:
                        put(LEVELS[LEVEL], delt, EMPTY)
                    if item == STONE:
                        put(LEVELS[LEVEL], delt, WALL)
                    if item != EMPTY:
                        if axe['uses']: axe['uses'] -= 1
                        else:
                            if randint(0, 1): INV.remove(axe)
                            data += "The pickaxe broke" 
            if cmd in ["s", "stairs"]:
                pos = find(ACTLAYER[LEVEL], PLAYER)
                under = get(LEVELS[LEVEL], pos)
                if under == UPSTAIR:
                    put(ACTLAYER[LEVEL], pos, EMPTY)
                    LEVEL -= 1
                    if LEVEL < 0:
                        print("Farewell traveler")
                        HP = 0
                elif under == DWNSTR:
                    LEVEL += 1
                    put(ACTLAYER[LEVEL], pos, PLAYER)
            animate(getlit([(find(ACTLAYER[LEVEL], PLAYER), 10)],  LEVEL), .15, layer2=ACTLAYER[LEVEL], data=data)
            data += str(boardsturn(LEVEL))
            animate(getlit([(find(ACTLAYER[LEVEL], PLAYER), 10)], LEVEL), .15, layer2=ACTLAYER[LEVEL], data=data)

    clear()
    print("You made it to level " + str(LEVEL))
    print("You got " + str(SCORE) + " gold")
    sleep(2)
    NAME = raw_input("Name?: ")
    clear()
    update_scoreboard(NAME, LEVEL)
