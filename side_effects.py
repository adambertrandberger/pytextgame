class SideEffect:
    def __init__(self, name, *args):
        self.name = name
        self.args = args

def add_to_inventory(object):
    return SideEffect('add_to_inventory', object)

def remove_from_inventory(object):
    return SideEffect('remove_from_inventory', object)

