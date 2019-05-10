"""
rlike.py a vanilla python turn based roguelike
board is splitlines syntax, list of strings
board[y][x] for example

PS: I hate pep8

TO DO LIST:
x enemy implementation
     / enemy turn (brain)
/ fighting implementation
x armor item implementation
x UNDER player duplication bug fix
     bug was in step(), was placing
     what was under player with 'under' flag on
x write line-of-sight function
     looks great! :)
x darken level (so you only see where theres light)
     decided to keep level lit once seen
. batteries
. flashlight
. pickaxe
. drill
. throw command
. potions
. scrolls

KNOWN BUGS:
? sometimes find(board, PLAYER) is false which makes no sense
! GOLD just moved like agg enemy??? how???
      . I think an enemy moves onto gold and because they're both
      in ACT they transfer
Ongoing:
. clean everything the f up
. try to optomize level builder
Also:
x added gold
x items spawn in rooms, 40% sword, 40% armor, 8% both, 2% nither
"""
from __future__ import print_function, unicode_literals
import os
import sys
from random import randint, choice
from time import sleep
from math import sqrt
DEBUG = "-d" in sys.argv

PLAYER = "@"
DWNSTR = ">"
UPSTAIR = "<"
STONE = "#"
WALL = "+"
DOOR = "="
EMPTY = " "
FLOOR = "."
DARK = "\\"

GOLD = "*"
STAFF = "/"
PICKAXE = "{"
BOW = ")"
BATTERY = "%"
ARMOR = "["

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

        DARK: "\033[0m",
        "\n": "\033[0m",
        "footer": "\033[0m",
}

CONSUME = "bcdfghjklmnprstvwxyz" + BATTERY
WEAP = STAFF + BOW
FIGHTABLE = "BCDFGHJKLMNPRSTVWXYZ"
TANG = STONE + WALL + DOOR  # Tangible
ACT = PLAYER + DOOR + FIGHTABLE + GOLD
GETTABLE = WEAP + ARMOR + CONSUME

INLIGHT = [set()]

START = """###########
#    R*   #
#  <   >  #
#    @    #
#         #
###########""".splitlines()

END = """##########
#    Wow #
#  <     #
# .,.,., #
# TheEnd #
##########""".splitlines()

HELP = """
COMMANDS:                                        ,
. L: Left  . S: Stairs . Q: Quit                 ,
. U: Up    . G: Get    . Un: check Under         ,
. R: Right . Dr: Drop  . Inv: check Inventory    ,
. D: Down  . Eq: Equip . H: Help (thats this)    ,
                                                 ,
SPRITES:                                         ,
. @: You   . >: Downward   . /: Weapon           ,
. #: Stone . <: Upward     . [: Armor            ,
. +: Wall      staircase   .  : Empty            ,
. =: Door  . *: Gold       . .: Floor            ,

"""

LEVELS = [START]
LEVEL = 0
SCORE = 0

# these are a dictionary of names and info for each level
ENEMIES = [{((5, 1), "R"): {
        "name": "Ralph",
        "type": "agg",
        "HP": 100,
        "ATK": 3,
        "DEF": 3,
        "char": "R",
}}]
UNDER = [{(5, 3): [" "], (5, 1): [" "]}]
ITEMS = [{}]

INV = []
HP = 50
ATK = 1
DEF = 1
EQUIP = {
        "weapn": None,
        "armor": None
}

#  Name maker, specialized to make silly sounding names like biffy and pulddigy
vowel = "aeiou"
const = "bbbcdddfffggghjklllmmnnppprstttvwwxyyyyz"
special = "bdfglp"


def makename():
        roll = randint(0, 100)
        if roll < 15:
                return choice(const) + choice(vowel) + (
                        choice(special) * 2) + "y"
        if roll < 50:
                return choice(const) + choice(vowel) + choice(special) + (
                        choice(special) * 2
                ) + choice(vowel) + choice(special) + "y"
        if roll < 65:
                return choice(const) + choice(
                        vowel) + choice(const) + choice(vowel) + "ly"
        if roll < 80:
                return choice(const) + choice(
                        special) + choice(vowel) + choice(
                                vowel) + choice(special) + choice(special)
        return choice(special) + choice(vowel) + choice(
                special) + choice(special)


