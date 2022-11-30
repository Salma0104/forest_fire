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

#Dict that sores the probability that each state will burn
chappral_prob = 0.71
relative_canyon = 1.35 * chappral_prob
relative_forrest = 0.16 * chappral_prob


probabilities_2_burn = {3:chappral_prob,4:0,5:relative_forrest,6:relative_canyon,7:1}


# NW=0, N=1, NE=2, W=3, E=4, SW=5, S=6, SE=7
# N=[SW,S,SE], NE=[W,SW,S], E=[NW,W,SW], SE = [N,NW,W], S=[NW,N,NE], SW=[N,NE,E], W=[NE,E,SE], NW=[E,SE,S]
#Dict that stores the corresponding neighbour cell that need to be burning for current cell to be affected by the wind
wind_opp = {'N':[5,6,7], 'NE':[3,5,6], 'E':[0,3,5], 'SE':[1,0,3], 'S':[0,1,2], 'SW':[1,2,4], 'W':[2,4,7], 'NW':[4,7,6]}

damp_plant_duration = np.zeros((200,200)) - 1

wind_direction = 'S'

def diagonal_water(start,grid):
    for i in range(35):
        grid[start[0],start[1]] = 1
        start[0] += 1
        start[1] += 1
    return grid

def diagonal_forest(start,grid,direction,length):
    for i in range(length):
        grid[start[0],start[1]:start[2]] = 5
        start[0] += direction
        start[1] += 1
        start[2] += 1
    return grid

def create_map():
    #initially set everything to unburnt chaparral state(0,0)

    #--- default all chappral
    grid = np.zeros((200,200)) + 3
    #grid[99,99] = 8
    #------ 
    
    #draw the lake
    grid[70:80,20:101] = 4
    # draw the dense forest
    grid[20:70,60:101] = 5
    grid[80:141,0:101] = 5
    #draw the canyon
    grid[20:160,120:131] = 6
    #draw the town
    grid[175:186,75:86] = 7
    #set top corners on fire
    #grid[0,0] = 8
    grid[0,199] = 8
    #draw the damp cells
    # grid[140,101:152] = 1
    # grid = diagonal_water([0,165],grid)
    # grid = diagonal_water([135,101],grid)
    # grid[0:150,50:100] = 1

    grid = diagonal_forest([141,75,101],grid,1,59)

    return grid

def setup(args):
    """Set up the config object used to interact with the GUI"""
    config_path = args[0]
    config = utils.load(config_path)
    # -- THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED --
    config.title = f"Forest Fire Simulation, Direction:{wind_direction}"
    config.dimensions = 2
    # 0 -> burnt out
    # 1-2 -> [damp chappral, damp forrest]
    # 3-7 -> [chapparal, lake, forest, canyon, town], 8-12 ->[chapparal on fire, lake on fire, forest on fire, canyon on fire, town on fire]
    config.states = (0,1,2,3,4,5,6,7,8,9,10,11,12)
    config.state_colors = [(0.5,0.5,0.5),(0,0.05,0.8),(0,0.2,0.9),(0.74,0.737,0.027),(0.024,0.68,0.933),(0.314,0.392,0.165),(0.984,0.988,0.024),(0,0,0),(1,0,0),(1,0,0),(1,0,0),(1,0,0),(1,0,0)]
    config.initial_grid = create_map()
    config.durations = (np.zeros((200,200)) - np.ones((200,200)))
    ##
    if not config.num_generations:
        config.num_generations = 700
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
''''Outputs True or False where True is outputted with a probability of "probability"  '''
def p_change(probability):
    if probability == None:
        return False
    c = np.random.choice(np.array([True, False]), p=[probability,(1-probability)])
    return c

# All functions below are vecorized so they can be applied to np.array

# A function that outputs the probability of x if p_change(x) is True else 0
apply_probability_burn = np.vectorize(lambda x: probabilities_2_burn.get(x) if p_change(probabilities_2_burn.get(x)) else 0)

# similar to p_change but 1/0 instead of True/False
''''Outputs 1 or 0 where 1 is outputted with a probability of "probability"  '''
p_change2_vec = np.vectorize(lambda x: np.random.choice(np.array([1, 0]), p=[x,(1-x)]))

