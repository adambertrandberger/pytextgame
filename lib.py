import re

class Character:
    def __init__(self, game):
        self.inventory = []
        self.action_callbacks = {}
        self.room_enter_callbacks = {}
        self.room_exit_callbacks = {}        
        self.game = game

    def starting_room(self, room):
        self.room = room
        return self

    def on(self, action_name, reaction):
        self.action_callbacks[action_name] = reaction

    def on_exit(self, room_name, reaction):
        self.room_exit_callbacks[room_name] = reaction

    def on_enter(self, room_name, reaction):
        self.room_enter_callbacks[room_name] = reaction

class Object:
    def __init__(self, name, description, actions):
        self.name = name
        self.description = description
        self.actions = actions
        self.callbacks = {}
        
    def __repr__(self):
        return self.name

    def tokenize(self):
        return self.name.split(' ')
    
    def on(self, action_name, reaction):
        self.callbacks[action_name] = reaction

# matches should be list of list (list of tokens
# [['this'], ['this', 'or', 'that']]
def eat(matches, tokens):
    for match_tokens in matches:
        equal = True
        for i in range(len(match_tokens)):
            if i >= len(tokens) or match_tokens[i] != tokens[i]:
                equal = False
                break;
        if equal:
            for i in range(len(match_tokens)):
                tokens.pop(0)
            return match_tokens

def list_startswith(list1, list2):
    if len(list1) > len(list2):
        return False
    
    for i in range(len(list1)):
        if list1[i] != list2[i]:
            return False
    return True

class Objects:
    def __init__(self, game):
        self.objects = []
        self.game = game
        
    def object(self, name, description, actions):
        self.objects.append(Object(name, description, actions))
        return self

    def notify(self, action_name, *objects):
        succeed = True
        notified = False
        for object in objects:
            if not object:
                continue
            
            if action_name in object.callbacks:
                succeed = object.callbacks[action_name]()
                notified = True
                break;
        return (notified, succeed)

    def get(self, name):
        matches = list(filter(lambda x: x.name == name, self.objects))
        if len(matches) > 1:
            raise Exception('More than one object named "%s"' % name)
        return matches[0] if len(matches) > 0 else None

    def eat(self, tokens):
        match_tokens = eat(map(lambda x: x.tokenize(), self.enumerate()), tokens)
        return ' '.join(match_tokens) if match_tokens else None
    
    def enumerate(self):
        return sorted(self.objects, key=lambda x: len(x.name), reverse=True)

    def on(self, object_name, action_name, reaction):
        self.get(object_name).on(action_name, reaction)

class Actions:
    def __init__(self, game):
        self.actions = []
        self.stops = ['in', 'on', 'the']
        self.game = game

    def action(self, name, *aliases):
        self.actions.append(list(map(str.split, [name] + list(aliases))))
        return self

    def stop_words(self, *words):
        self.stops = words
        return self

    def eat_stop_words(self, tokens):
        while tokens and tokens[0] in self.stops:
            tokens.pop(0)

    def eat(self, tokens):
        actions = self.enumerate()
        for action in actions:
            self.eat_stop_words(tokens)

            if list_startswith(action, tokens):
                for x in range(len(action)):
                    tokens.pop(0)
                    
                self.eat_stop_words(tokens)
                return self.canonicalize(action)

    def enumerate(self):
        all_actions = []
        for action in self.actions:
            for alias in action:
                all_actions.append(alias)
        return sorted(all_actions, key=len, reverse=True)
    
    def canonicalize(self, name):
        if type(name) == str:
            name = name.split(' ')
        for action in self.actions:
            if name in action:
                return ' '.join(action[0])

