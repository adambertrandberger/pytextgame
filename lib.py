import re

from side_effects import SideEffect
from predicates import Predicate

class Character:
    def __init__(self, game):
        self.inventory = []
        self.action_callbacks = {}
        self.room_enter_callbacks = {}
        self.room_exit_callbacks = {}
        self.inventory_limit = None
        self.game = game

    def add_to_inventory(self, object, force=False):
        if force or self.inventory_limit == None or len(self.inventory) + 1 <= self.inventory_limit:
            self.inventory.append(object)
            return True
        else:
            return False

    def inventory_size(self, size):
        self.inventory_limit = size
        return self
    
    def starting_room(self, room):
        self.room = room
        return self

    def on(self, action_name, reaction):
        self.action_callbacks[action_name] = reaction
        return self

    def on_exit(self, room_name, reaction):
        self.room_exit_callbacks[room_name] = reaction

    def on_enter(self, room_name, reaction):
        self.room_enter_callbacks[room_name] = reaction

    def on_enter_from(self, from_room, to_room, reaction):
        '''
        on_enter_from(living room, bathroom, succeed())

        Fires when you are entering from living room to the bathroom
        '''
        self.room_enter_from_callbacks[from_room + to_room] = reaction

    def on_exit_to(self, from_room, to_room, reaction):
        '''
        on_exit_to(living room, bathroom, succeed())

        Fire when you are exiting from the living room to the bathroom
        '''
        self.room_exit_to_callbacks[from_room + to_room] = reaction
        

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
        return self

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
        self.use_callbacks = {}

    def on_use(self, source, target, reaction, bidirectional=True):
        self.use_callbacks[source + target] = reaction

        if bidirectional:
            self.use_callbacks[target + source] = reaction
            
        return self
    
    def object(self, name, description, actions):
        self.objects.append(Object(name, description, actions))
        return self

    def notify(self, action_name, source_object, target_object):
        result = None
        notified = False
        objects = [source_object, target_object]

        if action_name == 'use' and source_object and target_object:
            use_key = source_object.name + target_object.name            
            if use_key in self.use_callbacks:
                result = self.game.exec_reaction(self.use_callbacks[use_key], source_object, target_object)
                notified = True
                
        for object in objects:
            if not object:
                continue
            
            if action_name in object.callbacks:
                result = self.game.exec_reaction(object.callbacks[action_name], source_object, target_object)
                notified = True
                break;

        return (notified, result)

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
        return self

class Actions:
    def __init__(self, game):
        self.actions = []
        self.stops = ['in', 'on', 'the', 'with', 'to']
        self.reactions = {}
        self.game = game

    def action(self, name, *aliases):
        if aliases and type(aliases[-1]) != str:
            self.reactions[name] = aliases[-1]
            aliases = aliases[:-1]
        self.actions.append(list(map(str.split, [name] + list(aliases))))
        return self

    def on(self, name, reaction):
        self.reactions[name] = reaction

    def has_reaction(self, name):
        return name in self.reactions

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

class Result:
    def __init__(self, succeed=True, message='', silence=True, side_effect=None):
        self.succeed = succeed
        self.message = message
        self.silence = silence
        self.side_effect = side_effect

class Cond:
    def __init__(self, condition, then_part, else_part):
        self.condition = condition
        self.then_part = then_part
        self.else_part = else_part

class Progn:
    def __init__(self, statements):
        self.statements = statements

def cond(predicate, then_part, else_part):
    return Cond(predicate, then_part, else_part)

def progn(*statements):
    return Progn(statements)

def fail(message='', silence=True):
    '''
    Don't continue the action and print the message to the screen
    '''
    return Result(False, message=message, silence=silence)

def info(message='', silence=False):
    return Result(True, message, silence)

