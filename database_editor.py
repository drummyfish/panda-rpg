from Tkinter import *
from ttk import Frame, Button, Label, Style, Notebook
import tkFileDialog
import math
from general import *
from level import *

class Tab(Frame):
  def __init__(self, parent):
    Frame.__init__(self, parent)
    self.parent = parent
    self.button_widgets = {}
    self.text_widgets = {}

  def add_button(self,name,grid_x,grid_y,command=None):
    self.button_widgets[name] = Button(self,text=name,command=command)
    self.button_widgets[name].grid(row=grid_y,column=grid_x,sticky=N + S + W + E)

  def add_text_input(self,name,grid_x,grid_y):
    self.text_widgets[name] = Text(self, height=1, width=30)
    self.text_widgets[name].grid(row=grid_y,column=grid_x,sticky=N + S + W + E)

class ItemTab(Tab):
  def __init__(self, parent):
    Tab.__init__(self, parent)
    self.init_ui()  

  def init_ui(self):
    self.style = Style()
    self.style.theme_use("default")
   
    line = 0
    self.add_text_input("name",0,line)
    line += 1
    self.add_button("edit item",0,line)
    line += 1
    self.add_button("new item",0,line)
    line += 1
    self.add_button("delete item",0,line)
   
    self.listbox = Listbox(self)
    self.listbox.grid(row=0,column=1,rowspan=line + 1)
   
    self.pack(fill=BOTH, expand=1)

class NPCTab(Tab):
  def __init__(self, parent):
    Tab.__init__(self, parent)
    self.init_ui()  

  def init_ui(self):
    self.style = Style()
    self.style.theme_use("default")
   
    self.pack(fill=BOTH, expand=1)

class DatabaseEditor(Frame): 
  def __init__(self, parent):
    Frame.__init__(self, parent)
    self.parent = parent
    
def main():
  root = Tk()
  root.title("database editor")
  notebook = Notebook(root)
  tab1 = ItemTab(notebook)
  tab2 = NPCTab(notebook)
  notebook.add(tab1,text='items')
  notebook.add(tab2,text='NPCs')
  notebook.pack()
  
  root.mainloop()  

if __name__ == '__main__':
  main()  