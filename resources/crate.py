position = game.script_get_position(source)

x = int(position[0])
y = int(position[1])

game.script_set_tile_steppable(x,y,False)