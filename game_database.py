## Describes an item (such as a potion, a sword etc.).

class ItemType:
  def __init__(self):
    self.name = ""

## Describes an NPC (such as a town guard, a forest troll etc.).

class NPCType:
  def __init__(self):
    self.name = ""
    self.max_health = 100
    self.max_energy = 100

class GameDatabase:
  def __init__(self):
    self.items_types = []
    self.npc_types = []
    
  def get_item_types(self):
    return self.item_types
  
  def get_npc_types(self):
    return self.npc_types
  
  def add_item_type(self, item_type):
    self.item_types.append(item_type)
    
  def add_npc_type(self, npc_type):
    self.item_types.append(npc_type)