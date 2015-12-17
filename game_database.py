## Describes an item (such as a potion, a sword etc.).

class ItemType:
  def __init__(self):
    self.name = ""
    self.model_name = ""
    self.texture_name = ""

## Describes an NPC (such as a town guard, a forest troll etc.).

class NPCType:
  def __init__(self):
    self.name = ""
    self.max_health = 100
    self.max_energy = 100

class GameDatabase:
  def __init__(self):
    self.item_types = {}
    self.npc_types = {}
    
  def get_item_types(self):
    return self.item_types
  
  def get_npc_types(self):
    return self.npc_types