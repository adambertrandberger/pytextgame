from lib import *

game = Game()
game.configure_directions() \
    .direction('east', 'e') \
    .direction('west', 'w') \
    .direction('north', 'n') \
    .direction('south', 's') \
    .direction('up', 'upstairs') \
    .opposite('down', 'downstairs') \
    .opposite('east', 'west') \
    .opposite('north', 'south') \
    .opposite('up', 'down')

game.configure_actions() \
    .skip_words('at', 'on', 'the') \
    .action('look', 'check out', 'inspect') \
    .action('take', 'pick up') \
    .action('go', 'walk') \
    .action('drop')

game.configure_objects() \
    .object('bathroom key', 'A dirty, dirty key', ['look', 'take']) \
    .object('towel', 'A stained towel.', ['look', 'take'])

game.configure_rooms() \
    .room('bathroom', 'A well kept bathroom', [
        'towel'
    ]) \
    .room('basement', 'A dark, creepy room', [
        'bathroom key'
    ]) \
    .room('living room', 'Smells clean', []) \
    .map('basement', 'upstairs', 'bathroom', bidirectional=False) \
    .map('living room', 'west', 'bathroom')

game.configure_character() \
    .starting_room('living room')

if __name__ == '__main__':
     while True:
         game.exec(input('> '))
