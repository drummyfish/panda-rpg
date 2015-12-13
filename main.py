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
from direct.gui.OnscreenText import OnscreenText
from direct.interval.LerpInterval import LerpPosInterval

from general import *
from level import *

class Game(ShowBase, DirectObject.DirectObject):
  DAYTIME_UPDATE_COUNTER = 32
  JUMP_DURATION = 0.6                    ##< jump duration in seconds
  CAMERA_HEIGHT = 0.7
  JUMP_EXTRA_HEIGHT = 0.3
  FOG_RANGE = 5
  USE_DISTANCE = 2                       ##< distance within which objects can be used by the player                           
  
  PROFILING = False                      ##< turn on for Panda3D profiling
  
  def __init__(self):
    vsync = ConfigVariableBool("sync-video")
    vsync.setValue(False)
    
    ShowBase.__init__(self)

    if Game.PROFILING:
      PStatClient.connect()              # <---- uncomment for profiling

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
    self.use_pressed = False                                        ##< whether the use key way pressed

    self.node_object_mapping = {}                                   ##< contains mapping of some node names to their corresponding objects
    self.focused_prop = None                                        ##< references a LevelProp item that the player is currently looking at

    base.setFrameRateMeter(True)

    self.filters = CommonFilters(base.win,base.cam)   
    self.filters.setBloom(size="small",desat=1)

    # initialise input handling:

    self.camera_time_before = 0
    self.camera_movement_speed = 4
    self.camera_rotation_speed = 0.3

    if not Game.PROFILING:
      base.disableMouse()

    self.taskMgr.add(self.camera_task,"camera_task")
    self.taskMgr.add(self.mouse_position_task,"mouse_position_task")
    self.taskMgr.add(self.time_task,"time_task")

    self.input_state = {}   # contains state of mouse and keyboard

    self.input_state["mx"] = 0
    self.input_state["my"] = 0
    self.input_state["mxf"] = 0.0
    self.input_state["myf"] = 0.0

    for key in ["w","s","a","d","q","e","space","mouse1","mouse3"]:
      self.input_state[key] = False
      self.accept(key,self.handle_input,[key,True])
      self.accept(key + "-up",self.handle_input,[key,False])

    self.level = Level.load_from_file("test_exterior.txt")         ##< contains the level data
    self.collision_mask = self.level.get_collision_mask()
    self.setup_environment_scene(self.level)
    
  def reenable_usage_task(self, prop, task):
    prop.disable_usage = False
    return task.done
    
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

  ## Updates the daytime (the variable and once every DAYTIME_UPDATE_COUNTER
  #  updates the scene accoordingly).

  def time_task(self, task):
    self.daytime = (task.time / 100) % 1
    
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
    
    if self.input_state["space"]:
      if not self.use_pressed:
        
        if self.focused_prop != None and not self.focused_prop.disable_usage:
          self.run_scripts(self.focused_prop.scripts_use,event_type="use",caller=self.focused_prop)
          
        self.use_pressed = True
    else:
      self.use_pressed = False
    
    current_rotation = self.camera.getHpr()
    current_position = self.camera.getPos()
      
    self.player_rotation = current_rotation[0] % 360
    new_rotation = [current_rotation.getX(),current_rotation.getY(),current_rotation.getZ()] 
    window_center = (base.win.getXSize() / 2, base.win.getYSize() / 2)
    
    if base.mouseWatcherNode.hasMouse() and not Game.PROFILING:
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

    # handle ray picking:

    self.picker_ray.setFromLens(base.camNode,0,0)
 
    self.collission_traverser.traverse(self.level_node_path)
    self.focused_prop = None
    
    caption = ""
    
    if self.collission_handler.getNumEntries() > 0:
      self.collission_handler.sortEntries()
      picked_object = self.collission_handler.getEntry(0).getIntoNodePath()
      picked_node = picked_object.getNodes()[2]
      
      distance = self.camera.getDistance(picked_object)
      
      if distance > Game.USE_DISTANCE:
        picked_object = None
        picked_node = None
      
      try:
        picked_name = picked_node.getName()
        self.focused_prop = self.node_object_mapping[picked_name]
        caption = self.focused_prop.caption
      except Exception:
        pass
      
    if caption != self.description_text.getText():        
      self.description_text.setText(caption)
      
    return task.cont

  ## Sets the time of the day as a value in interval <0,1> to affect the scene (lighting, skybox texture, ...).

  def set_daytime(self, daytime):    
    # TODO: OPTIMISE THIS as it will be run frequently

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
      
    # manage lights:
    
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
    ambient_color = (light_color[0] * self.ambient_light_amount, light_color[1] * self.ambient_light_amount, light_color[2] * self.ambient_light_amount)
    self.ambient_light_node.node().setColor(VBase4(ambient_color[0],ambient_color[1],ambient_color[2],1))

  ## Sets up the 3D scene (including camera, lights etc.) provided on provided level layout.

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
        
        node_path.set_bin("opaque",1)
        
        return node
      else:  # node with animated texture
        sequence_node = SequenceNode("sequence")
        sequence_node.setFrameRate(framerate)
        node_path = NodePath(sequence_node)
      
        for texture in textures_for_node:
          helper_node = node_path.attachNewNode("frame")
          model.instanceTo(helper_node)
          helper_node.setTexture(texture)
        
        node_path.set_bin("opaque",1)
        
        sequence_node.loop(True)
      
        return sequence_node
     
    cull_bin_manager = CullBinManager.getGlobalPtr()
    cull_bin_manager.setBinType(name="opaque",type=cull_bin_manager.BT_state_sorted)
      
    fog = Fog("fog")
    fog_color = level.get_fog_color()
    fog.setColor(fog_color[0],fog_color[1],fog_color[2])
    fog.setLinearRange(level.get_fog_distance(),level.get_fog_distance() + Game.FOG_RANGE)  

    # setup the camera:
    
    base.camLens.setFov(105)       
    base.camLens.setNear(0.01)
    base.camLens.setFar(level.get_fog_distance() + Game.FOG_RANGE + 5)   # set far plane a little behind the fog
    
    self.level_node_path = NodePath("level")
    self.level_node_path.reparentTo(self.render)

    # make the level:
    
    for j in range(level.get_height()):
      for i in range(level.get_width()):
        tile = level.get_tile(i,j)
        
        if not tile.is_empty():
          if not tile.wall: # floor tile
            tile_node_path = self.level_node_path.attachNewNode(make_node(level.get_tile(i,j).floor_model))
            tile_node_path.setPos(j,i,0)
            tile_node_path.setHpr(90,90,level.get_tile(i,j).floor_orientation * 90)
          else:             # wall
            offsets = [[0,0.5], [0.5,0], [-0.5,0], [0,-0.5]] # down, right, left, up
            rotations = [-90, 0, 180, 90]
            neighbours = [[0,1], [1,0], [-1,0], [0,-1]]

            for k in range(4):  # 4 walls (one for each direction)
              # check if the wall needs to be created:

              if level.is_wall(i + neighbours[k][0],j + neighbours[k][1]):
                continue

              tile_node_path = self.level_node_path.attachNewNode(make_node(level.get_tile(i,j).wall_model))
              tile_node_path.setPos(j + offsets[k][1],i + offsets[k][0],0)
              tile_node_path.setHpr(90,90,rotations[k])

        if level.get_tile(i,j).ceiling:
          tile_node_path = self.level_node_path.attachNewNode(make_node(level.get_tile(i,j).ceiling_model))
          tile_node_path.setPos(i,level.get_tile(i,j).ceiling_height,j)

    self.level_node_path.flattenLight()             # for optimisation => level geometry won't change

    # add props to the level:

    prop_counter = 0

    for prop in level.get_props():
      prop_node_path = self.level_node_path.attachNewNode(make_node(prop.model))
      name = "p" + str(prop_counter)              # 'p' for prop
      prop_node_path.getNodes()[0].setName(name)
      self.node_object_mapping[name] = prop
      prop.node_path = prop_node_path             # add new property to the prop: node path reference (for later dynamic modifications)
      prop.disable_usage = False                  # helper property
      
      prop_counter += 1
      
      prop_node_path.setPos(prop.position[1] - 0.5,prop.position[0] - 0.5,0)
      prop_node_path.setHpr(90,90,prop.orientation)
      
    skybox_texture_names = level.get_skybox_textures()
    
    self.level_node_path.setFog(fog)
    self.level_node_path.setTransparency(TransparencyAttrib.MBinary,1)
    self.level_node_path.set_bin("opaque",1)
    
    # setup the skybox (if there are any textures, otherwise don't create it at all)
    
    if len(skybox_texture_names) > 0:
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
      skybox.setLightOff(1)

      # front skybox, will be blend with back skybox using transparency (multitexturing is not a good solution because of low performance):
      skybox2 = self.loader.loadModel(RESOURCE_PATH + "skybox.obj")
      skybox2.setName("skybox2")
      skybox2.reparentTo(self.camera)
      skybox2.setHpr(0,90,0)
      skybox2.set_bin("background",1)
      skybox2.set_depth_write(False)
      skybox2.set_compass()
      skybox2.setMaterial(skybox_material)
      skybox2.setTransparency(TransparencyAttrib.MAlpha)
      skybox.setLightOff(1)
  
      self.skybox_textures = []
    
      for skybox_texture_name in skybox_texture_names:
        load_texture(skybox_texture_name)
        self.skybox_textures.append(textures[skybox_texture_name])

    self.level_node_path.reparentTo(self.render)

    # setup the lights:
    
    ambient_light = AmbientLight('ambient')
    ambient_light_path = render.attachNewNode(ambient_light) 
    render.setLight(ambient_light_path)
    
    directional_light = DirectionalLight('diffuse')
    directional_light_path = render.attachNewNode(directional_light)
    directional_light_path.setHpr(30,-80,0)
    directional_light_path.set_compass()
    render.setLight(directional_light_path)

    # setup the fog blocker (a wall behind the fog, acting as a horizon):

    fog_blocker = self.loader.loadModel(RESOURCE_PATH + "fog_blocker.obj")
    fog_blocker.reparentTo(self.camera)
    fog_blocker.setHpr(0,90,0)
    fog_blocker_scale = level.get_fog_distance() + Game.FOG_RANGE + 2;
    fog_blocker.setScale(fog_blocker_scale,1,fog_blocker_scale)
    fog_blocker.set_compass()
    fog_blocker_material = Material()
    fog_blocker_material.setAmbient(VBase4(0,0,0,1))
    fog_blocker_material.setEmission(VBase4(fog_color[0],fog_color[1],fog_color[2],1))
    fog_blocker_material.setDiffuse(VBase4(0,0,0,1))
    fog_blocker.setMaterial(fog_blocker_material)

    self.diffuse_lights = level.get_diffuse_lights()
    self.ambient_light_amount = level.get_ambient_light_amount()

    self.render.setShaderAuto()
    self.set_daytime(0.5)
    
    # setup ray picker:
    
    self.collission_traverser = CollisionTraverser()
    self.collission_handler = CollisionHandlerQueue()
    picker_node = CollisionNode('ray')
    picker_node_path = self.camera.attachNewNode(picker_node)
    picker_node.setFromCollideMask(GeomNode.getDefaultCollideMask())
    self.picker_ray = CollisionRay()
    picker_node.addSolid(self.picker_ray)
    self.collission_traverser.addCollider(picker_node_path,self.collission_handler)
    
    # setup the GUI:
    
    # TODO: change this to regulart cross later:
    self.cross = OnscreenText(text="+",parent=base.a2dBackground,pos=(0,0), scale=0.08,fg=(1, 1, 1, 1),shadow=(0, 0, 0, .5))
    self.description_text = OnscreenText(text="",parent=base.a2dBackground,pos=(0,-0.15), scale=0.08,fg=(1, 1, 1, 1),shadow=(0, 0, 0, .5))

    # run the init scripts:
 
    for prop in level.get_props():
      try:
        self.run_scripts(prop.scripts_load,event_type="load",caller=prop)
      except Exception:
        pass
        
  ## Runs given game script in the current context.
  #  @param filename name of the script (including extension but without the resource path)
  #  @param caller object that caused the script to be run
  #  @param event_type event type as a string
  #  @param params optional additional parameters

  def run_script(self, filename, caller=None, event_type=None, params=None):
    # set the local variables for the script:
    
    game = self        
    parameters = params
    source = caller
    event_type = event_type
    
    try:
      execfile(RESOURCE_PATH + filename)
    except Exception as e:
      print("error running script '" + filename + "':")
      print(e)
   
  ## Runs all scripts in a list.
   
  def run_scripts(self, filenames, caller=None, event_type=None, params=None):
    for filename in filenames:
      self.run_script(filename,caller,event_type,params)
  
  # ==================================== SCRIP API ====================================
  # The following functions are intended to be called from the game scripts, but can also
  # be called from the core source as well. Core functions however should never be called
  # from the scripts. The following local variables are available withing the script:
  #
  # game - reference to this Game object (self)
  # source - object that caused the script to be called
  # event_type - type of the event that caused the script to be called as a string
  # parameters - additional parameters
  
  def script_print(self, what):
    print(what)
    
  ## Gets the player position.
  #  @return player position as (x,y) tuple, note that this differs from
  #    the internal player position by half a square to match other
  #    positions
    
  def script_get_player_position(self):
    position = self.player_position    
    return (position[0] + 0.5,position[1] + 0.5)

  def script_set_player_position(self, new_x, new_y):
    self.player_position = (new_x,new_y)

  ## Return a tuple (horizontal_rotation, vertical_rotation) in angles.

  def script_get_player_rotation(self):
    rotation = self.camera.getHpr()
    return (rotation[0],rotation[1])

  ## Sets the player rotation.

  def script_set_player_rotation(self, new_rotation_horizontal, new_rotation_vertical):
    self.camera.setHpr(new_rotation_horizontal,new_rotation_vertical,0.0)

  def script_get_level_size(self):
    return (self.level.get_width(),self.level.get_height())

  def script_get_daytime(self):
    return self.daytime
  
  def script_set_daytime(self, new_daytime):
    self.set_daytime(new_daytime)
    
  ## Gets position of given object, which can be prop, NPC etc.
  #  For player position see script_get_player_position.
  #  @return (x,y) float tuple
    
  def script_get_position(self, what):
    return what.position
    
  ## Gets the data of the object as a string.
    
  def script_get_data(self, what):
    return what.data
    
  def script_set_position(self, what, new_x, new_y):
    what.position = (new_x,new_y)
    # change the corresponding node path position:
    what.node_path.setPos(new_y - 0.5,new_x - 0.5,0)
    
  ## Gradually moves given game object to a new position. 
   
  def script_move(self, what, new_x, new_y, duration):
    what.position = (new_x,new_y)
    what.disable_usage = True        # disable usage for the time of the movement
    move_interval = LerpPosInterval(what.node_path,duration,(new_y - 0.5,new_x - 0.5,0))
    taskMgr.doMethodLater(duration,self.reenable_usage_task,"reenable_task", extraArgs=[what],appendTask=True)  # this will re-enable the usage
    move_interval.start()
    
  def script_get_tile_steppable(self, x, y):
    try:
      return self.collision_mask[x][y]
    except Exception:
      return False
    
  def script_set_tile_steppable(self, x, y, steppable):
    try:
      self.level.get_tile(x,y).steppable = steppable
      # get the new collision mask:
      self.collision_mask = self.level.get_collision_mask()
    except Exception:
      pass
    
app = Game()
app.run()