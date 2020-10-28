#!/usr/bin/python3

import argparse
import fnmatch
import json
import os
import struct
import sys

import mca

#-----------------------------------------------------------------------------
# Setup

#  "id": "Home_-28,75,-178",
#  "name": "Home",
#  "x": -28,
#  "y": 75,
#  "z": -178,

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

def dumpchunk (msg: str, chunk: dict):
    warn("{0} ({1},{2})".format(msg, args.x, args.z))
    print(json.dumps(chunk.dump(), indent=2, sort_keys=True))
    exit(1)

def dumpdict (msg: str, data: dict):
    warn("{0} ({1},{2})".format(msg, args.x, args.z))
    print(json.dumps(data, indent=2, sort_keys=True))
    exit(1)

# "BB": [ -940, 8, -581, -778, 25, -464 ],
def bb_midpoint (bb: list):
    x = int((bb[0] + bb[3])/2)
    y = int((bb[1] + bb[4])/2)
    z = int((bb[2] + bb[5])/2)

    return x, y, z

def save_waypoint (filename: str, data: dict):
    with open(filename, 'w') as outfile:
        json.dump(data, outfile)

def find (pattern, path):
    result = []

    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))

    return result

#-----------------------------------------------------------------------------
def basic_structure (name: str, data: dict):
    if "BB" not in data:
        warn("no bounding border data found in {0} data".format(name))
        save_waypoint("{0}-no-bb.json".format(name), data)
        return 1

    mx, my, mz = bb_midpoint(data['BB'])

    waypoint = waypoint_template.copy()

    waypoint['id'] = "{0}_{1},{2},{3}".format(name,mx,my,mz)
    waypoint['name'] = name
    waypoint['x'] = mx
    waypoint['y'] = my
    waypoint['z'] = mz

    filename = "{0}.json".format(waypoint['id'])

    save_waypoint(filename, waypoint)

#-----------------------------------------------------------------------------
def Ocean_Ruin (data: dict):
    basic_structure('Ocean Ruin', data)

#-----------------------------------------------------------------------------
def Shipwreck (data: dict):
    basic_structure('Shipwreck', data)

#-----------------------------------------------------------------------------
def Mineshaft (data: dict):
    basic_structure('Mineshaft', data)

#-----------------------------------------------------------------------------
def find_structures (chunk: dict):
    level = chunk.get('Level')

    if not level:
        dumpchunk('no level data found in chunk', chunk)

    structures = level.get('Structures')

    if not structures:
        dumpchunk('no structures data found in level', chunk)

    starts = structures.get('Starts')

    if not starts:
        dumpchunk('no starts found in structures', chunk)

    data = starts.dump()

    for s in data:
        if data[s]['id'] == 'INVALID':
            continue

        func = globals()[s]
        func(data[s])

#-----------------------------------------------------------------------------
def parse_file (filename: str):
    with open(filename, 'rb') as f:
        for cx in range(0,32):
            for cz in range(0,32):
                warn("reading chunk {0},{1} from {2} ...".format(cx,cz,filename))

                s = (cx + cz * 32) * 4
                warn("s: {0}".format(s))

                f.seek(s)
                start = struct.unpack('>i', f.read(4))[0]
                warn("start: {0}".format(start))

                if start == 0:
                    warn("chunk {0},{1} is empty".format(cx,cz))
                    continue

                offset = 4096 * (start >> 8)
                warn("offset: {0}".format(offset))

                f.seek(offset)

                chunk = mca.Region.read_chunk(f)

                if not chunk:
                    warn("could not read chunk {0},{1}".format(cx,cz))
                    exit(1)

                find_structures(chunk)

#-----------------------------------------------------------------------------
# Parse command-line arguments

parser = argparse.ArgumentParser(description='Minecraft MCA dump')
parser.add_argument('mcapath')

args = parser.parse_args()

#parse_file('/home/harleypig/.config/gdlauncher_next/instances/Playpen/saves/Play that funky ___/region/r.-2.-1.mca')
#parse_file('/home/harleypig/.config/gdlauncher_next/instances/Playpen/saves/Play that funky ___/region/r.1.0.mca')
#exit(1)

testfile = '/home/harleypig/.config/gdlauncher_next/instances/Playpen/saves/Play that funky ___/region/r.1.0.mca'

mcas = find('*.mca', args.mcapath)

for mca in mcas:
    #print(">>>{0}<<<".format(mca))
    #parse_file(mca)
    parse_file(testfile)
    exit(1)