class Game:
    def __init__(self):
        self.rooms = Rooms(self)
        self.character = Character(self)
        self.objects = Objects(self)
        self.actions = Actions(self)
        self.directions = Directions(self)
        
        self.go_action_name = 'go'
        self.look_action_name = 'look'
        self.take_action_name = 'take'        

    def set_go_action_name(self, action_name):
        self.go_action_name = action_name

    def set_look_action_name(self, action_name):
        self.look_action_name = action_name

    def set_take_action_name(self, action_name):
        self.take_action_name = action_name

    def configure_directions(self):
        return self.directions

    def configure_rooms(self):
        return self.rooms

    def configure_character(self):
        return self.character

    def configure_objects(self):
        return self.objects

    def configure_actions(self):
        return self.actions

    def inventory_has(self, object):
        def func():
            return len(list(filter(lambda x: x == object, self.character.inventory))) > 0
        return func

    def cond(self, predicate, then_part, else_part):
        def func():
            if predicate():
                then_part()
            else:
                else_part()
        return func

    def fail(self, message):
        '''
        Don't continue the action and print the message to the screen
        '''
        def func():
            print(message)
            return False
        return func

    def succeed(self, message):
        '''        
        Continue with the action and print the message to the screen
        '''
        def func():
            print(message)
            return False
        return func
    
    def go(self, direction):
        '''
        Moves the character to a room in this direction
        '''
        next_room = self.rooms.go(self.character.room, direction)
        if not next_room:
            print('You cannot go %s' % direction)
        else:
            old_room = self.character.room
            self.character.room = next_room
            for room in self.character.room_enter_callbacks:
                if room == next_room:
                    self.character.room_enter_callbacks[room]()
                    break;
            for room in self.character.room_exit_callbacks:
                if room == next_room:
                    self.character.room_exit_callbacks[room]()
                    break;
                self.print_room()

    def exec(self, string):
        room = self.rooms.get(self.character.room)
        
        tokens = re.split('\s+', string.strip())
        
        action = self.actions.eat(tokens)
        source_object = self.objects.get(self.objects.eat(tokens))

        # for "use key on door":
        # "key" is source object
        # "door" is target object
        self.actions.eat_stop_words(tokens)
        target_object = self.objects.get(self.objects.eat(tokens))
        
        direction = self.directions.eat(tokens)

        notified, succeed = self.objects.notify(action, source_object, target_object)

        # still allow for callbacks if it doesn't have the action
        if source_object and action not in source_object.actions:
            return
        
        if not succeed:
            return
        
        if action == self.go_action_name:
            if not direction:
                print('You must give a valid direction to go')
            else:
                self.go(direction)
        elif action == self.look_action_name:
            if not source_object:
                self.print_room()
            else:
                print(source_object.description)
        elif action == self.take_action_name:
            if source_object.name in room.objects:
                self.character.inventory.append(source_object.name)
                print('You pick up the %s.' % source_object.name)
                room.objects.remove(source_object.name)
        elif action == 'inventory':
            if self.character.inventory:
                print('You have ' + ', '.join(map(lambda x: 'a ' + x, self.character.inventory)) + '.')
            else:
                print('Your inventory is empty.')
        elif not notified:
            print('I don\'t understand')

    def print_room(self):
        room = self.rooms.get(self.character.room)
        print(room.name.title())
        print('\t', room.description)
        adjacent_rooms = self.rooms.get_adjacent_rooms(self.character.room)

        print()        
        for direction in adjacent_rooms:
            print('%s is to the %s.' % (adjacent_rooms[direction].title(), direction))

        if room.objects:
            objects = room.objects.copy()
            if len(objects) > 1:
                objects.insert(-1, 'and')
                
            print('There is a %s here.' % ', '.join(objects))
            
class Room:
    def __init__(self, name, description='', objects=None):
        self.name = name
        self.description = description
        self.objects = objects if objects != None else []
        self.connections = []

class Rooms:
    def __init__(self, game):
        self.mappings = {}
        self.rooms = {}
        self.game = game

    def room(self, name, description, objects=None, connections=None):
        self.rooms[name] = Room(name, description, objects)
        return self
    
    def map(self, from_room, direction, to_room, bidirectional=True):
        if from_room not in self.mappings:
            self.mappings[from_room] = []
        if to_room not in self.mappings:
            self.mappings[to_room] = []
            
        self.mappings[from_room].append((direction, to_room))
        
        if bidirectional:
            self.mappings[to_room].append((self.game.directions.get_opposite(direction), from_room))

        return self

    def get(self, room_name):
        return self.rooms[room_name]

    def get_adjacent_rooms(self, room_name):
        return dict(self.mappings[room_name])
    
    def go(self, from_room, direction):
        for (to_dir, to_room) in self.mappings[from_room]:
            if direction == to_dir:
                return to_room
            
class Directions:
    def __init__(self, game):
        self.directions = []
        self.opposites = {}
        self.game = game

    def direction(self, name, *aliases):
        self.directions.append([name] + list(aliases))
        return self

    def canonicalize(self, name):
        for direction in self.directions:
            if name in direction:
                return direction[0]

    def enumerate(self):
        all_directions = []
        for direction in self.directions:
            for alias in direction:
                all_directions.append(alias)
        return sorted(all_directions, key=len, reverse=True)

    def eat(self, tokens):
        match_tokens = eat(map(lambda x: x.split(' '), self.enumerate()), tokens)
        return self.canonicalize(' '.join(match_tokens)) if match_tokens else None
    
    def opposite(self, name, opposite_name):
        name = self.canonicalize(name)
        opposite_name = self.canonicalize(opposite_name)
        self.opposites[name] = opposite_name
        self.opposites[opposite_name] = name
        return self

    def get_opposite(self, name):
        name = self.canonicalize(name)
        return self.opposites[name]
