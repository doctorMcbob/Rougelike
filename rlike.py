"""
rlike.py a vanilla python turn based roguelike
board is splitlines syntax, list of strings
board[y][x] for example

TO DO LIST:
	. enemy implementation
	. fighting implementation
	. armor item implementation
	. UNDER player duplication bug fix
	. write line-of-sight function
	. darken level (so you only see where theres light)
	. batteries 
	. flashlight

	. clean everything the f up
	. try to optomize level builder, the fact that im typing this while waiting for the level to load is a problem
"""
from __future__ import print_function, unicode_literals
import os, sys
from random import randint, choice
from time import sleep
from math import sqrt
DEBUG = "-d" in sys.argv

COLORS = {
	"@": "\033[1;45;93m",
	">": "\033[1;45;33m",
	"<": "\033[1;45;33m",
	"+": "\033[1;94;40m",
	"#": "\033[1;90;40m",
	"=": "\033[1;43;40m",
	" ": "\033[45m",
	".": "\033[1;45;35m",
	"/": "\033[1;45;96m",
	"footer": "\033[0m",
	
}
PLAYER = "@"
DWNSTR = ">"
UPSTAIR = "<"
STONE = "#"
WALL = "+"
DOOR = "="
EMPTY = " "
FLOOR = "."
RAT = "r"
SNAKE = "s"
BAT = "b"
STAFF = "/"
BOW = ")"
BATTERY = "%"
POTION = "p"
SCROLL = "~"
ARMOR = "}"

CONSUME = POTION + SCROLL + BATTERY
WEAP = STAFF + BOW
FIGHTABLE = RAT + BAT + SNAKE
TANG = STONE + WALL + DOOR #Tangible
ACT = PLAYER + DOOR + FIGHTABLE
GETTABLE = WEAP + ARMOR + CONSUME

START = """###########
#         #
#  < / >  #
#    @    #
#         #
###########""".splitlines()

END = """##########
#    Wow #
#  <     #
##########
# TheEnd #
##########""".splitlines()

ENEMIES = [{}]
UNDER = [{(5, 3):[" "],(5, 2):[" "]}] # a stack for each position, UNDER[level][position]
ITEMS = [{((5, 2), STAFF):{
		"name": "Pole",
		"stat": 2,
		"char": STAFF,
	}}] # a dictionary of names and info, ITEMS[(x, y, THING)]

INV = []
HP = 100
ATK = 1
DEF = 1
EQUIP = {
	"weapn": None,
	"armor": None
}

#### Name maker, specialized to make silly sounding names like biffy and pulddigy
vowel = "aeiou"
const = "bbbbbbcddddddfffggghjklllmmmnnnpppqrstttvwxyyyyz"
special = "bdfglp"
def makename():
	roll = randint(0, 100)
	if roll < 15:
		return choice(const) + choice(vowel) + ( choice(special) * 2 ) + "y"
	if roll < 50:
		return choice(const) + choice(vowel) + choice(special) + ( choice(special) * 2 ) + choice(vowel) + choice(special) + "y"
	if roll < 65:
		return choice(const) + choice(vowel) + choice(const) +  choice(vowel) + "ly"
	if roll < 80:
		return choice(const) + choice(special) + choice(vowel) + choice(vowel) + choice(special) + choice(special)
	return choice(special) + choice(vowel) + choice(special) + choice(special)

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

def clear(): os.system("clear || cls")

def animate(board, miliseconds, debug=False, data=False):
	if debug and not DEBUG:
		return 
	clear()
	printb(board); 
	if data: print(data)
	sleep(miliseconds)

def colored(st): 
	ret = ""
	for p in st:
		if p in COLORS:
			ret += COLORS[p] + p + COLORS['footer']
		else:
			ret += p
	return ret + COLORS['footer']

def printb(board): print(colored("\n".join(board)))

def find(board, piece):
	Y = 0
	while not piece in board[Y]: Y += 1
	return board[Y].index(piece), Y

def findall(board, piece):
	for y, line in enumerate(board):
		for x, pce in enumerate(line):
			if pce == piece: yield x, y

def insert(board, sub, position):
	for y, line in enumerate(sub):
		for x, piece in enumerate(line):
			put(board, (position[0] + x, position[1] + y), sub[y][x])

def bisequal(board1, board2):
	try:
		for y, line in enumerate(board1):
			for x, piece in enumerate(line):
				if piece != board2[y][x]: return False
		return True
	except IndexError: return False

def checkfor(board, sub):
	checklist = findall(board, sub[0][0])
	ret = []
	for x, y in checklist:
		p = get(board, (x, y))
		put(board, (x, y), "%")
		put(board, (x, y), p)
		try:
			if bisequal(getsub(board, (x, y), (len(sub[0]), len(sub))), sub):
				ret.append((x, y))
		except IndexError:
			continue
	return ret

