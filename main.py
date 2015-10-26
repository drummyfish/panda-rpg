from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import *
from direct.showbase import DirectObject

from general import *

class MyApp(ShowBase, DirectObject.DirectObject):
  def __init__(self):
    ShowBase.__init__(self)

    self.setup_environment_scene(make_test_level())

    base.setFrameRateMeter(True)

    # initialise input handling:

    self.camera_time_before = 0
    self.camera_movement_speed = 9
    self.camera_rotation_speed = 1500

    base.disableMouse()

    self.taskMgr.add(self.camera_task, "camera_task")
    self.taskMgr.add(self.mouse_position_task, "mouse_position_task")

    self.input_state = {}   # contains state of mouse and keyboard

    self.input_state["mx"] = 0
    self.input_state["my"] = 0

    for key in ["w","s","a","d","q","e","mouse1","mouse3"]:
      self.input_state[key] = False
      self.accept(key,self.handle_input,[key,True])
      self.accept(key + "-up",self.handle_input,[key,False])

  def handle_input(self,input_name,input_value):
    self.input_state[input_name] = input_value

  def mouse_position_task(self, task):
    if base.mouseWatcherNode.hasMouse():
      x = base.mouseWatcherNode.getMouseX()
      y = base.mouseWatcherNode.getMouseY()

      self.input_state["mx"] = x
      self.input_state["my"] = y

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

  ## Sets up 3D environment node based on provided level layout.

  def setup_environment_scene(self, level):
    models = {}      # model cache
    textures = {}    # texture cache
    
    def load_model(model_name):                # loads model into 'models' cache (only if it hasn't been loaded laready)
      if not model_name in models:
        models[model_name] = self.loader.loadModel(model_name)
    
    def load_texture(texture_name):            # loads texture into 'textures' cache (only if it hasn't been loaded laready)
      if not texture_name in textures:
        textures[texture_name] = self.loader.loadTexture(texture_name)
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
    fog.setColor(0.3,0.3,0.3)
    fog.setExpDensity(0.1)
    fog.setLinearRange(10,20)
    
    level_node_path = NodePath("level")
    level_node_path.reparentTo(self.render)
    level_node_path.setFog(fog)
    
    skybox = self.loader.loadModel(RESOURCE_PATH + "skybox.obj")
    skybox.reparentTo(self.camera)
    skybox.setHpr(0,90,0)
    skybox.set_bin("background", 0);
    skybox.set_depth_write(False);
    skybox.set_compass()
    skybox.setTexture(self.loader.loadTexture(level.get_skybox_texture()))
    
    skybox_material = Material()
    skybox_material.setEmission((1, 1, 1, 1))
    skybox.setMaterial(skybox_material)
    
    for j in range(level.get_height()):
      for i in range(level.get_width()):

        if not level.get_tile(i,j).wall:                            # floor tile
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

    level_node_path.setTransparency(True)
    level_node_path.reparentTo(self.render)
    level_node_path.setPos(-4, 10, -0.5)
    level_node_path.setHpr(0, 90, 0)

    ambient_light = AmbientLight('alight')
    ambient_light_path = render.attachNewNode(ambient_light) 
    ambient_light.setColor(VBase4(0.5, 0.5, 0.5, 1))
    render.setLight(ambient_light_path)
    
    point_light = DirectionalLight('plight')
    point_light_path = render.attachNewNode(point_light)
    point_light_path.setHpr(10, -45, 0)
    point_light_path.setPos(-4, 10, 2)
    render.setLight(point_light_path)

app = MyApp()
app.run()