def makeitem(ch, lvl):
        name = makename()
        if ch == STAFF:
                name = "Sword of " + name
        elif ch == ARMOR:
                name = "Suit of " + name + " Armor"
        return {
                "name": name,
                "stat": lvl + randint(-2, 10),
                "char": ch,
        }


def makeenemy(lvl):
        name = makename()
        return {
                "name": name,
                "type": choice(["agg", "hide", "sleep"]),
                "HP": max(2, lvl + randint(-5, 10)),
                "ATK": max(2, lvl + randint(-5, 5)),
                "DEF": max(2, lvl + randint(-5, 5)),
                "char": name[0].upper()
        }


def get(board, position): return board[position[1]][position[0]]


def getsub(board, position, dimensions):
        b = ""
        for y in range(dimensions[1]):
                for x in range(dimensions[0]):
                        b += get(board, (position[0] + x, position[1] + y))
                b += "\n"
        return b.splitlines()


def put(board, position, piece, under=False, lvl=None):
        x, y = position
        if under:
                if position in UNDER[lvl]:
                        UNDER[lvl][position].append(get(board, position))
                else:
                        UNDER[lvl][position] = [get(board, position)]
        board[y] = board[y][:x] + piece + board[y][x + 1:]


def getdist(p1, p2): return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def clear(): os.system("clear || cls")


def animate(board, miliseconds, debug=False, data=False):
        if debug and not DEBUG:
                return
        clear()
        printb(board)
        if data:
                print(data)
        sleep(miliseconds)


def colored(st, menu=False):
        ret = ""
        for p in st:
                if p == DARK and not menu:
                        ret += COLORS[p] + EMPTY
                elif p in COLORS:
                        ret += COLORS[p] + p
                elif p in FIGHTABLE and not menu:
                        ret += COLORS["ENEMY"] + p
                else:
                        ret += COLORS[EMPTY] + p
                ret += COLORS['footer']
        return ret + COLORS['footer']


def printb(board): print(colored("\n".join(board)))


def find(board, piece):
        Y = 0
        while not (piece in board[Y]):
                Y += 1
                if Y >= len(board):
                        return False
        return board[Y].index(piece), Y


def findall(board, piece):
        for y, line in enumerate(board):
                for x, pce in enumerate(line):
                        if pce == piece:
                                yield x, y


def insert(board, sub, position):
        for y, line in enumerate(sub):
                for x, piece in enumerate(line):
                        put(board,
                            (position[0] + x, position[1] + y), sub[y][x])


def bisequal(board1, board2):
        try:
                for y, line in enumerate(board1):
                        for x, piece in enumerate(line):
                                if piece != board2[y][x]:
                                        return False
                return True
        except IndexError:
                return False


def checkfor(board, sub):
        checklist = findall(board, sub[0][0])
        ret = []
        for x, y in checklist:
                try:
                        if bisequal(getsub(board, (x, y),
                                           (len(sub[0]), len(sub))), sub):
                                ret.append((x, y))
                except IndexError:
                        continue
        return ret


def step(board, position, direction, under=False, lvl=0):
        x2, y2 = position[0] + direction[0], position[1] + direction[1]
        nxt = get(board, (x2, y2))
        piece = get(board, position)
        if (piece in ACT) and (nxt in ACT):
                return collide(board, position, (x2, y2), LEVEL)
        if nxt in TANG:
                return "bump"
        if position not in UNDER[lvl] or not UNDER[lvl][position]:
                UNDER[lvl][position] = [EMPTY]
        put(board, position, UNDER[lvl][position].pop())
        put(board, (x2, y2), piece, under=under, lvl=lvl)
        return ""