def step(board, position, direction, under=False, lvl=0):
	x2, y2 = position[0] + direction[0], position[1] + direction[1]
	nxt = get(board, (x2, y2)) 
	piece = get(board, position)
	if ( piece in ACT ) and ( nxt in ACT ): 
		collide(board, position, (x2, y2))
	if nxt in TANG: return
	put(board, position, UNDER[lvl][position].pop(), under=under, lvl=lvl)
	put(board, (x2, y2), piece, under=under, lvl=lvl)

def collide(board, pos1, pos2):
	p1, p2 = get(board, pos1), get(board, pos2)
	if p2 == PLAYER != p1: 
		p1, p2 = p2, p1
		pos1, pos2 = pos2, pos1
	if p1 == PLAYER and p2 == DOOR:
		if pos2 in UNDER: put(board, pos2, UNDER[pos2])
		else: put(board, pos2, EMPTY)

def insight(board, position1, position2):
	pass

def new_floor(entry, lvl):
	"""returns floor with random carvings, garunteed solvable"""
	board = (
		STONE * max(min(randint(20, 20 + (3 * lvl)), 80), entry[0] + 2) + "\n"
		) * max(min(randint(15, 15 + (1 * lvl)), 80), entry[1] + 2)
	board = board.splitlines()
	exit = randint(1, len(board[0])-2), randint(2, len(board)-2)
	while sqrt((entry[0] - exit[0])**2 + (entry[1] - exit[1])**2) < min(len(board[0]) / 3, len(board) / 3, 2 + lvl):
		if DEBUG: print("Finding exit... ", exit)
		exit = randint(1, len(board[0])-2), randint(2, len(board)-2)
	X, Y = entry
	d = (0, 0) #Direction
	c = 0
	while (X, Y) != exit:
		animate(board, .00001, debug=True)

		if get(board, (X, Y)) == STONE:
			put(board, (X, Y), EMPTY)

		if c <= 0 and randint(0, 10) > 4:
			d = [(0, 1), (1, 0), (-1, 0), (0,-1)][randint(0,3)]
			c = randint(2, 5)
		dist = sqrt((X - exit[0])**2 + (Y - exit[1])**2)
		if dist < 6:
			if X == exit[0]: d = (0, 1) if Y < exit[1] else (0, -1)
			else: d = (1, 0) if X < exit[0] else (-1, 0)
		c -= 1
	 	X += d[0]
	 	Y += d[1]
	 	if X == 0: X += 1
	 	elif X == len(board[0])-1: X -= 1
	 	elif Y == 0: Y += 1
	 	elif Y == len(board)-1: Y -= 1
		put(board, entry, UPSTAIR)		
	put(board, exit, DWNSTR)
	return board

def makeroom(board, position, dimensions, lvl):
	w, h = dimensions
	room = ( ( ( WALL * w ) + "\n" ) * h ).splitlines()
	insert(room, [ FLOOR * (w - 2) ] * (h - 2), (1, 1))
	for x in range(randint(2, 4)):
		put(room, choice([n for n in findall(room, WALL)]), DOOR)
	insert(board, room, position)


def scrub(board, limit=3):
	slots = checkfor(board, [STONE * limit] * limit)
	while slots:
		for slot in slots:
			x_, y_ = slot
			slot = getsub(board, slot, (limit, limit))
			for stone in findall(slot, STONE):
				x, y = stone
				x, y = x + x_, y + y_
				try:
					nbrs = sum([get(board, pos) == STONE for pos in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]])
				except IndexError:
					nbrs = 2
				if nbrs >= 2 and randint(0, 20) < 5:
					put(slot, stone, EMPTY)
			insert(board, slot, (x_, y_))
			slots = checkfor(board, [STONE * limit] * limit)
			animate(board, .00001, debug=True)
	for stone in findall(board, STONE):
		x, y = stone
		try:
			nbrs = sum([get(board, pos) == EMPTY for pos in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]])
		except IndexError:
			nbrs = 0
		animate(board, .00001, debug=True)
		if nbrs in [2, 3] and randint(0, 20) < 8:
			put(board, stone, EMPTY)
	return board

def refine(board, lvl):
	sub = getsub(board, (1, 1), (len(board[0]) - 2, len(board) - 2))
	room = checkfor(sub, [STONE * 6] * 6)
	if room: makeroom(sub, choice(room), (6, 6), lvl)
	b = scrub(sub)	
	for stone in findall(b, STONE):
		try:
			if get(b, (stone[0] + 1, stone[1])) == get(b, (stone[0] - 1, stone[1])) == EMPTY:
				put(b, stone, "+")
			if get(b, (stone[0], stone[1] + 1)) == get(b, (stone[0], stone[1] - 1)) == EMPTY:
				put(b, stone, "+")
		except IndexError:
			continue
	insert(board, b, (1, 1))
	return board

