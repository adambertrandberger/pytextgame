class Predicate:
    def __init__(self, name, *args):
        self.name = name
        self.args = args

def inventory_has(object):
    return Predicate('inventory_has', object)

def has_visited(room):
    return Predicate('has_visited', room)

def in_room(room):
    return Predicate('in_room', room)