def collide(board, pos1, pos2, lvl):
        global SCORE, ENEMIES, HP
        data = ""
        p1, p2 = get(board, pos1), get(board, pos2)
        if p1 == PLAYER and p2 in [DOOR, GOLD]:
                if pos2 in UNDER:
                        put(board, pos2, UNDER[pos2], under=True, lvl=lvl)
                else:
                        put(board, pos2, EMPTY, under=True, lvl=lvl)
        if p1 == PLAYER and p2 == GOLD:
                SCORE += 10
                data += "got 10 gold\n"
                put(board, pos1, UNDER[lvl][pos1].pop())
                put(board, pos2, p1, under=True, lvl=lvl)
        if p1 == PLAYER and p2 in FIGHTABLE and (pos2, p2) in ENEMIES[lvl]:
                enemy = ENEMIES[lvl][(pos2, p2)]
                enemy['type'] = "agg"
                roll = randint(0, 100)
                if roll < 15:
                        data += "you miss the " + enemy['name']
                        data += "[ " + str(enemy['HP']) + " ]\n"
                else:
                        data += "you hit the " + enemy['name']
                        data += "[ " + str(enemy['HP']) + " ]\n"
                        if randint(0, 50):
                                dmg = max(ATK - enemy['DEF'], 1)
                        else:
                                data += "critical hit!\n"
                                dmg = 100
                        enemy['HP'] -= dmg
        if p1 in FIGHTABLE and (pos1, p1) in ENEMIES[lvl] and p2 == PLAYER:
                enemy = ENEMIES[lvl][(pos1, p1)]
                roll = randint(0, 100)
                if roll < 15:
                        data += "the " + enemy['name'] + " misses you\n"
                else:
                        data += "the " + enemy['name'] + " hits you\n"
                        dmg = max(enemy['ATK'] - DEF, 1)
                        HP -= dmg
        if p1 in FIGHTABLE and (pos1, p1) in ENEMIES[lvl] and p2 != PLAYER:
                return "bump"
        return data


def directto(pos1, pos2):
        """the direction you should go to be closer from point 1 to point 2"""
        x1, y1 = pos1
        x2, y2 = pos2
        if x1 - x2 == 0:
                return (0, 1) if (y1 - y2) < 0 else (0, -1)
        elif y1 - y2 == 0:
                return (1, 0) if (x1 - x2) < 0 else (-1, 0)
        else:
                slope = max(
                        abs(x1 - x2), abs(y1 - y2)
                ) / min(
                        abs(x1 - x2), abs(y1 - y2)
                )
                if abs(x1 - x2) > abs(y1 - y2):
                        if (x1 - x2) % slope:
                                return (1, 0) if (x1 - x2) < 0 else (-1, 0)
                        else:
                                return (0, 1) if (y1 - y2) < 0 else (0, -1)
                elif abs(x1 - x2) <= abs(y1 - y2):
                        if (y1 - y2) % slope:
                                return (0, 1) if (y1 - y2) < 0 else (0, -1)
                        else:
                                return (1, 0) if (x1 - x2) < 0 else (-1, 0)


def insight(board, position1, position2, dist=10):
        if False in [position1, position2]:
                return False
        if getdist(position1, position2) > dist:
                return False
        x1, y1 = position2
        x2, y2 = position1
        flag = False
        while (x1, y1) != (x2, y2):
                d = directto((x1, y1), (x2, y2))
                if d[0] and get(board, (x1 + d[0], y1)) in TANG:
                        d = (0, 1) if (y1 - y2) < 0 else (0, -1)
                        if not flag:
                                flag = True
                        else:
                                return False
                elif d[1] and get(board, (x1, y1 + d[1])) in TANG:
                        d = (1, 0) if (x1 - x2) < 0 else (-1, 0)
                        if not flag:
                                flag = True
                        else:
                                return False
                x1, y1 = x1 + d[0], y1 + d[1]
                if get(board, (x1, y1)) in TANG and (x1, y1) != (x2, y2):
                        return False
        return True