def catch_fire(grid,burn_mask,adjacent_wind_mask,diagonal_wind_mask):
    p_grid = np.zeros((200,200))
    p_grid[burn_mask] = grid[burn_mask]
    if p_grid[burn_mask].size > 0:
        #changes each state in subarray to its p value where p = probability to burn e.g [1,4] = [0,0.8]
        p_grid[burn_mask] = apply_probability_burn(p_grid[burn_mask])
        p_grid[burn_mask] *= 0.4 #penalty for wind blowing the wrong way

        p_grid[adjacent_wind_mask]  =  (p_grid[adjacent_wind_mask] /0.4) * 10 #make the wind blowing the right way stronger
        p_grid[diagonal_wind_mask]  =  (p_grid[diagonal_wind_mask] /0.4) * 0.9

        #using the probability stored it outputs either 1 or 0 e.g. [0,0.8] might equal [0,1]
        p_grid[p_grid > 1] = 1
        p_grid[burn_mask] = p_change2_vec(p_grid[burn_mask])
    return p_grid


def transition_function(grid, neighbourstates, neighbourcounts, durations):
    # each variable stores the 200x200 array corresponding to the direction to center cell
    NW, N, NE, W, E, SW, S, SE = neighbourstates
    # cells currently in state 0-4 NOT lake
    unburnt = (grid == 3) | (grid==5) | (grid==6) | (grid==7)
    # all states in states > 4 (Moore)
    burning = (N > 7) | (W > 7) | (S > 7) | (E > 7)| (NE > 7) | (SE > 7) | (NW > 7) | (SW > 7) 
    burning_von_neuman = (N > 7) | (W > 7) | (S > 7) | (E > 7)
    # union the results

    has_no_damp_neighbour = (neighbourcounts[1] == 0) & (neighbourcounts[2] == 0)
    has_damp_neighbour = (neighbourcounts[1] > 0) | (neighbourcounts[2] > 0)

    to_burning = unburnt & burning & has_no_damp_neighbour
    to_burning_von_neuman = unburnt & burning_von_neuman & has_damp_neighbour

    # Adjacent cell == the neighbour in the opposide direction to wind, right_diag is the cell to the right of the adjacent cell, left_diag is cell to left of adjacent cell
    right_diag, adjacent, left_diag = wind_opp.get(wind_direction)

    #boolean mask thats true for all cells where the adjacent neighbour is not burning.
    center_not_burning = (neighbourstates[adjacent] <= 7) & (neighbourstates[adjacent] > 0)
    # boolean mask where only diagonal neighbours are burning
    diagonal_burning = ((neighbourstates[right_diag] > 7) | (neighbourstates[left_diag] > 7)) & center_not_burning 
    # boolean mask where adjacent neighbour is burning but diagonals can also burn
    adjacent_burning = (neighbourstates[adjacent] > 7)


    # boolean mask where any from diagonals and adjacent are burning

    #p_grid will only store states for specified subarray
    p_grid = catch_fire(grid,to_burning,adjacent_burning,diagonal_burning)
    
    #for every element in grid thats equal to 1 in p_grid, change its state to burning (add 5)
    grid[p_grid==1] += 5

    p_grid = catch_fire(grid,to_burning_von_neuman,adjacent_burning,diagonal_burning)
    
    #for every element in grid thats equal to 1 in p_grid, change its state to burning (add 5)
    grid[p_grid==1] += 5


    #set all the newly burning cells to their respective durations:

    newlyBurntChappral = (durations == -1) & (grid == 8) #because -1 means duration not set, so we are yet to set these burning ones (s5)
    newlyBurntForest = (durations == -1) & (grid == 10)
    newlyBurntCanyon = (durations == -1) & (grid == 11)
    newlyBurntTown = (durations == -1) & (grid == 12)
    
    #setting durations
    #one iteration is 15 mins
    durations[newlyBurntChappral] = np.random.randint((60/15 * 6), (60/15 * 24 * 2))
    durations[newlyBurntForest] = np.random.randint((60/15 * 24 * 7), (60/15 * 24 * 30)) #7 days to 30 days
    durations[newlyBurntTown] = 2
    durations[newlyBurntCanyon] = 10
    #decrement all durations by 1:

    durations[durations > 0] -= 1

    #make a burnt out cell if duration is 0

    burntOut = (durations == 0)
    grid[burntOut] = 0 #0 is burnt state

    damp_plants = (grid == 1) | (grid == 2)
    new_burn_neigh_damp_plant = burning & damp_plants & (damp_plant_duration == - 1)
    damp_plant_duration[new_burn_neigh_damp_plant] = 50
    damp_plant_duration[damp_plant_duration > 0] -= 1
    grid[damp_plant_duration == 0] += 2
    damp_plant_duration[damp_plant_duration == 0] = -1
    




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