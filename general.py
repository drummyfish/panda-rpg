RESOURCE_PATH = "resources/"

## Represents a model that has either static or animated frame animated texture.

class AnimatedTextureModel:
  def __init__(self, animated_texture_model=None):
    if animated_texture_model == None:
      self.model_name = ""
      self.texture_names = []
      self.framerate = 1.0
    else:
      self.model_name = animated_texture_model.model_name
      self.framerate = animated_texture_model.framerate
    
      self.texture_names = []

      for texture_name in animated_texture_model.texture_names:
        self.texture_names.append(texture_name)

## Represents one level tile.

class LevelTile:
  def __init__(self, level_tile=None):
    if level_tile == None:
      self.wall = False                                ##< whether the tile is a wall (True) or floor (False)
      self.ceiling = False                             ##< whether the tile has a ceiling (ceiling can also be above walls)
      self.ceiling_height = 1
      self.floor_orientation = 0                       ##< rotation of the floor, possible values: 0, 1, 2, 3
      self.wall_model = AnimatedTextureModel()         ##< model for wall 
      self.floor_model = AnimatedTextureModel()        ##< model for floor
      self.ceiling_model = AnimatedTextureModel()      ##< model for ceiling
    else:                                              # make deep copy
      self.wall = level_tile.wall
      self.ceiling = level_tile.ceiling
      self.ceiling_height = level_tile.ceiling_height
      self.floor_orientation = level_tile.floor_orientation
      self.wall_model = AnimatedTextureModel(level_tile.wall_model) 
      self.floor_model = AnimatedTextureModel(level_tile.floor_model)        
      self.ceiling_model = AnimatedTextureModel(level_tile.ceiling_model)      
    
## Represents a level prop, for example a column. Prop has its position and orientation
#  but doesnt affect anything in the game and has no colissions.

class LevelProp:
  def __init__(self, position=[0.0,0.0], orientation=0):
    self.model = AnimatedTextureModel()
    self.position = position
    self.orientation = orientation       ##< rotation in degrees

class Level:
  def __init__(self, width, height, default_tile=None):
    self.layout = [[None for i in range(height)] for j in range(width)]
    self.width = width
    self.height = height
    self.skybox_texture = ""
    self.props = []

    for i in range(len(self.layout)):
      for j in range(len(self.layout[0])):
        if default_tile == None:
          self.layout[i][j] = LevelTile()
        else:
          self.layout[i][j] = default_tile

  def add_prop(self, prop):
    self.props.append(prop)

  def get_props(self):
    return self.props

  def get_width(self):
    return self.width

  def get_height(self):
    return self.height
  
  def set_skybox_texture(self, texture_name):
    self.skybox_texture = texture_name
    
  def get_skybox_texture(self):
    return self.skybox_texture

  def get_tile(self, x, y):
    return self.layout[x][y]
  
  def set_tile(self, x, y, tile):
    try:
      self.layout[x][y] = tile
    except Exception:
      pass
  
  def is_wall(self, x, y):
    if x < 0 or y < 0 or x >= self.get_width() or y >= self.get_height():
      return True
    
    return self.layout[x][y].wall
  
def make_test_level():               # DELETE THIS LATER
  floor_tile = LevelTile()
  floor_tile.wall = False
  floor_tile.floor_model.model_name = RESOURCE_PATH + "floor_flat.obj"
  floor_tile.floor_model.texture_names.append(RESOURCE_PATH + "grass.png")
  
  floor_tile2 = LevelTile()
  floor_tile2.wall = False
  floor_tile2.ceiling = True
  floor_tile2.floor_model.model_name = RESOURCE_PATH + "floor_flat.obj"
  floor_tile2.floor_model.texture_names.append(RESOURCE_PATH + "grass.png")
  floor_tile2.ceiling_model.model_name = RESOURCE_PATH + "ceiling_flat.obj"
  floor_tile2.ceiling_model.texture_names.append(RESOURCE_PATH + "t1.jpg")
    
  floor_tile3 = LevelTile()
  floor_tile3.wall = False
  floor_tile3.floor_model.model_name = RESOURCE_PATH + "floor_flat.obj"
  floor_tile3.floor_model.texture_names.append(RESOURCE_PATH + "grass.png")
  floor_tile3.floor_orientation = 1
    
  wall_tile = LevelTile()
  wall_tile.wall = True
  wall_tile.wall_model.model_name = RESOURCE_PATH + "wall_flat.obj"
  wall_tile.wall_model.texture_names.append(RESOURCE_PATH + "wall.png")
  wall_tile.wall_model.texture_names.append(RESOURCE_PATH + "grass.png")
  wall_tile.wall_model.texture_names.append(RESOURCE_PATH + "t2.jpg")
  wall_tile.wall_model.framerate = 10
    
  wall_tile2 = LevelTile()
  wall_tile2.wall = True
  wall_tile2.wall_model.model_name = RESOURCE_PATH + "wall_bulwark.obj"
  wall_tile2.wall_model.texture_names.append(RESOURCE_PATH + "wall.png")
    
  level = Level(40,30,floor_tile)
  level.set_skybox_texture(RESOURCE_PATH + "skybox.png")
 
  i_plus = 10
  j_plus = 7
 
  for i in range(20):
    for j in range(15):
      level.set_tile(i + i_plus,j + j_plus,floor_tile2)
      
      if i == 5 and j == 4:
        level.set_tile(i + i_plus,j + j_plus,floor_tile3)
 
  level.set_tile(0,1,wall_tile)
  level.set_tile(0,2,wall_tile)
  level.set_tile(0,3,wall_tile)
    
  level.set_tile(1,5,wall_tile)
  level.set_tile(1,6,wall_tile)
  level.set_tile(2,6,wall_tile)
    
  for i in range(level.get_width()):
    level.set_tile(i,0,wall_tile2)
    level.set_tile(i,level.get_height() - 1,wall_tile2)

  for i in range(15):
    level.set_tile(i,10,wall_tile2)

  for i in range(level.get_height()):
    level.set_tile(0,i,wall_tile2)
    level.set_tile(level.get_width() - 1,i,wall_tile2)

  column1 = LevelProp()
  column1.position[0] = 0.5
  column1.position[1] = 0.5
  column1.model.model_name = RESOURCE_PATH + "column_test.obj"
  column1.model.texture_names.append(RESOURCE_PATH + "wall.png")
  
  level.add_prop(column1)

  return level