def getlit(board, lights, lvl):  # 420 blaze it
        global INLIGHT
        s = ""
        for y, line in enumerate(board):
                for x, piece in enumerate(line):
                        if (x, y) not in INLIGHT[lvl]:
                                for light, dis in lights:
                                        if insight(board, light, (x, y), dis):
                                                INLIGHT[lvl].add((x, y))
                        if (x, y) in INLIGHT[lvl]:
                                s += piece
                        else:
                                s += DARK
                s += "\n"
        return s.splitlines()


def solvable(board):
        try:
                entry = find(board, UPSTAIR)
                exit = find(board, DWNSTR)
                infected = [entry, ]
                check = [entry, ]
                while check:
                        if exit in infected:
                                return infected
                        x, y = check.pop()
                        for nbr in [(x+1, y), (x-1, y), (x, y-1), (x, y+1)]:
                                if (nbr not in infected and get(
                                                board, nbr) not in TANG):
                                        infected.append(nbr)
                                        check.append(nbr)
                return False
        except IndexError:  # walk off ledge
                return False


def newfloor(entry, lvl):
        board = (
                STONE * max(min(randint(20, 20 + (3 * lvl)), 110),
                            entry[0] + 2) + "\n"
        ) * max(min(randint(15, 15 + (1 * lvl)), 37), entry[1] + 2)
        board = board.splitlines()
        insert(board, [EMPTY * (len(board[0]) - 2)] * (len(board)-2), (1, 1))
        exit = randint(1, len(board[0])-2), randint(2, len(board)-2)
        while getdist(entry, exit) < len(board[0]) / 2:
                exit = randint(1, len(board[0])-2), randint(2, len(board)-2)
        put(board, exit, DWNSTR)
        put(board, entry, UPSTAIR)
        return board


def makeroom(board, position, dimensions, lvl):
        w, h = dimensions
        room = (((WALL * w) + "\n") * h).splitlines()
        insert(room, [FLOOR * (w - 2)] * (h - 2), (1, 1))
        for x in range(randint(2, 4)):
                put(room, choice([n for n in findall(room, WALL)]), DOOR)
        insert(board, room, position)


def pathfind(board):
        """expects board with entrence, and exit and all empties"""
        # can definetly optomize, thinking, check only what solvable returns?
        empties = checkfor(board, EMPTY)
        while empties:
                while solvable(board) and empties:
                        pos = choice(empties)
                        insert(board, STONE, pos)
                        animate(board, 0.01, data=pos, debug=True)
                        empties = checkfor(board, EMPTY)
                put(board, pos, FLOOR)
        for pos in findall(board, FLOOR):
                put(board, pos, EMPTY)
        return board


def scrub(board, limit=3):
        # hopefully i'll optomize this in a streak of brilliance
        slots = checkfor(board, [STONE * limit] * limit)
        while slots:
                slot = choice(slots)
                x, y = slot
                slot = getsub(board, slot, (limit, limit))
                for n in range(6):
                        put(slot, choice(
                                [stone for stone in findall(slot, STONE)]
                        ), EMPTY)
                insert(board, slot, (x, y))
                animate(board, .001, debug=True)
                slots = checkfor(board, [STONE * limit] * limit)

        for stone in findall(board, STONE):
                x, y = stone
                try:
                        nbrs = sum([get(board, pos) == EMPTY for pos in [
                                (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)
                        ]])
                except IndexError:
                        nbrs = 0
                animate(board, .001, debug=True)
                if nbrs in [2, 3] and randint(0, 20) < 8:
                        put(board, stone, EMPTY)
        return board


def refine(board, lvl):
        sub = getsub(board, (1, 1), (len(board[0]) - 2, len(board) - 2))
        room = checkfor(sub, [STONE * 6] * 6)
        if room:
                makeroom(sub, choice(room), (6, 6), lvl)
        b = scrub(sub)
        for stone in findall(b, STONE):
                try:
                        if get(b, (stone[0] + 1, stone[1])) == get(
                                        b, (stone[0] - 1, stone[1])) == EMPTY:
                                put(b, stone, "+")
                        if get(b, (stone[0], stone[1] + 1)) == get(
                                        b, (stone[0], stone[1] - 1)) == EMPTY:
                                put(b, stone, "+")
                except IndexError:
                        continue
        insert(board, b, (1, 1))
        return board


