from math import pi, sin, cos, radians
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import *
from pandac.PandaModules import WindowProperties
from direct.showbase import DirectObject
from direct.filter.CommonFilters import CommonFilters
from pandac.PandaModules import ClockObject
from panda3d.core import ConfigVariableBool, CullBinManager

from level import *

class Game(ShowBase, DirectObject.DirectObject):
  DAYTIME_UPDATE_COUNTER = 32
  JUMP_DURATION = 0.6                                               ##< jump duration in seconds
  CAMERA_HEIGHT = 0.7
  JUMP_EXTRA_HEIGHT = 0.3
  
  def __init__(self):
    vsync = ConfigVariableBool("sync-video")
    vsync.setValue(False)
    
    ShowBase.__init__(self)

    props = WindowProperties() 
    props.setSize(1024,768) 
    props.setCursorHidden(True) 
    props.setMouseMode(WindowProperties.M_relative)

    base.win.requestProperties(props) 

    FPS = 60
    globalClock = ClockObject.getGlobalClock()
    globalClock.setMode(ClockObject.MLimited)
    globalClock.setFrameRate(FPS)

    self.daytime = 0.0                                              ##< time of day in range <0,1>
    self.update_daytime_counter = Game.DAYTIME_UPDATE_COUNTER       ##< counts frames to update daytime effects to increase FPS
    self.collision_mask = None                                      ##< current level collision mask (2D list of bool)

    self.player_position = [0.0,0.0]                                ##< player position
    self.player_rotation = 0.0                                      ##< player rotation in degrees

    self.time_of_jump = - 0.100                                     ##< time of last player's jump
    self.in_air = False                                             ##< if the player is in air (jumping)

    base.setFrameRateMeter(True)

    self.filters = CommonFilters(base.win,base.cam)   
    self.filters.setBloom(size="small",desat=1)

    # initialise input handling:

    self.camera_time_before = 0
    self.camera_movement_speed = 4
    self.camera_rotation_speed = 0.3

    base.disableMouse()

    self.taskMgr.add(self.camera_task,"camera_task")
    self.taskMgr.add(self.mouse_position_task,"mouse_position_task")
    self.taskMgr.add(self.time_task,"time_task")

    self.input_state = {}   # contains state of mouse and keyboard

    self.input_state["mx"] = 0
    self.input_state["my"] = 0
    self.input_state["mxf"] = 0.0
    self.input_state["myf"] = 0.0

    for key in ["w","s","a","d","q","e","mouse1","mouse3"]:
      self.input_state[key] = False
      self.accept(key,self.handle_input,[key,True])
      self.accept(key + "-up",self.handle_input,[key,False])

    level = Level.load_from_file("test_output.txt")
    
    self.collision_mask = level.get_collision_mask()
    self.setup_environment_scene(level)

  def handle_input(self,input_name,input_value):
    self.input_state[input_name] = input_value

  def mouse_position_task(self, task):
    if base.mouseWatcherNode.hasMouse():
      x = base.mouseWatcherNode.getMouseX()
      y = base.mouseWatcherNode.getMouseY()
      
      size = base.getSize()
      
      self.input_state["mxf"] = x   # float
      self.input_state["myf"] = y   
      
      self.input_state["mx"] = int(x * size[0] / 2)   # pixel
      self.input_state["my"] = int(y * size[1] / 2)

    return task.cont

  def time_task(self, task):
    self.daytime = (task.time / 300) % 1
    
    if self.update_daytime_counter > 0:
      self.update_daytime_counter -= 1
      return task.cont
    else:
      self.update_daytime_counter = Game.DAYTIME_UPDATE_COUNTER
      self.set_daytime(self.daytime)
      return task.cont
  
  ## Computes a new position of object in movement, respecting the
  #  collisions with level geometry.
  #
  #  @param position object position ((x,y) float tuple)
  #  @param direction object orientation in degrees, starting pointing right, going CCW
  #  @param distance distance to be travelled
  #  @return new position as a tuple
  
  def move_with_collisions(self, position, direction, distance):    
    padding_size = 0.2
    bias = 0.01

    def position_to_tile(float_position):
      return (int(round(float_position[0])),int(round(float_position[1])))
    
    def tile_is_walkable(tile_position):
      try:
        return self.collision_mask[tile_position[0]][tile_position[1]]
      except Exception:
        return False
    
    def position_collides(float_position):
      # Checks if position collides taking padding into account. Returns list of
      # collided paddings:
      #      0
      #    1   3    
      #      2
      # Empty list is returned for no collision.
      
      tile_position = position_to_tile(float_position)
      
      result = []
      
      if not tile_is_walkable(tile_position):
        return [0,1,2,3]
      
      position_within_tile = (float_position[0] - tile_position[0] + 0.5,float_position[1] - tile_position[1] + 0.5)
      
      if position_within_tile[0] < padding_size and not tile_is_walkable((tile_position[0] - 1,tile_position[1])):
        result.append(1)
      elif position_within_tile[0] > 1.0 - padding_size and not tile_is_walkable((tile_position[0] + 1,tile_position[1])):
        result.append(3)
      
      elif position_within_tile[1] < padding_size and not tile_is_walkable((tile_position[0],tile_position[1] - 1)):
        result.append(0)
      elif position_within_tile[1] > 1.0 - padding_size and not tile_is_walkable((tile_position[0],tile_position[1] + 1)):
        result.append(2)
      
      return result
    
    new_position = [position[0],position[1]]
    
    direction = direction % 360
    
    new_position[0] += cos(radians(direction)) * distance
    new_position[1] -= sin(radians(direction)) * distance
    
    collisions = position_collides(new_position)
    
    if len(collisions) == 0:   # no collision for new position => OK
      return new_position
    
    current_tile = position_to_tile(position)
    
    if 3 in collisions:
      new_position[0] = current_tile[0] + 0.5 - padding_size - bias
    elif 1 in collisions:
      new_position[0] = current_tile[0] - 0.5 + padding_size + bias
    
    collisions = position_collides(new_position)
    
    if len(collisions) == 0:   # no collision for new position => OK
      return new_position
    
    if 0 in collisions:
      new_position[1] = current_tile[1] - 0.5 + padding_size + bias
    elif 2 in collisions:
      new_position[1] = current_tile[1] + 0.5 - padding_size - bias
    
    if len(position_collides(new_position)) == 0:
      return new_position
    
    return position
  
  def camera_task(self, task):
    current_position = self.camera.getPos()
   
    camera_forward = self.camera.getRelativeVector(self.render,VBase3(0,1,0))
    camera_right = self.camera.getRelativeVector(self.render,VBase3(1,0,0))

    new_position = [self.player_position[0],self.player_position[1]]

    time_difference = task.time - self.camera_time_before
    
    self.camera_time_before = task.time

    distance = self.camera_movement_speed * time_difference

    self.in_air = task.time <= self.time_of_jump + Game.JUMP_DURATION

    if self.input_state["w"]:
      self.player_position = self.move_with_collisions(self.player_position,self.player_rotation,distance)

    if self.input_state["s"]:
      self.player_position = self.move_with_collisions(self.player_position,self.player_rotation + 180,distance)

    if self.input_state["a"]:
      self.player_position = self.move_with_collisions(self.player_position,self.player_rotation + 90,distance)

    if self.input_state["d"]:
      self.player_position = self.move_with_collisions(self.player_position,self.player_rotation + 270,distance)
    
    if not self.in_air and self.input_state["e"]:
      self.time_of_jump = task.time
    
    current_rotation = self.camera.getHpr()
    current_position = self.camera.getPos()
      
    self.player_rotation = current_rotation[0] % 360
      
    new_rotation = [current_rotation.getX(),current_rotation.getY(),current_rotation.getZ()] 

    window_center = (base.win.getXSize() / 2, base.win.getYSize() / 2)
    base.win.movePointer(0, window_center[0], window_center[1])
      
    mouse_difference = (self.input_state["mx"],self.input_state["my"])
      
    new_rotation[0] -= mouse_difference[0] * self.camera_rotation_speed
    new_rotation[1] += mouse_difference[1] * self.camera_rotation_speed 
    
    self.camera.setHpr(new_rotation[0],max(min(new_rotation[1],90),-90),new_rotation[2])

    camera_height = Game.CAMERA_HEIGHT
    
    if self.in_air:
      jump_phase = (task.time - self.time_of_jump) / Game.JUMP_DURATION
      
      camera_height += Game.JUMP_EXTRA_HEIGHT * (1 - (jump_phase * 2 - 1) ** 2)
      
     

    self.camera.setPos(self.player_position[1],self.player_position[0],camera_height)

    return task.cont

  ## Sets the time of the day as a value in interval <0,1> to affect the scene (lighting, skybox texture, ...).

  def set_daytime(self, daytime):    
    # TODO: HUGELY OPTIMISE THIS

    try:
      self.skybox_node = self.skybox_node
      self.skybox2_node = self.skybox2_node
      self.diffuse_light_node = self.diffuse_light_node
      self.ambient_light_node = self.ambient_light_node
      self.skybox_texture_index_before = self.skybox_texture_index_before
    except Exception:
      self.skybox_node = self.render.find("**/skybox")
      self.skybox2_node = self.render.find("**/skybox2")
      self.diffuse_light_node = self.render.find("**/diffuse")
      self.ambient_light_node = self.render.find("**/ambient")
      self.skybox_texture_index_before = -1
    
    if not self.skybox_node.isEmpty():      # handle skybox, if there is any
      texture_index = int(len(self.skybox_textures) * self.daytime)
      fraction = 1.0 / len(self.skybox_textures)
      remainder = self.daytime - fraction * texture_index
      ratio = remainder / fraction
    
      transition_range = 0.2
      remaining_range = (1.0 - transition_range) / 2.0
    
      if ratio < remaining_range:
        ratio = 0.0
      elif ratio < 1.0 - remaining_range:
        ratio = (ratio - remaining_range) / transition_range
      else:
        ratio = 1.0
    
      self.skybox2_node.setAlphaScale(ratio)
    
      if texture_index != self.skybox_texture_index_before:   # switch front and back skybox
        self.skybox_texture_index_before = texture_index
        self.skybox_node.setTexture(self.skybox_textures[texture_index])
        self.skybox2_node.setTexture(self.skybox_textures[(texture_index + 1) % len(self.skybox_textures)])
      
    # set lights:
    
    if self.diffuse_light_node.isEmpty() or self.ambient_light_node.isEmpty():
      return
    
    light_index = int(len(self.diffuse_lights) * self.daytime)
    fraction = 1.0 / len(self.diffuse_lights)
    remainder = self.daytime - fraction * light_index
    ratio = remainder / fraction
    one_minus_ratio = 1.0 - ratio
    
    color1 = self.diffuse_lights[light_index]
    color2 = self.diffuse_lights[(light_index + 1) % len(self.diffuse_lights)]

    light_color = (color1[0] * one_minus_ratio + color2[0] * ratio,color1[1] * one_minus_ratio + color2[1] * ratio,color1[2] * one_minus_ratio + color2[2] * ratio)
    
    self.diffuse_light_node.node().setColor(VBase4(light_color[0],light_color[1],light_color[2],1))

    phase = sin(self.daytime * 2 * pi)
    phase2 = cos(self.daytime * 2 * pi)

    #self.diffuse_light_node.setHpr(phase * 10,-90 + phase * 20,0)   
    
    self.diffuse_light_node.setPos(phase2 * -5,phase * -10,20)
    self.diffuse_light_node.lookAt(self.camera)

    ambient_color = (light_color[0] * self.ambient_light_amount, light_color[1] * self.ambient_light_amount, light_color[2] * self.ambient_light_amount)
    self.ambient_light_node.node().setColor(VBase4(ambient_color[0],ambient_color[1],ambient_color[2],1))

  ## Sets up 3D environment node based on provided level layout.

  def setup_environment_scene(self, level):
    models = {}      # model cache
    textures = {}    # texture cache
    
    def load_model(model_name):                # loads model into 'models' cache (only if it hasn't been loaded laready)
      if not model_name in models:
        models[model_name] = self.loader.loadModel(RESOURCE_PATH + model_name)
    
    def load_texture(texture_name):            # loads texture into 'textures' cache (only if it hasn't been loaded laready)
      if not texture_name in textures:
        textures[texture_name] = self.loader.loadTexture(RESOURCE_PATH + texture_name)
        textures[texture_name].setMinfilter(Texture.FTLinearMipmapLinear)

    def make_node(animated_texture_model):     # makes a node out of AnimatedTextureModel object, handles loading models and textures and caches
      load_model(animated_texture_model.model_name)
      
      model = models[animated_texture_model.model_name]
      
      textures_for_node = []
      
      for texture_name in animated_texture_model.texture_names:
        if len(texture_name) != 0:
          load_texture(texture_name)
          textures_for_node.append(textures[texture_name])
      
      framerate = animated_texture_model.framerate
      
      if len(textures_for_node) in [0,1]:
        node = PandaNode("node")
        node_path = NodePath(node)
        result = NodePath(node_path)
        model.instanceTo(node_path)
        
        if len(textures_for_node) == 1:
          node_path.setTexture(textures_for_node[0])
        
        return node
      else:  # node with animated texture
        sequence_node = SequenceNode("sequence")
        sequence_node.setFrameRate(framerate)
        node_path = NodePath(sequence_node)
      
        for texture in textures_for_node:
          helper_node = node_path.attachNewNode("frame")
          model.instanceTo(helper_node)
          helper_node.setTexture(texture)
        
        sequence_node.loop(True)
      
        return sequence_node
    
    fog = Fog("fog")
    fog_color = level.get_fog_color()
    fog.setColor(fog_color[0],fog_color[1],fog_color[2])
    fog.setExpDensity(0.1)
    fog.setLinearRange(level.get_fog_distance(),level.get_fog_distance() + 5)  

    base.camLens.setFov(105)       # setup the camera
    base.camLens.setNear(0.01)
    base.camLens.setFar(level.get_fog_distance() + 10)
    
    level_node_path = NodePath("level")
    level_node_path.reparentTo(self.render)
    level_node_path.setFog(fog)
    
    for j in range(level.get_height()):
      for i in range(level.get_width()):
        tile = level.get_tile(i,j)
        
        if not tile.is_empty():
          if not tile.wall:                            # floor tile
            tile_node_path = level_node_path.attachNewNode(make_node(level.get_tile(i,j).floor_model))
            tile_node_path.setPos(i,0,j)
            tile_node_path.setHpr(0,0,level.get_tile(i,j).floor_orientation * 90)
          else:                                                       # wall
            offsets = [[0,0.5], [0.5,0], [-0.5,0], [0,-0.5]] # down, right, left, up
            rotations = [-90, 0, 180, 90]
            neighbours = [[0,1], [1,0], [-1,0], [0,-1]]

            for k in range(4):  # 4 walls (one for each direction)
              # check if the wall needs to be created:

              if level.is_wall(i + neighbours[k][0],j + neighbours[k][1]):
                continue

              tile_node_path = level_node_path.attachNewNode(make_node(level.get_tile(i,j).wall_model))
              tile_node_path.setPos(i + offsets[k][0],0,j + offsets[k][1])
              tile_node_path.setHpr(0,0,rotations[k])

        if level.get_tile(i,j).ceiling:
          tile_node_path = level_node_path.attachNewNode(make_node(level.get_tile(i,j).ceiling_model))
          tile_node_path.setPos(i,level.get_tile(i,j).ceiling_height,j)

    for prop in level.get_props():
      tile_node_path = level_node_path.attachNewNode(make_node(prop.model))
      tile_node_path.setPos(prop.position[0] - 0.5,0,prop.position[1] - 0.5)
      tile_node_path.setHpr(0,0,prop.orientation)

    skybox_texture_names = level.get_skybox_textures()
    
    if len(skybox_texture_names) > 0:      # no skybox textures => no skybox
      # back skybox:
      skybox = self.loader.loadModel(RESOURCE_PATH + "skybox.obj")
      skybox.setName("skybox")
      skybox.reparentTo(self.camera)
      skybox.setHpr(0,90,0)
      skybox.set_bin("background",0)
      skybox.set_depth_write(False)
      skybox.set_compass()
      skybox_material = Material()
      skybox_material.setEmission((1, 1, 1, 1))
      skybox.setMaterial(skybox_material)

      # front skybox:
      skybox2 = self.loader.loadModel(RESOURCE_PATH + "skybox.obj")
      skybox2.setName("skybox2")
      skybox2.reparentTo(self.camera)
      skybox2.setHpr(0,90,0)
      skybox2.set_bin("background",1)
      skybox2.set_depth_write(False)
      skybox2.set_compass()
      skybox2.setMaterial(skybox_material)
      skybox2.setTransparency(TransparencyAttrib.MAlpha)
  
      self.skybox_textures = []
    
      for skybox_texture_name in skybox_texture_names:
        load_texture(skybox_texture_name)
        self.skybox_textures.append(textures[skybox_texture_name])

    # TODO set transparency only for nodes that really need it!
    level_node_path.setTransparency(True)
    level_node_path.reparentTo(self.render)
    level_node_path.setHpr(90, 90, 0)

    # manage lights:

    ambient_light = AmbientLight('ambient')
    ambient_light_path = render.attachNewNode(ambient_light) 
    ambient_light.setColor(VBase4(level.get_ambient_light_amount(),level.get_ambient_light_amount(),level.get_ambient_light_amount(),1))
    render.setLight(ambient_light_path)
    
    directional_light = DirectionalLight('diffuse')
    directional_light_path = self.camera.attachNewNode(directional_light)
    directional_light_path.setHpr(0,-90,0)   
    directional_light_path.setPos(0,0,20)
    directional_light.getLens().setNearFar(10,30)   
    directional_light.getLens().setFilmSize(20,20)
    directional_light_path.set_compass()
    directional_light.setColor(VBase4(0.7,0.7,0.7,1))
    render.setLight(directional_light_path)

    self.diffuse_lights = level.get_diffuse_lights()
    self.ambient_light_amount = level.get_ambient_light_amount()

    #directional_light.setShadowCaster(True,256,256)
    self.render.setShaderAuto()

    self.set_daytime(0.5)

app = Game()
app.run()
