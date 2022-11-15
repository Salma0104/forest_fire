# Name: NAME
# Dimensions: 2

# --- Set up executable path, do not edit ---
import sys
import inspect
import numpy as np
this_file_loc = (inspect.stack()[0][1])
main_dir_loc = this_file_loc[:this_file_loc.index('ca_descriptions')]
sys.path.append(main_dir_loc)
sys.path.append(main_dir_loc + 'capyle')
sys.path.append(main_dir_loc + 'capyle/ca')
sys.path.append(main_dir_loc + 'capyle/guicomponents')
# ---

from capyle.ca import Grid2D, Neighbourhood, randomise2d
import capyle.utils as utils

def create_map():
    #initially set everything to unburnt chaparral state(0,0)
    grid = np.zeros((200,200))
    #draw the lake
    grid[70:80,20:101] = 1
    # draw the dense forest
    grid[20:70,60:101] = 2
    grid[80:141,0:101] = 2
    #draw the canyon
    grid[20:160,120:131] = 3
    #draw the town
    grid[175:186,75:86] = 4
    #set top corners on fire
    grid[0:4,0:4] = 5
    grid[0:4,196:200] = 5
    return grid

def setup(args):
    """Set up the config object used to interact with the GUI"""
    config_path = args[0]
    config = utils.load(config_path)
    # -- THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED --
    config.title = "Forest Fire Simulation"
    config.dimensions = 2
    # 0-4 -> [chapparal, lake, forest, canyon, town], 5-9 ->[chapparal on fire, lake on fire, forest on fire, canyon on fire, town on fire]
    # 10 -> burnt out
    config.states = (0,1,2,3,4,5,6,7,8,9,10)
    config.state_colors = [(0.74,0.737,0.027),(0.024,0.68,0.933),(0.314,0.392,0.165),(0.984,0.988,0.024),(0,0,0),(1,0,0),(1,0,0),(1,0,0),(1,0,0),(1,0,0),(0.5,0.5,0.5)]
    config.initial_grid = create_map()
    
    # -------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----

    # config.state_colors = [(0,0,0),(1,1,1)]
    # config.grid_dims = (200,200)

    # ----------------------------------------------------------------------

    # the GUI calls this to pass the user defined config
    # into the main system with an extra argument
    # do not change
    if len(args) == 2:
        config.save()
        sys.exit()
    return config

def transition_function(grid, neighbourstates, neighbourcounts, decaygrid):
    """Function to apply the transition rules
    and return the new grid"""
    # YOUR CODE HERE
#     Transition rule: 0->1: total neighbours/total neighbours on fire*C(coefficient)*L(likeliness of the type of bush sets on fire)
# 1->2:  probability of material stop burning// after a set amount of time 
    

    neighbour_on_fire = (neighbourcounts[5] + neighbourcounts[6] + neighbourcounts[7] + neighbourcounts[8] + neighbourcounts[9]) >=3 # cells that have 3 neighbours in state 0
    
    
    chapparal_not_fire = (grid == 0) 
    # chapparal_decaygrid[chapparal_not_fire] -= 1
    chapparal_fire = chapparal_not_fire & neighbour_on_fire
    grid[chapparal_fire] = 5

    
    lake_not_fire = (grid == 1) 
    lake_fire = lake_not_fire & neighbour_on_fire
    grid[lake_fire] = 1 #lake can't be on fire
    

    forest_not_fire = (grid == 2) 
    forest_fire = forest_not_fire & neighbour_on_fire
    # forest_decaygrid[forest_not_fire] -= 1
    grid[forest_fire] = 6


    canyon_not_fire = (grid == 3) 
    canyon_fire = canyon_not_fire & neighbour_on_fire
    # canyon_decaygrid[canyon_not_fire] -= 7
    grid[canyon_fire] = 6


    town_not_fire = (grid == 4) 
    town_fire = town_not_fire & neighbour_on_fire
    grid[town_fire] = 6
    

    chapparal_on_fire = (grid == 5)
    decaygrid[chapparal_on_fire] -= 20

    forest_on_fire = (grid == 7)
    decaygrid[forest_on_fire] -= 3
    
    canyon_on_fire = (grid == 8)
    decaygrid[canyon_on_fire] -= 40
    

    decayed_to_zero = (decaygrid == 0)
    grid[decayed_to_zero] = 10
   
    return grid


def main():
    """ Main function that sets up, runs and saves CA"""
    # Get the config object from set up
    config = setup(sys.argv[1:])
    
    decaygrid = np.zeros(config.grid_dims)
    decaygrid.fill(100)
    # chapparal_decaygrid = np.zeros(config.grid_dims)
    # chapparal_decaygrid.fill(6)

    # forest_decaygrid = np.zeros(config.grid_dims)
    # forest_decaygrid.fill(2)

    # canyon_decaygrid = np.zeros(config.grid_dims)
    # canyon_decaygrid.fill(180)


    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, (transition_function, decaygrid))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()