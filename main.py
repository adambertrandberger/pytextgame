from lib import *
import side_effects
import predicates

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
    .action('use', 'u') \
    .action('eat', 'consume') \
    .action('drop', 'd') \
    .action('talk')
#    .action('destroy', 'break', progn(side_effects.destroy(), succeed()))

game.configure_objects() \
    .object('key', 'A dirty, dirty key', ['look', 'take', 'use']) \
    .object('towel', 'A stained towel.', ['look', 'take', 'drop']) \
    .object('crab', 'A bright red crab.', ['talk', 'look']) \
    .object('car', 'A big red van', ['look']) \
    .on('key', 'eat', cond(
         predicates.has_visited('bathroom'),
         progn(
              side_effects.remove_from_inventory(),
              succeed('Yum')),
         fail())) \
    .on('crab', 'talk', succeed('Welcome home, son!')) \
    .on_use('crab', 'towel', succeed('Mmm, thanks! I needed that.')) \
    .on_use('key', 'towel', progn(side_effects.add_to_inventory('taco'), succeed('Nice!'))) \
    .on('car', 'take', cond(predicates.inventory_has('forklift'),
                            succeed('You use your forklift to take the car'),
                            fail('You try to stuff the car into your inventory, but it\'s too heavy.'))) \
    .on('towel', 'drop', cond(predicates.in_room('living room'),
                              fail('You can\'t drop that in the living room'),
                              succeed()))

game.configure_rooms() \
    .room('bathroom', 'A well kept bathroom.', [
         'towel',
         'car'
    ]) \
    .room('basement', 'A dark, creepy room.', [

    ]) \
    .room('living room', 'Smells clean!', [
         'key',
         'crab'
         
    ]) \
    .map('basement', 'upstairs', 'bathroom', bidirectional=False) \
    .map('living room', 'west', 'bathroom')

game.configure_character() \
    .starting_room('living room') \
    .on_exit('living room', cond(
         predicates.inventory_has('key'),
         succeed(),
         fail('You need the key')))

if __name__ == '__main__':
     while True:
          game.execute(input('> '))
