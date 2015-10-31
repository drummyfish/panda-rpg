from Tkinter import *
from ttk import Frame, Button, Label, Style
import tkFileDialog
import math
from level import *

class Editor(Frame):
  TILE_SIZE = 20
  SMALL_TILE_SIZE = 14         # for displaying ceiling
  PADDING_X = 3
  PADDING_Y = 1
  
  def __init__(self, parent):
    Frame.__init__(self, parent)   
    self.parent = parent
    self.init_ui()
        
  def on_save_file_clicked(self):
    filename = tkFileDialog.asksaveasfilename()
    
    if len(filename) == 0:
      return
    
    Level.save_to_file(self.level,filename)
   
  def on_load_file_clicked(self):
    filename = tkFileDialog.askopenfilename()
    
    if len(filename) == 0:
      return
    
    self.level = Level.load_from_file(self.level,"test_output.txt")
    self.selected_tile = None
    self.redraw_level()
   
  def on_set_map_info_click(self):
    self.level.set_name(self.get_text("name"))
    self.level.set_skybox_textures(self.string_to_list(self.get_text("skybox textures")))
    
    diffuse_lights = self.get_text("daytime colors").replace(" ", "").split(";")
   
    for i in range(len(diffuse_lights)):
      values = diffuse_lights[i][1:-1].split(",")
      diffuse_lights[i] = (float(values[0]),float(values[1]),float(values[2]))
      
    self.level.set_light_properties(float(self.get_text("ambient light amount")),diffuse_lights)
    
  def on_canvas_click(self, event):
    self.selected_tile = self.pixel_to_tile_coordinates(event.x,event.y)
    self.redraw_level()
    self.update_gui_info()

  def on_canvas_click2(self, event):   # right click 
    try:
      clicked_tile = self.pixel_to_tile_coordinates(event.x,event.y)
      tile = self.level.get_tile(clicked_tile[0],clicked_tile[1])
      tile.wall = self.get_check("is wall")
      tile.ceiling = self.get_check("has ceiling")
      tile.wall_model.model_name = self.get_text("wall model")
      tile.wall_model.texture_names = self.string_to_list(self.get_text("wall textures"))
      tile.floor_model.texture_names = self.string_to_list(self.get_text("floor textures"))
      tile.ceiling_model.texture_names = self.string_to_list(self.get_text("ceiling textures"))
      tile.floor_model.model_name = self.get_text("floor model")
      tile.ceiling_model.model_name = self.get_text("ceiling model")
      tile.floor_orientation = int(self.get_text("orientation"))
      self.redraw_level()
    except Exception:
      print("error: wrong value")
    
  def color_to_string(self, color):
    return "(" + str(color[0]) + "," + str(color[1]) + "," + str(color[2]) + ")"
    
  ## Sets text in given text widget (of given name).
    
  def set_text(self, name, text):
    self.text_widgets[name].delete("1.0",END)
    self.text_widgets[name].insert("1.0",text)
    
  def get_text(self, name):
    return self.text_widgets[name].get("1.0",END).replace("\n","")
    
  ## Sets checkbox value of checkbox of given name.
    
  def set_check(self, name, bool_value):
    self.checkbox_widgets[name].value.set(bool_value == True)
    
  ## Gets a bool value of a checkbox of given name.
    
  def get_check(self, name):
    return self.checkbox_widgets[name].value.get() == True
    
  def list_to_string(self, input_list):
    result = ""
    
    first = True
    
    for item in input_list:
      if first:
        first = False
      else:
        result += ";"
      
      result += str(item)
    
    return result
    
  def string_to_list(self, input_string):
    return input_string.split(";")
    
  ## Updates the info in GUI, i.e. selected tile information etc.
    
  def update_gui_info(self):
    self.set_text("width",str(self.level.get_width()))
    self.set_text("height",str(self.level.get_height()))
    
    if self.selected_tile != None:
      tile = self.level.get_tile(self.selected_tile[0],self.selected_tile[1])
      self.set_text("name",self.level.get_name())
      self.set_text("ambient light amount",str(self.level.get_ambient_light_amount()))
      self.set_text("daytime colors",self.list_to_string(self.level.get_diffuse_lights()).replace(" ",""))
      self.set_text("fog color",self.color_to_string(self.level.get_fog_color()))
      self.set_text("wall model",tile.wall_model.model_name)
      self.set_text("wall textures",self.list_to_string(tile.wall_model.texture_names))
      self.set_text("floor model",tile.floor_model.model_name)
      self.set_text("floor textures",self.list_to_string(tile.floor_model.texture_names))
      self.set_text("ceiling model",tile.ceiling_model.model_name)
      self.set_text("ceiling textures",self.list_to_string(tile.ceiling_model.texture_names))
      self.set_text("ceiling height",str(tile.ceiling_height))
      self.set_text("orientation",str(tile.floor_orientation))
      self.set_check("is wall",tile.wall)
      self.set_check("has ceiling",tile.ceiling)
    else:
      self.set_text("name","")
      self.set_text("ambient light amount","")
      self.set_text("daytime colors","")
      self.set_text("fog color","")
      self.set_text("wall model","")
      self.set_text("wall textures","")
      self.set_text("floor model","")
      self.set_text("floor textures","")
      self.set_text("ceiling model","")
      self.set_text("ceiling textures","")
      self.set_text("ceiling height","")
      self.set_text("orientation","")
      self.set_check("is wall",False)
      self.set_check("has ceiling",False)
      
  def pixel_to_tile_coordinates(self, x, y):
    return (int(math.floor(x / Editor.TILE_SIZE)),int(math.floor(y / Editor.TILE_SIZE)))
   
  ## Computes color for AnimatedTextureModel object as its hash based on attributes checked
  #  in GUI (display texture, display model etc.). Returns tkinter color string.
   
  def compute_model_color(self, model):
    textures = ""
  
    for texture_name in model.texture_names:
      textures += texture_name
  
    red = hash(model.model_name) % 256
    green = hash(textures) % 256
    blue = hash(model.model_name + textures) % 256
    
    return ("#%0.2x" % red) + ("%0.2x" % green) + ("%0.2x" % blue)
   
  def redraw_level(self):
    self.canvas.config(width=self.level.get_width() * Editor.TILE_SIZE, height=self.level.get_height() * Editor.TILE_SIZE)
    self.canvas.delete("all")
    
    small_tile_offset = math.floor((Editor.TILE_SIZE - Editor.SMALL_TILE_SIZE) / 2)
    
    half_tile_size = Editor.TILE_SIZE / 2
    
    for y in range(self.level.get_height()):
      for x in range(self.level.get_width()):
        corner1 = (x * Editor.TILE_SIZE, y * Editor.TILE_SIZE)
        corner2 = (corner1[0] + Editor.TILE_SIZE - 1, corner1[1] + Editor.TILE_SIZE - 1)
        
        tile = self.level.get_tile(x,y)
        
        if tile.wall:
          fill_color = self.compute_model_color(self.level.get_tile(x,y).wall_model)
        else:
          fill_color = self.compute_model_color(self.level.get_tile(x,y).floor_model)
        
        ceiling_color = self.compute_model_color(self.level.get_tile(x,y).ceiling_model)
           
        if tile.wall:       # wall
          self.canvas.create_rectangle(corner1[0], corner1[1], corner2[0], corner2[1], outline="black", fill=fill_color)
        else:               # floor
          self.canvas.create_rectangle(corner1[0], corner1[1], corner2[0], corner2[1], outline=fill_color, fill=fill_color)

          if self.get_check("display orientation"):
            if tile.floor_orientation == 0:
              p1 = (corner1[0] + 1,corner2[1] - 1)
              p2 = (corner2[0] + 1,corner2[1] - 1)
            elif tile.floor_orientation == 1:
              p1 = (corner1[0] + 1,corner1[1] - 1)
              p2 = (corner1[0] + 1,corner2[1] - 1)
            elif tile.floor_orientation == 2:
              p1 = (corner1[0] + 1,corner1[1] - 1)
              p2 = (corner2[0] + 1,corner1[1] - 1)
            else:
              p1 = (corner2[0] + 1,corner1[1] - 1)
              p2 = (corner2[0] + 1,corner2[1] - 1)
              
            p3 = (corner1[0] + half_tile_size,corner1[1] + half_tile_size)
            
            self.canvas.create_polygon(p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],outline="white",fill="green")

        if tile.ceiling and self.get_check("display ceiling"):
          self.canvas.create_rectangle(corner1[0] + small_tile_offset, corner1[1] + small_tile_offset, corner2[0] - + small_tile_offset, corner2[1] - + small_tile_offset, outline=ceiling_color, fill=ceiling_color)

        if self.selected_tile != None and self.selected_tile[0] == x and self.selected_tile[1] == y:
          self.canvas.create_rectangle(corner1[0], corner1[1], corner2[0], corner2[1], outline="red")

  ## Adds given widget to given place in grid layout.

  def add_widget(self, widget, grid_x, grid_y, column_span=1, row_span=1, spread_x=False):
    
    stick = W + N
    
    if spread_x:
      stick = stick + E
    
    widget.grid(row=grid_x, column=grid_y, rowspan=row_span, columnspan=column_span, padx=Editor.PADDING_X, pady=Editor.PADDING_Y, sticky=stick)
     
  def add_name_value_input(self, name):
    self.label_widgets[name] = Label(self, text=name)
    self.add_widget(self.label_widgets[name],self.current_row,0)
    
    self.text_widgets[name] = Text(self, height=1, width=30)
    self.add_widget(self.text_widgets[name],self.current_row,1)
    
    self.current_row += 1
    
  def add_name_check_input(self, name, checked=False, command=None):
    self.label_widgets[name] = Label(self, text=name)
    self.add_widget(self.label_widgets[name],self.current_row,0)
    
    value = IntVar()
    
    self.checkbox_widgets[name] = Checkbutton(self,variable=value,command=command)
    self.checkbox_widgets[name].value = value
    self.add_widget(self.checkbox_widgets[name],self.current_row,1)
    
    self.set_check(name,checked)
    
    self.current_row += 1
     
  def add_button(self, name, command=None):
    self.button_widgets[name] = Button(self,text=name,command=command)
    self.add_widget(self.button_widgets[name],self.current_row,0,2,1,True)
    
    self.current_row += 1
    
  def init_ui(self):
    self.parent.title("editor")
    self.style = Style()
    self.style.theme_use("default")
    self.pack(fill=BOTH, expand=1)
        
    self.label_widgets = {}
    self.text_widgets = {}
    self.checkbox_widgets = {}
    self.button_widgets = {}
    
    self.current_row = 0
    
    self.add_button("save file",self.on_save_file_clicked)
    self.add_button("load file",self.on_load_file_clicked)
    self.add_name_value_input("name")
    self.add_name_value_input("skybox textures")
    self.add_name_value_input("daytime colors")
    self.add_name_value_input("ambient light amount")
    self.add_name_value_input("fog color")
    self.add_name_value_input("width")
    self.add_name_value_input("height")
    self.add_button("set map info",self.on_set_map_info_click)
    self.add_name_value_input("wall model")
    self.add_name_value_input("wall textures")
    self.add_name_value_input("floor model")
    self.add_name_value_input("floor textures")
    self.add_name_value_input("ceiling model")
    self.add_name_value_input("ceiling textures")
    self.add_name_value_input("ceiling height")
    self.add_name_value_input("orientation")
    self.add_name_check_input("is wall")
    self.add_name_check_input("has ceiling")
    self.add_name_check_input("display texture",True,self.redraw_level)
    self.add_name_check_input("display model",True,self.redraw_level)
    self.add_name_check_input("display ceiling",True,self.redraw_level)
    self.add_name_check_input("display ceiling height",True,self.redraw_level)
    self.add_name_check_input("display orientation",True,self.redraw_level)
    
    self.canvas = Canvas(self, width=200, height=100, background="white", borderwidth=2, relief=SUNKEN)
    self.add_widget(self.canvas,0,2,1,self.current_row + 1)
    
    self.canvas.bind("<Button-1>", self.on_canvas_click)
    self.canvas.bind("<Button-3>", self.on_canvas_click2)
    
    self.selected_tile = (0,0)
    
    self.level = Level(30,35) #make_test_level()
    self.redraw_level()
    
def main():
  root = Tk()
  root.geometry("1280x768")
  app = Editor(root)
  root.mainloop()  

if __name__ == '__main__':
  main()  