def populate(board, lvl):
	return board

def dequip(item):
	if EQUIP["weap"] == item:
		INV.append(item)
		EQUIP["weap"] = None
		ATK -= item['stat']
	elif EQUIP["armor"] == item:
		INV.append(item)
		EQUIP["weap"] = None
		DEF -= item['stat']
	else: return "not equipted"

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

LEVELS = [START]
def dig_dungeon(floors=15):
	global UNDER, ENEMIES, ITEMS, LEVELS, END
	lvl = floors
	UNDER += [{}] * (floors + 1)
	ITEMS += [{}] * (floors + 1)
	ENEMIES += [{}] * (floors + 1)
	while floors:
		animate(["Digging Dungeon...", "floor " + str(lvl-floors)], 0)
		floors -= 1
		LEVELS.append(populate(refine(new_floor(find(LEVELS[-1], DWNSTR), lvl-floors), lvl-floors), lvl-floors))
	entry = find(LEVELS[-1], DWNSTR)
	LEVELS.append([" " * (entry[0] + len(END[0]))] * (entry[1] + len(END)))	
	insert(LEVELS[-1], END, (entry[0] - 2, entry[1] - 2))


LEVEL = 0
board = LEVELS[LEVEL]
dig_dungeon(floors=int(raw_input("Wesley's Roguelike\nHow many levels? (blank for 15): ")))
data = "The Jeorney Begins"
animate(board, .300, data=data)
while True:
	if LEVEL > len(LEVELS): break
	cmds = raw_input(": ").split()[::-1]
	while cmds:
		data = "HP: " + str(HP) + " Weapon: "
		if EQUIP['weapn']: data += EQUIP["weapn"]['name']
		else: data += "None"
		if EQUIP['armor']: data += " Armor: " + EQUIP["armor"]["name"] + "\n"
		else: data += " Armor: None\n"
		cmd = cmds.pop()
		if cmd in ["Q", "quit"]: 
			if raw_input("Print dungeon? Nothing for no..."):
				for b in LEVELS: 
					print()
					printb(b)
			quit()

		if cmd in ["L", "left"]: 
			step(board, find(board, PLAYER), (-1, 0), under=True, lvl=LEVEL)
		if cmd in ["R", "right"]: 
			step(board, find(board, PLAYER), (1, 0), under=True, lvl=LEVEL)
		if cmd in ["U", "up"]: 
			step(board, find(board, PLAYER), (0, -1), under=True, lvl=LEVEL)
		if cmd in ["D", "down"]: 
			step(board, find(board, PLAYER), (0, 1), under=True, lvl=LEVEL)

		if cmd in ["Un", "under"]: 
			data += ", ".join(UNDER[LEVEL][find(board, PLAYER)])

		if cmd in ["Inv", "inventory"]:
			data += ", ".join([item["name"] for item in INV])

		if cmd in ["stats"]:
			data += "Atk: " + str(ATK) + "\nDef: " + str(DEF)

		if cmd in ["Eq", "equip"]:
			if cmds:
				eq = cmds.pop()
			else:
				eq = raw_input("Equipt what? : ")
			for item in INV:
				if item["name"] == eq:
					data += str(equip(item))	

		if cmd in ["G", "get"]:
			for piece in UNDER[LEVEL][find(board, PLAYER)]:
				if (find(board, PLAYER), piece) in ITEMS[LEVEL]:
					UNDER[LEVEL][find(board, PLAYER)].remove(piece)
					INV.append(ITEMS[LEVEL][(find(board, PLAYER), piece)])

		if cmd in ["W", "warp"]: # and DEBUG:
			put(board, find(board, PLAYER), UNDER[LEVEL][find(board, PLAYER)].pop(), under=True, lvl=LEVEL)
			put(board, find(board, DWNSTR), PLAYER, under=True, lvl=LEVEL)

		if cmd in ["S", "stairs"]:
			pos = find(board, PLAYER)
			if pos in UNDER[LEVEL]: 
				if UPSTAIR in UNDER[LEVEL][pos]:
					LEVEL -= 1
					if LEVEL < 0: 
						print("Farewell traveler")
						quit()
				elif DWNSTR in UNDER[LEVEL][pos]: 
					LEVEL += 1
					put(LEVELS[LEVEL], find(LEVELS[LEVEL], UPSTAIR), PLAYER, under=True, lvl=LEVEL)

		board = LEVELS[LEVEL]
		animate(board, .300, data=data)