def populate(board, lvl):
        global ITEMS, ENEMIES
        empties = checkfor(board, EMPTY)
        room = checkfor(board, FLOOR)
        roll = randint(0, 100)
        # load items into room
        items = []
        if roll > 49:
                items.append(makeitem(STAFF, lvl))
        if roll < 60:
                items.append(makeitem(ARMOR, lvl))
        if 50 <= roll <= 51:
                items = []
        for item in items:
                pos = choice(room)
                room.remove(pos)
                ITEMS[lvl][(pos, item['char'])] = item
                put(board, pos, item['char'], under=True, lvl=lvl)
        # load gold
        for x in range(randint(10, 15 + 15 * (lvl > 10))):
                pos = choice(empties)
                empties.remove(pos)
                put(board, pos, GOLD, under=True, lvl=lvl)
        # load enemies
        enemies = [makeenemy(lvl) for x in range(lvl + 5, lvl + 10)]
        for enemy in enemies:
                pos = choice(empties)
                empties.remove(pos)
                ENEMIES[lvl][(pos, enemy['char'])] = enemy
                put(board, pos, enemy['char'], under=True, lvl=lvl)
        return board


def dequip(item):
        global ATK, DEF
        if EQUIP["weapn"] == item:
                INV.append(item)
                EQUIP["weapn"] = None
                ATK -= item['stat']
        elif EQUIP["armor"] == item:
                INV.append(item)
                EQUIP["armor"] = None
                DEF -= item['stat']
        else:
                return "not equipted"


def equip(item):
        global ATK, DEF
        if item not in INV:
                return "do not have " + item["name"]
        if item['char'] not in WEAP + ARMOR:
                return item['name'] + " not equipable"
        elif item['char'] in WEAP:
                if EQUIP["weapn"]:
                        dequip(EQUIP['weapn'])
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


def boardsturn(board, lvl):
        global ENEMIES
        s = ""
        for pos, ch in ENEMIES[lvl].keys():
                enemy = ENEMIES[lvl][(pos, ch)]
                x, y = pos
                if enemy["HP"] <= 0:
                        ENEMIES[lvl].pop((pos, ch))
                        if pos in UNDER[lvl]:
                                put(board, pos, UNDER[lvl][pos].pop(),
                                    under=True, lvl=lvl)
                        else:
                                put(board, pos, EMPTY, under=True, lvl=lvl)
                        s += enemy['name'] + " dies"
                        continue
                if enemy['type'] == "sleep":
                        pass
                elif enemy['type'] == "agg" and insight(board, pos,
                                                        find(board, PLAYER)):
                        pos2 = find(board, PLAYER)
                        direc = directto(pos, pos2)
                        S = step(board, pos, direc, under=True, lvl=lvl)
                        print(S)
                        if not S:
                                ENEMIES[lvl].pop((pos, ch))
                                ENEMIES[lvl][
                                        ((x + direc[0], y + direc[1]), ch)
                                ] = enemy
                        else:
                                s += S
                if enemy['type'] == "hide":
                        pass
        return s


def dig_dungeon(floors=15):
        global INLIGHT, UNDER, ENEMIES, ITEMS, LEVELS, END
        LEVEL = 0
        UNDER += [{}] * (floors + 1)
        ITEMS += [{}] * (floors + 1)
        ENEMIES += [{}] * (floors + 1)
        for x in range(floors + 1):
                INLIGHT.append(set())
        while floors:
                animate(["Digging Dungeon...", "floor " + str(LEVEL)], 0)
                floors -= 1
                LEVEL += 1
                board = pathfind(newfloor(find(LEVELS[-1], DWNSTR), LEVEL))
                board = refine(board, LEVEL)
                board = populate(board, LEVEL)
                LEVELS.append(board)

        entry = find(LEVELS[-1], DWNSTR)
        LEVELS.append([" " * (entry[0] + len(END[0]))] * (entry[1] + len(END)))
        insert(LEVELS[-1], END, (entry[0] - 3, entry[1] - 2))


