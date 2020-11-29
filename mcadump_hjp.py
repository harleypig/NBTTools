#!/usr/bin/python3

# https://minecraft.gamepedia.com/Java_Edition_level_format
# https://minecraft.gamepedia.com/Chunk_format

import argparse
import fnmatch
import json
import os
import struct
import sys

import mca

#-----------------------------------------------------------------------------
# Setup

waypoint_template = {
  "icon": "waypoint-normal.png",
  "r": 0,
  "g": 0,
  "b": 0,
  "enable": True,
  "type": "Normal",
  "origin": "journeymap",
  "dimensions": [ 0 ],
  "persistent": True
}

#-----------------------------------------------------------------------------
# Functions

def warn (*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# "BB": [ -940, 8, -581, -778, 25, -464 ],
def bb_midpoint (bb: list):
    x = int((bb[0] + bb[3])/2)
    y = int((bb[1] + bb[4])/2)
    z = int((bb[2] + bb[5])/2)

    return x, y, z

def find (pattern, path):
    result = []

    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))

    return result

def save_json (filename: str, data: dict):
    with open(filename, 'w') as outfile:
        json.dump(data, outfile)

def dumpchunk (msg: str, chunk: dict):
    warn(msg)
    print(json.dumps(chunk.dump(), indent=2, sort_keys=True))

def save_waypoint (name: str, mx: int, my: int, mz: int, dim=[1]):
    waypoint = waypoint_template.copy()

    waypoint['id'] = "{0}_{1},{2},{3}".format(name,mx,my,mz)
    waypoint['name'] = name
    waypoint['x'] = mx
    waypoint['y'] = my
    waypoint['z'] = mz
    waypoint['dimensions'] = dim

    filename = "json/{0}.json".format(waypoint['id'])

    save_json(filename, waypoint)

#-----------------------------------------------------------------------------
def basic_structure (name: str, data: dict, dim=[3]):
    if "BB" not in data:
        warn("no bounding border data found in {0} data".format(name))
        save_json("json/{0}-no-bb.json".format(name), data)
        return 1

    mx, my, mz = bb_midpoint(data['BB'])

    save_waypoint(name, mx, my, mz, dim)


#-----------------------------------------------------------------------------
def Ocean_Ruin (data: dict):
    basic_structure('Ocean Ruin', data)

#-----------------------------------------------------------------------------
def Shipwreck (data: dict):
    basic_structure('Shipwreck', data)

#-----------------------------------------------------------------------------
def Mineshaft (data: dict):
    basic_structure('Mineshaft', data, [3])

#-----------------------------------------------------------------------------
def Igloo (data: dict):
    basic_structure('Igloo', data)

#-----------------------------------------------------------------------------
def Jungle_Pyramid (data: dict):
    basic_structure('Jungle Pyramid', data)

#-----------------------------------------------------------------------------
def Pillager_Outpost (data: dict):
    basic_structure('Pillager Outpost', data)

#-----------------------------------------------------------------------------
def Swamp_Hut (data: dict):
    basic_structure('Swamp Hut', data)

#-----------------------------------------------------------------------------
def Village (data: dict):
    basic_structure('Village', data)

#-----------------------------------------------------------------------------
def quark_big_dungeon (data: dict):
    if "BB" not in data:
        warn("no bounding border data found in quark:big_dungeon data".format(name))
        save_json("json/{0}-no-bb.json".format(name), data)
        return 1

    name='Big Dungeon Corner'

    my = data['BB'][1]

    if data['BB'][4] > my:
        my = data['BB'][4]

    mx1 = data['BB'][0]
    mx2 = data['BB'][3]
    mz1 = data['BB'][2]
    mz2 = data['BB'][5]

    save_waypoint(name, mx1, my, mz1)
    save_waypoint(name, mx1, my, mz2)
    save_waypoint(name, mx2, my, mz1)
    save_waypoint(name, mx2, my, mz2)

#-----------------------------------------------------------------------------
def find_structures (level: dict):
    structures = level.get('Structures')

    if not structures:
        dumpchunk('no structures data found in level', level)
        return 1

    starts = structures.get('Starts')

    if not starts:
        dumpchunk('no starts found in structures', structures)
        return 1

    data = starts.dump()

    for s in data:
        if data[s]['id'] == 'INVALID':
            continue

        try:
            func = globals()[s]
            func(data[s])

        except KeyError:
            if s == 'quark:big_dungeon':
                quark_big_dungeon(data[s])

            else:
                warn("don't know how to handle structure {0}".format(s))
                savefile="json/{0}.json".format(s)
                save_json(savefile, data[s])

#-----------------------------------------------------------------------------
def parse_file (filename):
    with open(filename, 'rb') as f:
        for cx in range(0,32):
            for cz in range(0,32):
                #warn("reading chunk {0},{1} from {2} ...".format(cx,cz,filename))

                s = (cx + cz * 32) * 4
                #warn("s: {0}".format(s))

                f.seek(s)
                start = struct.unpack('>i', f.read(4))[0]
                #warn("start: {0}".format(start))

                if start == 0:
                    #warn("chunk {0},{1} is empty".format(cx,cz))
                    continue

                offset = 4096 * (start >> 8)
                #warn("offset: {0}".format(offset))

                f.seek(offset)

                chunk = mca.Region.read_chunk(f)

                if not chunk:
                    warn("could not read chunk {0},{1}".format(cx,cz))
                    exit(1)

                level = chunk.get('Level')

                if not level:
                    dumpchunk('no level data found in chunk', chunk)
                    return 1

                find_structures(level)

#-----------------------------------------------------------------------------
# Parse command-line arguments

parser = argparse.ArgumentParser(description='Minecraft MCA dump')
parser.add_argument('mcapath')
args = parser.parse_args()

mcas = find('*.mca', args.mcapath)

for m in mcas:
    warn("Parsing {0}".format(os.path.basename(m)))
    parse_file(m)
