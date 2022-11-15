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

probabilities_2_burn = {0:0.75,1:0,2:0.3,3:0.95,4:1}
probabilities_2_burnt = {5:1/24,7:1/720,8:1,8:1}
wind_opp = {'N':6,'S':1,'E':3,'W':4}
wind_direction = 'S'

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
    #grid[0,0] = 5
    grid[0,199] = 5
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
    config.num_generations = 750
    config.wrap =False
    
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

#probability state will change
def p_change(probability):
    if probability == None:
        return False
    c = np.random.choice(np.array([True, False]), p=[probability,(1-probability)])
    return c

def p_change2(probability):
    if probability == None:
        return 0
    c = np.random.choice(np.array([1, 0]), p=[probability,(1-probability)])
    return c



# #function for changing states from not burning to burning
# state_change_burning = lambda x: x + 5 if p_change(probabilities_2_burn.get(x)) else x
# state_change_burning_vec = np.vectorize(state_change_burning)

# #function for changing states from burning to burnt
# state_change_burnt = lambda x: 10 if p_change(probabilities_2_burnt.get(x)) else x
# state_change_burnt_vec = np.vectorize(state_change_burnt)


# apply_probability_burn = np.vectorize(lambda x: 1 if p_change(probabilities_2_burn.get(x)) else 0)
# apply_probability_burnt = np.vectorize(lambda x: 1 if p_change(probabilities_2_burnt.get(x)) else 0)

apply_probability_burn = np.vectorize(lambda x: probabilities_2_burn.get(x) if p_change(probabilities_2_burn.get(x)) else 0)
apply_probability_burnt = np.vectorize(lambda x: 1 if p_change(probabilities_2_burnt.get(x)) else 0)
p_change2_vec = np.vectorize(lambda x: np.random.choice(np.array([1, 0]), p=[x,(1-x)]))

def transition_function(grid, neighbourstates, neighbourcounts):
    #Change unburnt 2 burning
    NW, N, NE, W, E, SW, S, SE = neighbourstates
    unburnt = (grid == 0) | (grid == 2) | (grid == 3) | (grid == 4) # cells currently in state 0-4 NOT lake
    vn_burning = (N > 4) | (W > 4) | (S > 4) | (E > 4) # adjacent states in states > 4 (Von Neumann)
    to_burning = unburnt & vn_burning # union the results

    p_grid = np.zeros((200,200))

    #change burning 2 burnt
    to_burnt = (grid == 5) | (grid == 7) | (grid == 8) | (grid == 9) # cells currently in state 5-9 NOT lake

    wind_affect = unburnt & (neighbourstates[wind_opp.get(wind_direction)] > 4) # cells were the wind blows in their direction

    p_grid[to_burning] = grid[to_burning]
    if p_grid[to_burning].size > 0:
        p_grid[to_burning] = apply_probability_burn(p_grid[to_burning])
        p_grid[to_burning] *= 0.5
        p_grid[wind_affect] /= 0.5
        p_grid[to_burning] = p_change2_vec(p_grid[to_burning])
        # print(p_grid[to_burning])
    grid[p_grid==1] += 5

    p_grid[:,:] = 0
    p_grid[to_burnt] = grid[to_burnt]
    if p_grid[to_burnt].size > 0:
        p_grid[to_burnt] = apply_probability_burnt(p_grid[to_burnt])
    grid[p_grid==1] = 10



    # if there are cells that can still burn
    # if grid[to_burning].size >0:
    #     grid[to_burning] = state_change_burning_vec(grid[to_burning])
    
    # # if there are cells that are still on fire
    # if grid[burning].size >0:
    #     grid[burning] = state_change_burnt_vec(grid[burning])

    return grid


def main():
    """ Main function that sets up, runs and saves CA"""
    # Get the config object from set up
    config = setup(sys.argv[1:])

    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, transition_function)

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()