board = LEVELS[LEVEL]
clear()
floors = raw_input(colored("""Welcome to the Dungeon of LURD                   ,
COMMANDS:                                        ,
. L: Left  . S: Stairs . Q: Quit                 ,
. U: Up    . G: Get    . Un: check Under         ,
. R: Right . Dr: Drop  . Inv: check Inventory    ,
. D: Down  . Eq: Equip . H: Help (thats this)    ,
                                                 ,
SPRITES:                                         ,
. @: You   . >: Downward   . /: Weapon           ,
. #: Stone . <: Upward     . [: Armor            ,
. +: Wall      staircase   .  : Empty            ,
. =: Door  . *: Gold       . .: Floor            ,
                                                 ,
Time to build the dungeon.                       ,
How many levels deep? (blank for 15): """, menu=True))
if floors:
        dig_dungeon(int(floors))
else:
        dig_dungeon()

data = "The Jeorney Begins"
animate(getlit(board, [(find(board, PLAYER), 10)], LEVEL), .300, data=data)
while HP > 0:
        if LEVEL > len(LEVELS):
                break
        cmds = raw_input(": ").split()[::-1]
        while cmds:
                data = "LEVEL: " + str(LEVEL) + " GOLD: " + str(SCORE)
                data += " \nHP: " + str(HP) + " Weapon: "
                if EQUIP['weapn']:
                        data += EQUIP["weapn"]['name']
                else:
                        data += "None"
                if EQUIP['armor']:
                        data += " Armor: " + EQUIP["armor"]["name"] + "\n"
                else:
                        data += " Armor: None\n"
                cmd = cmds.pop()
                if cmd in ["Q", "quit"]:
                        if raw_input("are you sure? you will die..."):
                                if DEBUG and raw_input("Print dungeon?"):
                                        for b in LEVELS:
                                                print()
                                                printb(b)
                                HP = 0

                if cmd in ["H", "help"]:
                        data += HELP

                if cmd in ["L", "left"]:
                        data += step(board,
                                     find(board, PLAYER), (-1, 0),
                                     under=True, lvl=LEVEL)
                if cmd in ["U", "up"]:
                        data += step(board,
                                     find(board, PLAYER), (0, -1),
                                     under=True, lvl=LEVEL)
                if cmd in ["R", "right"]:
                        data += step(board,
                                     find(board, PLAYER), (1, 0),
                                     under=True, lvl=LEVEL)
                if cmd in ["D", "down"]:
                        data += step(board,
                                     find(board, PLAYER), (0, 1),
                                     under=True, lvl=LEVEL)

                if cmd in ["Un", "under"]:
                        data += ", ".join(UNDER[LEVEL][find(board, PLAYER)])

                if cmd in ["Inv", "inventory"]:
                        if INV:
                                data += "refrence by number\n"
                        for n, item in enumerate(INV):
                                data += str(n) + ": " + item['name'] + "\n"

                if cmd in ["stats"] and DEBUG:
                        data += "Atk: " + str(ATK) + "\nDef: " + str(DEF)

                if cmd in ["???"] and DEBUG:
                        data += str((UNDER[LEVEL],
                                     ENEMIES[LEVEL], ITEMS[LEVEL]))

                if cmd in ["Eq", "equip"]:
                        if cmds:
                                eq = cmds.pop()
                        else:
                                eq = raw_input("Equipt what? : ")
                        for n, item in enumerate(INV):
                                if "stat" not in item:
                                        data += "Thats"
                                elif eq in [item['name'], str(n)]:
                                        data += str(equip(item))
                                break
                        else:
                                data += "Nothing found under " + eq

                if cmd in ["G", "get"]:
                        for piece in UNDER[LEVEL][find(board, PLAYER)]:
                                if (find(board, PLAYER), piece) in ITEMS[
                                                LEVEL]:
                                        UNDER[LEVEL][
                                                find(board, PLAYER)
                                        ].remove(piece)
                                        INV.append(ITEMS[LEVEL][
                                                (find(board, PLAYER), piece)
                                        ])
                                        data += "got " + INV[-1]['name']

                if cmd in ["W", "warp"] and DEBUG:
                        put(board, find(board, PLAYER),
                            UNDER[LEVEL][find(board, PLAYER)].pop(),
                            under=True, lvl=LEVEL)
                        put(board, find(board, DWNSTR), PLAYER,
                            under=True, lvl=LEVEL)

                if cmd in ["S", "stairs"]:
                        pos = find(board, PLAYER)
                        if pos in UNDER[LEVEL]:
                                if UPSTAIR in UNDER[LEVEL][pos]:
                                        put(board, pos,
                                            UNDER[LEVEL][pos].pop())
                                        LEVEL -= 1
                                        put(LEVELS[LEVEL], pos, PLAYER,
                                            under=True, lvl=LEVEL)
                                        if LEVEL < 0:
                                                print("Farewell traveler")
                                                quit()
                                elif DWNSTR in UNDER[LEVEL][pos]:
                                        put(board, pos,
                                            UNDER[LEVEL][pos].pop())
                                        LEVEL += 1
                                        put(LEVELS[LEVEL], pos, PLAYER,
                                            under=True, lvl=LEVEL)

                if cmd in ["Dr", "Drop"]:
                        if cmds:
                                dr = cmds.pop()
                        else:
                                dr = raw_input("Drop what? : ")
                        for n, item in enumerate(INV):
                                if dr in [item['name'], str(n)]:
                                        INV.remove(item)
                                        ITEMS[LEVEL][(
                                                find(board, PLAYER),
                                                item['char'])] = item
                                        UNDER[LEVEL][
                                                find(board, PLAYER)
                                        ].append(item['char'])
                                        data += "Dropped " + item['name']
                                        break
                        else:
                                data += "Nothing found under " + dr
                board = LEVELS[LEVEL]
                animate(getlit(
                        board, [(find(board, PLAYER), 10)], LEVEL),
                        .150, data=data)
                data += boardsturn(board, LEVEL)
                animate(getlit(
                        board, [(find(board, PLAYER), 10)], LEVEL),
                        .150, data=data)

