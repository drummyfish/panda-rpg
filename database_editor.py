from Tkinter import *
from ttk import Frame, Button, Label, Style, Notebook
import tkFileDialog
import math
from general import *
from game_database import *
from level import *
from general_gui import *

class Tab(Frame):
  def __init__(self, parent, database):
    Frame.__init__(self, parent)
    self.parent = parent
    self.database = database
    self.button_widgets = {}
    self.text_widgets = {}
    self.model_widgets = {}

  def add_button(self,name,grid_x,grid_y,command=None):
    self.button_widgets[name] = Button(self,text=name,command=command)
    self.button_widgets[name].grid(row=grid_y,column=grid_x,sticky=N + S + W + E)

  def add_text_input(self,name,grid_x,grid_y):
    self.text_widgets[name] = Text(self, height=1, width=30)
    self.text_widgets[name].grid(row=grid_y,column=grid_x,sticky=N + S + W + E)

  def add_model_input(self,name,grid_x,grid_y):
    self.model_widgets[name] = AnimatedTextureModelInput(self)
    self.model_widgets[name].grid(row=grid_y,column=grid_x,sticky=N + S + W + E)

  def add_label(self,name,grid_x,grid_y):
    label = Label(self, text=name)
    label.grid(row=grid_y,column=grid_x,sticky=N + S + W + E)

  def get_text_value(self,name):
    return self.text_widgets[name].get("1.0",END).replace("\n","")

  def set_text_value(self,name,text):
    self.text_widgets[name].delete("1.0",END)
    self.text_widgets[name].insert("1.0",text)

class ItemTab(Tab):
  def __init__(self, parent, database):
    Tab.__init__(self, parent, database)
    
    self.selected_id = None          # non negative integer id or None
    self.init_ui()
    self.update_listbox()
    self.update_item_info()

  def init_ui(self):
    self.style = Style()
    self.style.theme_use("default")
   
    line = 0
    self.add_label("id",0,line)
    line += 1
    self.add_text_input("id",0,line)
    line += 1
    self.add_label("name",0,line)
    line += 1
    self.add_text_input("name",0,line)
    line += 1
    self.add_label("model",0,line)
    line += 1
    self.add_model_input("item model",0,line)
    line += 1
    self.add_button("edit item",0,line,self.on_edit_item_click)
    line += 1
    self.add_button("new item",0,line,self.on_new_item_type_click)
    line += 1
    self.add_button("delete item",0,line,self.on_delete_item_click)
   
    self.listbox = Listbox(self)
    self.listbox.grid(row=0,column=1,rowspan=line + 1)
    self.listbox.bind('<<ListboxSelect>>',self.on_listbox_change)
   
    self.pack(fill=BOTH, expand=1)

  def on_new_item_type_click(self):
    self.selected_id = self.database.new_item_type()
    self.update_listbox()

  def on_listbox_change(self,event):
    try:
      widget = event.widget
      selection = widget.curselection()
  
      selected_item_text = widget.get(selection[0])
      helper = selected_item_text.split(" ")

      self.selected_id = int(helper[0])
      
      self.update_item_info()
    except Exception:
      # list clicked but no items => index exception
      return

  def on_edit_item_click(self):
    if self.selected_id != None:
      selected_item = self.database.get_item_types()[self.selected_id]
      
      selected_item.name = self.get_text_value("name")
      self.model_widgets["item model"].fill_model(selected_item.model)
      
      self.database.get_item_types().pop(self.selected_id,None)
      self.database.get_item_types()[self.selected_id] = selected_item
      
      self.update_item_info()
      self.update_listbox()
    
  def on_delete_item_click(self):
    if self.selected_id != None:
      self.database.get_item_types().pop(self.selected_id,None)
      self.selected_id = None
    
    self.update_listbox()
    self.update_item_info()
    
  def update_listbox(self):
    items = self.database.get_item_types()
    
    self.listbox.delete(0,END)
    
    i = 0
    
    for item_id in items:
      self.listbox.insert(i,str(item_id) + " " + self.database.item_types[item_id].name)
      i += 1
      
  def update_item_info(self):
    if self.selected_id != None:
      selected_item = self.database.get_item_types()[self.selected_id]
      
      self.set_text_value("id",self.selected_id)
      self.set_text_value("name",selected_item.name)
      self.model_widgets["item model"].set_model(selected_item.model)
    else:
      self.set_text_value("id","")
      self.set_text_value("name","")
      self.model_widgets["item model"].clear()

class NPCTab(Tab):
  def __init__(self, parent, database):
    Tab.__init__(self, parent, database)
    self.init_ui()  
    self.update_gui()

  def init_ui(self):
    self.style = Style()
    self.style.theme_use("default")
   
    self.pack(fill=BOTH, expand=1)

  def update_gui(self):
    return

class MainTab(Tab):
  def __init__(self, parent, database):
    Tab.__init__(self, parent, database)
    self.init_ui()  

  def init_ui(self):
    self.add_button("load database",0,0,self.on_load_click)
    self.add_button("save database",0,1,self.on_save_click)
    self.pack(fill=BOTH, expand=1)
    
  def on_save_click(self):
    filename = tkFileDialog.asksaveasfilename()
    
    if len(filename) == 0:
      return
    
    GameDatabase.save_to_file(self.database,filename)    
  
  def on_load_click(self):
    filename = tkFileDialog.askopenfilename()
    
    if len(filename) == 0:
      return
    
    self.database = GameDatabase.load_from_file(filename)
    
    self.parent.tab_items.database = self.database
    self.parent.tab_items.update_listbox()
    
def main():
  root = Tk()
  root.title("database editor")
  notebook = Notebook(root)
  
  database = GameDatabase()
  
  notebook.tab_main = MainTab(notebook,database)
  notebook.tab_items = ItemTab(notebook,database)
  notebook.tab_npcs = NPCTab(notebook,database)
  
  notebook.add(notebook.tab_main,text='Main')
  notebook.add(notebook.tab_items,text='Items')
  notebook.add(notebook.tab_npcs,text='NPCs')
  
  notebook.pack()
  
  root.mainloop()  

if __name__ == '__main__':
  main()  