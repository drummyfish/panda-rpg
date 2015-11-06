RESOURCE_PATH = "resources/"
import pickle

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
      self.steppable = not self.wall                   ##< whether the tile can be stepped on
    else:                                              # make deep copy
      self.wall = level_tile.wall
      self.ceiling = level_tile.ceiling
      self.ceiling_height = level_tile.ceiling_height
      self.floor_orientation = level_tile.floor_orientation
      self.wall_model = AnimatedTextureModel(level_tile.wall_model) 
      self.floor_model = AnimatedTextureModel(level_tile.floor_model)        
      self.ceiling_model = AnimatedTextureModel(level_tile.ceiling_model)      
      self.steppable = level_tile.steppable
    
  ## Checks if the tile is empty (has no model). Empty tile can still have ceiling.
    
  def is_empty(self):
    return (self.wall and len(self.wall_model.model_name) == 0) or (not self.wall and len(self.floor_model.model_name) == 0)
    
## Represents a level prop, for example a column. Prop has its position and orientation
#  but doesnt affect anything in the game and has no colissions.

class LevelProp:
  def __init__(self, level_prop=None, position=[0.0,0.0], orientation=0):
    if level_prop == None:
      self.model = AnimatedTextureModel()
      self.position = position             ##< (x,y) float position
      self.orientation = orientation       ##< rotation in degrees
    else:
      self.model = AnimatedTextureModel(level_prop.model)
      self.position  = level_prop.position
      self.orientation = level_prop.orientation

class Level:
  ## Class static method, saves the level into given file.
  
  def save_to_file(level, filename):
    output_file = open(filename,"w")
    pickle.dump(level,output_file)
    output_file.close()
  
  ## Class static method, loads the level from given file and returns it.
  #  the level argument has to be there because of python interpreter
  #  for some reason.
  
  def load_from_file(level, filename):
    input_file = open(filename,"r")
    result = pickle.load(input_file)
    input_file.close()
    return result
  
  def __init__(self, width, height, default_tile=None):
    self.layout = [[None for i in range(height)] for j in range(width)]
    self.width = width
    self.height = height
    self.skybox_textures = []              ##< contains names of skybox textures that are being chained between during daytime
    self.ambient_light_amount = 0.5        ##< amount of ambient light in range <0,1>
    self.fog_color = (0.5,0.5,0.5)         ##< fog color
    self.fog_distance = 10
    self.diffuse_lights = [(1.0,1.0,1.0),(0.5,0.5,0.5)]  ##< list of light colors (3-item tuples tuples) that are interpolated between during daytime
    self.props = []
    self.name = ""                         ##< level name

    for i in range(len(self.layout)):
      for j in range(len(self.layout[0])):
        if default_tile == None:
          self.layout[i][j] = LevelTile()
        else:
          self.layout[i][j] = LevelTile(default_tile)

  ## Resizes the map.

  def set_size(self, new_width, new_height):
    old_size = (self.get_width(),self.get_height())
    old_layout = self.layout
    
    self.width = new_width
    self.height = new_height
    
    self.layout = [[None for i in range(new_height)] for j in range(new_width)]
    
    for i in range(len(self.layout)):
      for j in range(len(self.layout[0])):
        try:
          self.layout[i][j] = old_layout[i][j]
        except Exception:
          self.layout[i][j] = LevelTile()

  def set_fog_distance(self,distance):
    self.fog_distance = distance

  def get_fog_distance(self):
    return self.fog_distance

  def add_prop(self, prop):
    self.props.append(prop)

  def get_props(self):
    return self.props

  def get_width(self):
    return self.width

  def set_name(self, name):
    self.name = name
    
  def get_name(self):
    return self.name

  def get_height(self):
    return self.height
  
  ## Sets the lighting properties of the level.
  #
  #  @param ambient_light_amount amount of ambient light in range <0,1>
  #  @param diffuse_lights list of light colors (3-item tuples tuples) that are interpolated between during daytime
  
  def set_light_properties(self,ambient_light_amount, diffuse_lights):
    self.ambient_light_amount = ambient_light_amount
    self.diffuse_lights = diffuse_lights
    
  def get_ambient_light_amount(self):
    return self.ambient_light_amount
  
  def get_diffuse_lights(self):
    return self.diffuse_lights
  
  ## Sets the fog color.
  #
  #  @param fog_color fog color (three item tuple of floats in range <0,1>)
  
  def set_fog_color(self, fog_color):
    self.fog_color = fog_color
    
  def get_fog_color(self):
    return self.fog_color
  
  ## Sets the names of skybox textures used for different
  #  times of day.
  #
  #  @param texture_names list of texture names, the textures
  #         will be chenged between depending on the time of day
  
  def set_skybox_textures(self, texture_names):
    self.skybox_textures = texture_names
    
  ## Gets the list of skybox texture names.
    
  def get_skybox_textures(self):
    return self.skybox_textures

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