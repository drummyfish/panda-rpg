from Tkinter import *
from ttk import Frame, Button, Label, Style, Notebook
import tkFileDialog
import math
from general import *
from game_database import *
from level import *

class Tab(Frame):
  def __init__(self, parent, database):
    Frame.__init__(self, parent)
    self.parent = parent
    self.database = database
    self.button_widgets = {}
    self.text_widgets = {}

  def add_button(self,name,grid_x,grid_y,command=None):
    self.button_widgets[name] = Button(self,text=name,command=command)
    self.button_widgets[name].grid(row=grid_y,column=grid_x,sticky=N + S + W + E)

  def add_text_input(self,name,grid_x,grid_y):
    self.text_widgets[name] = Text(self, height=1, width=30)
    self.text_widgets[name].grid(row=grid_y,column=grid_x,sticky=N + S + W + E)

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
    
    self.selected_id = None          # string id or None
    
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
    self.add_label("model name",0,line)
    line += 1
    self.add_text_input("model",0,line)
    line += 1
    self.add_label("texture name",0,line)
    line += 1
    self.add_text_input("texture",0,line)
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
    new_item_type = ItemType()
    
    new_id = self.get_text_value("id")
    new_item_type.name = self.get_text_value("name")
    
    if not new_id in self.database.get_item_types():
      self.database.get_item_types()[new_id] = new_item_type
    else:
      print("id already exists")
    
    self.update_listbox()

  def on_listbox_change(self,event):
    try:
      widget = event.widget
      selection = widget.curselection()
      self.selected_id = widget.get(selection[0])
      self.update_item_info()
    except Exception:
      # list clicked but no items => index exception
      return

  def on_edit_item_click(self):
    if self.selected_id != None:
      selected_item = self.database.get_item_types()[self.selected_id]
      
      new_id = self.get_text_value("id")
      
      selected_item.name = self.get_text_value("name")
      selected_item.model_name = self.get_text_value("model")
      selected_item.texture_name = self.get_text_value("texture")
      
      self.database.get_item_types().pop(self.selected_id,None)
      self.database.get_item_types()[new_id] = selected_item
      
      self.selected_id = new_id
      
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
      self.listbox.insert(i,item_id)
      i += 1
      
  def update_item_info(self):
    if self.selected_id != None:
      selected_item = self.database.get_item_types()[self.selected_id]
      
      self.set_text_value("id",self.selected_id)
      self.set_text_value("name",selected_item.name)
      self.set_text_value("model",selected_item.model_name)
      self.set_text_value("texture",selected_item.texture_name)
    else:
      self.set_text_value("id","")
      self.set_text_value("name","")
      self.set_text_value("model","")
      self.set_text_value("texture","")

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
    self.add_button("load database",0,0)
    self.add_button("save database",0,1)
    self.pack(fill=BOTH, expand=1)
    
def main():
  root = Tk()
  root.title("database editor")
  notebook = Notebook(root)
  
  database = GameDatabase()
  
  tab_main = MainTab(notebook,database)
  tab_items = ItemTab(notebook,database)
  tab_npcs = NPCTab(notebook,database)
  
  notebook.add(tab_main,text='Main')
  notebook.add(tab_items,text='Items')
  notebook.add(tab_npcs,text='NPCs')
  
  notebook.pack()
  
  root.mainloop()  

if __name__ == '__main__':
  main()  