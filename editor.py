from Tkinter import *
from ttk import Frame, Button, Label, Style
import math
from general import *

class Editor(Frame):
  TILE_SIZE = 20
  SMALL_TILE_SIZE = 14         # for displaying ceiling
  PADDING_X = 3
  PADDING_Y = 1
  
  def __init__(self, parent):
    Frame.__init__(self, parent)   
    self.parent = parent
    self.init_ui()
        
  def on_button_set_size_click(self):
    try:
      new_height = int(self.text_widgets["height"].get("1.0",END)) * Editor.TILE_SIZE
      new_width = int(self.text_widgets["width"].get("1.0",END)) * Editor.TILE_SIZE
    except Exception:
      print("error: wrong size")
     
  def on_canvas_click(self, event):
    self.selected_tile = self.pixel_to_tile_coordinates(event.x,event.y)
    self.redraw_level()
    self.update_gui_info()

  def on_canvas_click2(self, event):   # right click
    self.selected_tile = None
    self.redraw_level()
    self.update_gui_info()
    
  ## Sets text in given text widget (of given name).
    
  def set_text(self, name, text):
    self.text_widgets[name].delete("1.0",END)
    self.text_widgets[name].insert("1.0",text)
    
  def list_to_string(self, input_list):
    result = ""
    
    first = True
    
    for item in input_list:
      if first:
        first = False
      else:
        result += ";"
      
      result += item
    
    return result
    
  ## Updates the info in GUI, i.e. selected tile information etc.
    
  def update_gui_info(self):
    self.set_text("width",str(self.level.get_width()))
    self.set_text("height",str(self.level.get_height()))
    
    if self.selected_tile != None:
      tile = self.level.get_tile(self.selected_tile[0],self.selected_tile[1])
      self.set_text("wall model",tile.wall_model.model_name)
      self.set_text("wall textures",self.list_to_string(tile.wall_model.texture_names))
      self.set_text("floor model",tile.floor_model.model_name)
      self.set_text("floor textures",self.list_to_string(tile.floor_model.texture_names))
      self.set_text("ceiling model",tile.ceiling_model.model_name)
      self.set_text("ceiling textures",self.list_to_string(tile.ceiling_model.texture_names))
      self.set_text("ceiling height",str(tile.ceiling_height))
      self.set_text("orientation",str(tile.floor_orientation))
    else:
      self.set_text("wall model","")
      self.set_text("wall textures","")
      self.set_text("floor model","")
      self.set_text("floor textures","")
      self.set_text("ceiling model","")
      self.set_text("ceiling textures","")
      self.set_text("ceiling height","")
      self.set_text("orientation","")
      
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
        
        if self.selected_tile != None and self.selected_tile[0] == x and self.selected_tile[1] == y:
          self.canvas.create_rectangle(corner1[0], corner1[1], corner2[0], corner2[1], outline="red", fill=fill_color)   
        elif tile.wall:
          self.canvas.create_rectangle(corner1[0], corner1[1], corner2[0], corner2[1], outline="black", fill=fill_color)
        else:
          self.canvas.create_rectangle(corner1[0], corner1[1], corner2[0], corner2[1], outline=fill_color, fill=fill_color)

        if tile.ceiling:
          self.canvas.create_rectangle(corner1[0] + small_tile_offset, corner1[1] + small_tile_offset, corner2[0] - + small_tile_offset, corner2[1] - + small_tile_offset, outline=ceiling_color, fill=ceiling_color)

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
    
  def add_name_check_input(self, name):
    self.label_widgets[name] = Label(self, text=name)
    self.add_widget(self.label_widgets[name],self.current_row,0)
    
    self.checkbox_widgets[name] = Checkbutton(self)
    self.add_widget(self.checkbox_widgets[name],self.current_row,1)
    
    self.current_row += 1
     
  def add_button(self, name):
    self.button_widgets[name] = Button(self, text=name)
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
    
    self.add_button("save file")
    self.add_button("load file")
    self.add_name_value_input("width")
    self.add_name_value_input("height")
    self.add_button("set size")
    self.add_name_check_input("draw mode")
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
    self.add_button("set tile")
    self.add_name_check_input("display texture")
    self.add_name_check_input("display model")
    self.add_name_check_input("display ceiling")
    self.add_name_check_input("display ceiling height")
    self.add_name_check_input("display orientation")
    
    self.canvas = Canvas(self, width=200, height=100, background="white", borderwidth=2, relief=SUNKEN)
    self.add_widget(self.canvas,0,2,1,self.current_row + 1)
    
    self.canvas.bind("<Button-1>", self.on_canvas_click)
    self.canvas.bind("<Button-3>", self.on_canvas_click2)
    
    self.selected_tile = (0,0)
    
    self.level = make_test_level()
    self.redraw_level()
    
def main():
  root = Tk()
  root.geometry("1280x768")
  app = Editor(root)
  root.mainloop()  

if __name__ == '__main__':
  main()  