from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import *
from direct.showbase import DirectObject

from level import *

class MyApp(ShowBase, DirectObject.DirectObject):
  DAYTIME_UPDATE_COUNTER = 2
  
  def __init__(self):
    ShowBase.__init__(self)

    self.daytime = 0.0                                              ##< time of day in range <0,1>
    self.update_daytime_counter = MyApp.DAYTIME_UPDATE_COUNTER      ##< counts frames to update daytime effects to increase FPS

    base.setFrameRateMeter(True)

    # initialise input handling:

    self.camera_time_before = 0
    self.camera_movement_speed = 9
    self.camera_rotation_speed = 1500

    base.disableMouse()

    self.taskMgr.add(self.camera_task,"camera_task")
    self.taskMgr.add(self.mouse_position_task,"mouse_position_task")
    self.taskMgr.add(self.time_task,"time_task")

    self.input_state = {}   # contains state of mouse and keyboard

    self.input_state["mx"] = 0
    self.input_state["my"] = 0

    for key in ["w","s","a","d","q","e","mouse1","mouse3"]:
      self.input_state[key] = False
      self.accept(key,self.handle_input,[key,True])
      self.accept(key + "-up",self.handle_input,[key,False])

    self.setup_environment_scene(Level.load_from_file(Level(1,1),"test_output.txt"))

  def handle_input(self,input_name,input_value):
    self.input_state[input_name] = input_value

  def mouse_position_task(self, task):
    if base.mouseWatcherNode.hasMouse():
      x = base.mouseWatcherNode.getMouseX()
      y = base.mouseWatcherNode.getMouseY()

      self.input_state["mx"] = x
      self.input_state["my"] = y

    return task.cont

  def time_task(self, task):
    self.daytime = (task.time / 3) % 1
    
    if self.update_daytime_counter > 0:
      self.update_daytime_counter -= 1
      return task.cont
    else:
      self.update_daytime_counter = MyApp.DAYTIME_UPDATE_COUNTER
    
    self.set_daytime(self.daytime)
    return task.cont
  
  def camera_task(self, task):
    current_position = self.camera.getPos()

    camera_forward = self.camera.getRelativeVector(self.render,VBase3(0,1,0))
    camera_right = self.camera.getRelativeVector(self.render,VBase3(1,0,0))

    new_position = [current_position.getX(),current_position.getY(),current_position.getZ()]

    time_difference = task.time - self.camera_time_before
    self.camera_time_before = task.time

    coefficient = self.camera_movement_speed * time_difference

    if self.input_state["w"]:
      new_position[0] -= camera_forward[0] * coefficient
      new_position[1] += camera_forward[1] * coefficient

    if self.input_state["s"]:
      new_position[0] += camera_forward[0] * coefficient
      new_position[1] -= camera_forward[1] * coefficient

    if self.input_state["a"]:
      new_position[0] -= camera_right[0] * coefficient
      new_position[1] += camera_right[1] * coefficient

    if self.input_state["d"]:
      new_position[0] += camera_right[0] * coefficient
      new_position[1] -= camera_right[1] * coefficient

    if self.input_state["e"]:
      new_position[2] += self.camera_movement_speed * time_difference

    if self.input_state["q"]:
      new_position[2] -= self.camera_movement_speed * time_difference

    if self.input_state["mouse1"]:
      current_rotation = self.camera.getHpr()
      new_rotation = [current_rotation.getX(),current_rotation.getY(),current_rotation.getZ()] 

      window_center = (base.win.getXSize() / 2, base.win.getYSize() / 2)
      base.win.movePointer(0, window_center[0], window_center[1])
      
      new_rotation[0] -= self.input_state["mx"] * self.camera_rotation_speed * time_difference
      new_rotation[1] += self.input_state["my"] * self.camera_rotation_speed * time_difference
      self.camera.setHpr(new_rotation[0],new_rotation[1],new_rotation[2])

    self.camera.setPos(new_position[0],new_position[1],new_position[2])

    return task.cont

  ## Sets the time of the day as a value in interval <0,1> to affect the scene (lighting, skybox texture, ...).

  def set_daytime(self, daytime):
    skybox_node = self.render.find("**/skybox")
    
    if skybox_node.isEmpty():
      return
    
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
    
    skybox_node.setTexture(self.skybox_texture_stage1,self.skybox_textures[texture_index])
    skybox_node.setTexture(self.skybox_texture_stage2,self.skybox_textures[(texture_index + 1) % len(self.skybox_textures)])
    self.skybox_texture_stage2.setColor(Vec4(ratio,ratio,ratio,ratio))
    
    # set diffuse light:
    
    diffuse_light_node = self.render.find("**/diffuse")
    ambient_light_node = self.render.find("**/ambient")
    
    if diffuse_light_node.isEmpty() or ambient_light_node.isEmpty():
      return
    
    light_index = int(len(self.diffuse_lights) * self.daytime)
    fraction = 1.0 / len(self.diffuse_lights)
    remainder = self.daytime - fraction * light_index
    ratio = remainder / fraction
    one_minus_ratio = 1.0 - ratio
    
    color1 = self.diffuse_lights[light_index]
    color2 = self.diffuse_lights[(light_index + 1) % len(self.diffuse_lights)]

    light_color = (color1[0] * one_minus_ratio + color2[0] * ratio,color1[1] * one_minus_ratio + color2[1] * ratio,color1[2] * one_minus_ratio + color2[2] * ratio)
    
    diffuse_light_node.node().setColor(VBase4(light_color[0],light_color[1],light_color[2],1))

    ambient_color = (light_color[0] * self.ambient_light_amount, light_color[1] * self.ambient_light_amount, light_color[2] * self.ambient_light_amount)
    ambient_light_node.node().setColor(VBase4(ambient_color[0],ambient_color[1],ambient_color[2],1))

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
        textures[texture_name].setMinfilter(Texture.FTNearestMipmapLinear)

    def make_node(animated_texture_model):     # makes a node out of AnimatedTextureModel object, handles loading models and textures and caches
      load_model(animated_texture_model.model_name)
      
      model = models[animated_texture_model.model_name]
      
      textures_for_node = []
      
      for texture_name in animated_texture_model.texture_names:
        load_texture(texture_name)
        textures_for_node.append(textures[texture_name])
      
      framerate = animated_texture_model.framerate
      
      if len(textures_for_node) == 1:
        node = PandaNode("node")
        node_path = NodePath(node)
        result = NodePath(node_path)
        model.instanceTo(node_path)
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

    base.camLens.setFov(105)       # setup the camera
    base.camLens.setNear(0.1)
    base.camLens.setFar(25)

    half_width = level.get_width() / 2.0
    half_height = level.get_height() / 2.0 
    
    fog = Fog("fog")
    fog_color = level.get_fog_color()
    fog.setColor(fog_color[0],fog_color[1],fog_color[2])
    fog.setExpDensity(0.1)
    fog.setLinearRange(level.get_fog_distance(),10)
    
    level_node_path = NodePath("level")
    level_node_path.reparentTo(self.render)
    level_node_path.setFog(fog)
    
    for j in range(level.get_height()):
      for i in range(level.get_width()):
        tile = level.get_tile(i,j)
        
        if not tile.is_empty():
          if not tile.wall:                            # floor tile
            tile_node_path = level_node_path.attachNewNode(make_node(level.get_tile(i,j).floor_model))
            tile_node_path.setPos(i - half_width,0,j - half_height)
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
              tile_node_path.setPos(i + offsets[k][0] - half_width,0,j + offsets[k][1] - half_height)
              tile_node_path.setHpr(0,0,rotations[k])

        if level.get_tile(i,j).ceiling:
          tile_node_path = level_node_path.attachNewNode(make_node(level.get_tile(i,j).ceiling_model))
          tile_node_path.setPos(i - half_width,level.get_tile(i,j).ceiling_height,j - half_height)

    for prop in level.get_props():
      tile_node_path = level_node_path.attachNewNode(make_node(prop.model))
      tile_node_path.setPos(prop.position[0] - half_width,0,prop.position[1] - half_height)
      tile_node_path.setHpr(prop.orientation,0,0)

    skybox = self.loader.loadModel(RESOURCE_PATH + "skybox.obj")
    skybox.setName("skybox")
    skybox.reparentTo(self.camera)
    skybox.setHpr(0,90,0)
    skybox.set_bin("background", 0);
    skybox.set_depth_write(False);
    skybox.set_compass()
    skybox_material = Material()
    skybox_material.setEmission((1, 1, 1, 1))
    skybox.setMaterial(skybox_material)
  
    self.skybox_texture_stage1 = TextureStage("ts0")
    self.skybox_texture_stage2 = TextureStage("ts2")
    self.skybox_texture_stage2.setCombineRgb(TextureStage.CMInterpolate,TextureStage.CSTexture,TextureStage.COSrcColor,TextureStage.CSPrevious,TextureStage.COSrcColor,TextureStage.CSConstant,TextureStage.COSrcColor)
    self.skybox_texture_stage2.setColor(Vec4(0.5,0.5,0.5,0.5))
    self.skybox_textures = []
    
    skybox_texture_names = level.get_skybox_textures()
    
    for skybox_texture_name in skybox_texture_names:
      load_texture(skybox_texture_name)
      self.skybox_textures.append(textures[skybox_texture_name])

    level_node_path.setTransparency(True)
    level_node_path.reparentTo(self.render)
    level_node_path.setPos(-4, 10, -0.5)
    level_node_path.setHpr(0, 90, 0)

    # manage lights:

    ambient_light = AmbientLight('ambient')
    ambient_light_path = render.attachNewNode(ambient_light) 
    ambient_light.setColor(VBase4(level.get_ambient_light_amount(),level.get_ambient_light_amount(),level.get_ambient_light_amount(),1))
    render.setLight(ambient_light_path)
    
    directional_light = DirectionalLight('diffuse')
    directional_light_path = render.attachNewNode(directional_light)
    directional_light.setColor(VBase4(0.7,0.7,0.7,1))
    directional_light_path.setHpr(10, -45, 0)
    directional_light_path.setPos(-4, 10, 1)
    render.setLight(directional_light_path)

    self.diffuse_lights = level.get_diffuse_lights()
    self.ambient_light_amount = level.get_ambient_light_amount()

    self.set_daytime(0.5)

app = MyApp()
app.run()
