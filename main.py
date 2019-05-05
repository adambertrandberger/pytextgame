from lib import *

dirs = Directions()
dirs.add('east', 'e')
dirs.add('west', 'w')
dirs.add('north', 'n')
dirs.add('south', 's')
dirs.add('up', 'upstairs')
dirs.add('down', 'downstairs')
dirs.add_opposite('east', 'west')
dirs.add_opposite('north', 'south')
dirs.add_opposite('up', 'down')

acts = Actions()
acts.add_skip_words('at', 'on', 'the')
acts.add('look', 'check out', 'inspect')
acts.add('take', 'pick up')
acts.add('go', 'walk')
acts.add('drop')

objs = Objects()
objs.add('bathroom key', 'A dirty, dirty key', ['look', 'take'])
objs.add('towel', 'A stained towel.', ['look', 'take'])

rooms = Rooms()
rooms.add('bathroom', 'A well kept bathroom', [
    'towel'
])
rooms.add('basement', 'A dark, creepy room', [
    'bathroom key'
])
rooms.add('living room', 'Smells clean', [])

rooms.map('basement', 'upstairs', 'bathroom', bidirectional=False)
rooms.map('living room', 'west', 'bathroom')

char = Character('living room')

game = Game(char, rooms, objs, acts, dirs)

if __name__ == '__main__':
     while True:
         game.exec(input('> '))
