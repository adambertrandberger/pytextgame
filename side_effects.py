class SideEffect:
    def __init__(self, *args):
        self.args = args
        
        self.source = None
        self.target = None

    def call(self, game, source, target):
        self.source = source
        self.target = target
        self.execute(game, *self.args)

    def default_to_source(self, input):
        return self.source if not input else input

    def default_to_target(self, input):
        return self.target if not input else input
        
    def execute(self, game, args):
        raise Exception('Must implement `execute` for SideEffect')

class AddToInventory(SideEffect):
    def execute(self, game, object):
        game.character.add_to_inventory(self.default_to_source(object), force=True)

class RemoveFromInventory(SideEffect):
    def execute(self, game, object):
        game.character.inventory.remove(self.default_to_source(object))         

class Destroy(SideEffect):
    def execute(self, game, object):
        object = self.default_to_source(object)
        if object in game.character.inventory:
            game.character.inventory.remove(object)
            
        room = game.rooms.get(game.character.room)
        if object in room.objects:
            game.rooms.get(game.character.room).objects.remove(object)

class ChangeDescription(SideEffect):
    def execute(self, game, object_name, new_description):
        for object in game.objects.objects:
            if object.name == object_name:
                object.description = new_description
                break;
            
def add_to_inventory(object=None):
    return AddToInventory(object)

def remove_from_inventory(object=None):
    return RemoveFromInventory(object)

def destroy(object=None):
    return Destroy(object)

def change_description(object, new_description):
    return ChangeDescription(object, new_description)