clear()
print("You made it to level " + str(LEVEL))
print("You got " + str(SCORE) + " gold")
NAME = raw_input("Name?: ")
if len(NAME) > 10:
        NAME = NAME[0:10]
if not NAME:
        NAME = "You"
myentry = " ".join([NAME, str(LEVEL), str(SCORE)])
board = """   ### HALL OF FAME ###   ,
   NAME    | FLOOR, SCORE ,
-----------+--------------,
           |              ,
           |              ,
           |              ,
           |              ,
           |              ,
           |              ,
           |              ,
           |              ,
           |              ,
           |              ,""".splitlines()

try:
        with open("scoreboard.txt", "r") as SCOREBOARD:
                scoreboard = SCOREBOARD.read().splitlines()
except IOError:
        scoreboard = []
print(scoreboard)
raw_input()
with open("scoreboard.txt", "w") as SCOREBOARD:
        ENTERED = False
        for i, entry in enumerate(scoreboard):
                name, lvl, score = entry.split()
                if i > 10:
                        break
                if not ENTERED:
                        if LEVEL >= int(lvl) and SCORE > int(score):
                                SCOREBOARD.write(myentry + "\n")
                                ENTERED = True
                SCOREBOARD.write(entry + "\n")
        if len(scoreboard) < 10 and not ENTERED:
                SCOREBOARD.write(myentry)
with open("scoreboard.txt", "r") as SCOREBOARD:
        scoreboard = SCOREBOARD.read().splitlines()
        for i, entry in enumerate(scoreboard):
                name, lvl, score = entry.split()
                print(name, lvl, score)
                insert(board, [name], (0, i + 3))
                insert(board, [lvl], (13, i + 3))
                insert(board, [score], (20, i + 3))
printb(board)
