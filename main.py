from lib import *

inv = []

game = Game()
game.configure_directions() \
    .direction('east', 'e') \
    .direction('west', 'w') \
    .direction('north', 'n') \
    .direction('south', 's') \
    .direction('up', 'upstairs') \
    .direction('down', 'downstairs') \
    .opposite('east', 'west') \
    .opposite('north', 'south') \
    .opposite('up', 'down')

game.configure_actions() \
    .action('look', 'l', 'check out', 'inspect') \
    .action('take', 't', 'pick up') \
    .action('inventory', 'inv', 'i') \
    .action('go', 'g', 'walk') \
    .action('drop') \
    #    .on('take', lambda state: inv.append(state.object))

game.configure_objects() \
    .object('bathroom key', 'A dirty, dirty key', ['look', 'take']) \
    .object('towel', 'A stained towel.', ['look', 'take']) \
    .object('car', 'A big red van', ['look']) \
    .on('car', 'take', game.cond(game.inventory_has('forklift'),
                                 game.succeed('You use your forklift to take the car'),
                                 game.fail('You try to stuff the car into your inventory, but it\'s too heavy.')))

game.configure_rooms() \
    .room('bathroom', 'A well kept bathroom.', [
         'towel',
         'car'
    ]) \
    .room('basement', 'A dark, creepy room.', [
         'bathroom key'
    ]) \
    .room('living room', 'Smells clean!', []) \
    .map('basement', 'upstairs', 'bathroom', bidirectional=False) \
    .map('living room', 'west', 'bathroom')

game.configure_character() \
    .starting_room('living room') \
    .on_exit('living room', lambda: print("HAHAHA"))


if __name__ == '__main__':
     while True:
          game.exec(input('> '))