def succeed(message='', silence=True):
    '''        
    Continue with the action and print the message to the screen
    '''
    return Result(True, message, silence)

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

        self.visited_rooms = set()

        self.silence = False

    def set_go_action_name(self, action_name):
        self.go_action_name = action_name

    def set_look_action_name(self, action_name):
        self.look_action_name = action_name

    def set_take_action_name(self, action_name):
        self.take_action_name = action_name

    def print(self, *message):
        if not self.silence:
            print(*message)

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

    def exec_reaction(self, reaction, source_object=None, target_object=None):
        preds = {
            'inventory_has': lambda object: object in self.character.inventory,
            'in_room': lambda room: room == self.character.room,
            'has_visited': lambda room: room in self.visited_rooms
        }

        source = None if not source_object else source_object.name
        target = None if not target_object else target_object.name

        def default_to_source(input):
            if input == None:
                return source
            else:
                return input
        if type(reaction) == Cond:
            was_true = False
            if type(reaction.condition) == Predicate:
                was_true = preds[reaction.condition.name](*reaction.condition.args)
            else:
                raise Exception('Unknown condition')
            if was_true:
                return self.exec_reaction(reaction.then_part, source_object, target_object)
            else:
                return self.exec_reaction(reaction.else_part, source_object, target_object)
        if isinstance(reaction, SideEffect):
            reaction.call(self, source, target)
        elif type(reaction) == Progn:
            last_result = None
            for statement in reaction.statements:
                last_result = self.exec_reaction(statement, source_object, target_object)
            return last_result
        elif type(reaction) == Result:
            return reaction

    def in_room(self, room_name):
        def func():
            return self.character.room == room_name
        return func

    def go(self, direction):
        '''
        Moves the character to a room in this direction
        '''
        next_room = self.rooms.go(self.character.room, direction)
        if not next_room:
            self.print('You cannot go %s' % direction)
        else:
            result = None
            for room in self.character.room_enter_callbacks:
                if room == next_room:
                    result = self.exec_reaction(self.character.room_enter_callbacks[room])
                    break;

            if result and result.message:
                self.print(result.message)
            if result and not result.succeed:
                return
            
            for room in self.character.room_exit_callbacks:
                if room == self.character.room:
                    result = self.exec_reaction(self.character.room_exit_callbacks[room])
                    break;

            if result and result.message:
                self.print(result.message)
                self.silence = result.silence                
            if not result or result.succeed:
                self.character.room = next_room
                self.print_room()

            self.visited_rooms.add(self.character.room)
            
            self.silence = False

    def execute(self, string):
        self.silence = False
        failed = False

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

        notified, reaction_result = self.objects.notify(action, source_object, target_object)

        if tokens:
            failed = True
            self.print('I don\'t understand.')
        elif reaction_result and not reaction_result.succeed:
            # for interrupting normal actions
            pass
        elif self.actions.has_reaction(action): # if the action has a custom reaction
            result = self.exec_reaction(self.actions.reactions[action], source_object, target_object)
            if result:
                if not result.succeed and not result.message:
                    failed = True
                    self.print('That didn\'t work.')
        # still allow for callbacks if it doesn't have the action
        elif not notified and source_object and action not in source_object.actions:
            if source_object.name not in self.rooms.get(self.character.room).objects and source_object.name not in self.character.inventory:
                self.print('I don\'t see a %s anywhere.' % source_object)
            else:
                self.print('You can\'t %s that.' % action)
                
            failed = True
        elif action == 'use':
            if not source_object:
                failed = True
                print('Use what?')
            elif not target_object:
                failed = True
                print('Use %s on what?' % source_object)
            else:
                if source_object.name not in self.character.inventory and target_object.name not in self.character.inventory:
                    failed = True
                    print('You don\'t have that')
                else:
                    message = 'You use the %s on the %s' % (source_object, target_object)
                    if reaction_result:
                        if not reaction_result.succeed:
                            failed = True
                            print('That didn\'t work.')
                    else:
                        print('Nothing happens.')
        elif action == self.go_action_name:
            if not direction:
                failed = True
                self.print('You must give a valid direction to go')
            else:
                self.go(direction)
        elif action == self.look_action_name:
            if not source_object:
                self.print_room()
            else:
                self.print(source_object.description)
        elif action == self.take_action_name:
            if not source_object:
                self.print('Take what?')
            elif source_object.name in room.objects:
                if self.character.add_to_inventory(source_object.name):
                    print('You pick up the %s.' % source_object)
                    room.objects.remove(source_object.name)
                else:
                    failed = True
                    print('Your inventory is out of room.')
            else:
                failed = True
                self.print('There is no %s in here.' % source_object)
        elif action == 'drop':
            if source_object and source_object.name in self.character.inventory:
                room.objects.append(source_object.name)
                self.character.inventory.remove(source_object.name)
            else:
                print('You don\'t have a %s.' % source_object)
                failed = True
        elif action == 'inventory':
            if self.character.inventory:
                self.print('You have:\n\t' + '\n\t'.join(map(lambda x: ('a ' + x).title(), self.character.inventory)))
            else:
                self.print('Your inventory is empty.')
        elif not notified:
            failed = True
            self.print('I don\'t understand.')

        if reaction_result:
            if not failed and reaction_result and reaction_result.message:
                print(reaction_result.message)
            elif not reaction_result.succeed and not reaction_result.message:
                print('That didn\'t work.')
            

    def print_room(self):
        room = self.rooms.get(self.character.room)
        self.print(room.name.title())
        self.print('\t', room.description)
        adjacent_rooms = self.rooms.get_adjacent_rooms(self.character.room)

        self.print()        
        for direction in adjacent_rooms:
            self.print('%s is to the %s.' % (adjacent_rooms[direction].title(), direction))

        if room.objects:
            objects = sorted(room.objects.copy())
            if len(objects) > 1:
                objects.insert(-1, 'and')
                
            self.print('There is a %s here.' % ', '.join(objects))
            
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
