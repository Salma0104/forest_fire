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
probabilities_2_burn = {0:0.6,1:0,2:0.2,3:0.8,4:0.8}

#Dict that sores the probability that each state will stop burning (become burnt)
probabilities_2_burnt = {5:1/24,7:1/720,8:1,8:1}


# NW=0, N=1, NE=2, W=3, E=4, SW=5, S=6, SE=7
# N=[SW,S,SE], NE=[W,SW,S], E=[NW,W,SW], SE = [N,NW,W], S=[NW,N,NE], SW=[N,NE,E], W=[NE,E,SE], NW=[E,SE,S]
#Dict that stores the corresponding neighbour cell that need to be burning for current cell to be affected by the wind
wind_opp = {'N':[5,6,7], 'NE':[3,5,6], 'E':[0,3,5], 'SE':[1,0,3], 'S':[0,1,2], 'SW':[1,2,4], 'W':[2,4,7], 'NW':[4,7,6]}

wind_direction = 'W'

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
    config.title = f"Forest Fire Simulation, Direction:{wind_direction}"
    config.dimensions = 2
    # 0-4 -> [chapparal, lake, forest, canyon, town], 5-9 ->[chapparal on fire, lake on fire, forest on fire, canyon on fire, town on fire]
    # 10 -> burnt out
    config.states = (0,1,2,3,4,5,6,7,8,9,10)
    config.state_colors = [(0.74,0.737,0.027),(0.024,0.68,0.933),(0.314,0.392,0.165),(0.984,0.988,0.024),(0,0,0),(1,0,0),(1,0,0),(1,0,0),(1,0,0),(1,0,0),(0.5,0.5,0.5)]
    config.initial_grid = create_map()
    ##
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
# A function that outputs 1 if p_change(x) is True else 0
apply_probability_burnt = np.vectorize(lambda x: 1 if p_change(probabilities_2_burnt.get(x)) else 0)

# similar to p_change but 1/0 instead of True/False
''''Outputs 1 or 0 where 1 is outputted with a probability of "probability"  '''
p_change2_vec = np.vectorize(lambda x: np.random.choice(np.array([1, 0]), p=[x,(1-x)]))

def transition_function(grid, neighbourstates, neighbourcounts, durations):
    # each variable stores the 200x200 array corresponding to the direction to center cell
    NW, N, NE, W, E, SW, S, SE = neighbourstates
    # cells currently in state 0-4 NOT lake
    unburnt = (grid == 0) | (grid == 2) | (grid == 3) | (grid == 4) 
    # adjacent states in states > 4 (Moore)
    burning = (N > 4) | (W > 4) | (S > 4) | (E > 4)|(NE > 4) | (SE > 4) | (NW > 4) | (SW > 4) 
    # union the results
    to_burning = unburnt & burning 

    p_grid = np.zeros((200,200))

    # cells currently in state 5-9 NOT lake
    to_burnt = (grid == 5) | (grid == 7) | (grid == 8) | (grid == 9) 

    #wind_affect = unburnt & (neighbourstates[wind_opp.get(wind_direction)] > 4) # cells were the wind blows in their direction

    # Adjacent cell == the neighbour in the opposide direction to wind, right_diag is the cell to the right of the adjacent cell, left_diag is cell to left of adjacent cell
    right_diag, adjacent, left_diag = wind_opp.get(wind_direction)

    #boolean mask thats true for all cells where the adjacent neighbour is not burning.
    center_not_burning = (neighbourstates[adjacent] <= 4) 
    # boolean mask where only diagonal neighbours are burning
    diagonal_burning = ((neighbourstates[right_diag] > 4) | (neighbourstates[left_diag] > 4)) & center_not_burning 
    # boolean mask where adjacent neighbour is burning but diagonals can also burn
    adjacent_burning = (neighbourstates[adjacent] > 4)


    # boolean mask where any from diagonals and adjacent are burning
    uniform_wind_affect = (neighbourstates[right_diag] > 4) | (neighbourstates[left_diag] > 4) | (neighbourstates[adjacent]>4)

    #p_grid will only store states for specified subarray
    p_grid[to_burning] = grid[to_burning]
    if p_grid[to_burning].size > 0:
        #changes each state in subarray to its p value where p = probability to burn e.g [1,4] = [0,0.8]
        p_grid[to_burning] = apply_probability_burn(p_grid[to_burning])
        p_grid[to_burning] *= 0.5

        #UNCOMMENT TWO LINES BELOW TO GIVE LOWER PROBABILITY TO DIAGONAL AND HIGHER TO ADJACENT  
        p_grid[adjacent_burning]  =  (p_grid[adjacent_burning] /0.5) * 1.25
        p_grid[diagonal_burning]  =  (p_grid[diagonal_burning] /0.5) * 1.05

       #Comment out line below if you uncommented 2 lines above (gives diagonal and adjacent same probability increase becuase of wind)
        # p_grid[uniform_wind_affect] =  (p_grid[uniform_wind_affect]/0.5) * 1.25

        #using the probability stored it outputs either 1 or 0 e.g. [0,0.8] might equal [0,1]
        p_grid[to_burning] = p_change2_vec(p_grid[to_burning])
    
    #for every element in grid thats equal to 1 in p_grid, change its state to burning (add 5)
    grid[p_grid==1] += 5


    #set all the newly burning cells to their respective durations:

    newlyBurntChappral = (durations == -1) & (grid == 5) #because -1 means duration not set, so we are yet to set these burning ones (s5)
    newlyBurntForest = (durations == -1) & (grid == 7)
    newlyBurntCanyon = (durations == -1) & (grid == 8)
    newlyBurntTown = (durations == -1) & (grid == 9)
    
    #setting durations
    #one iteration is 15 mins
    durations[newlyBurntChappral] = np.random.randint((60/15 * 2), (60/15 * 8))
    durations[newlyBurntForest] = np.random.randint((60/15 * 24 * 2), (60/15 * 24 * 30)) #2 days to 30 days
    durations[newlyBurntTown] = 1
    durations[newlyBurntCanyon] = 1
    #decrement all durations by 1:

    durations[durations > 0] -= 1

    #make a burnt out cell if duration is 0

    burntOut = (durations == 0)
    print(durations)
    grid[burntOut] = 10 #10 is burnt state

    # #durations: #we are setting these in the wrong location, it gets overrided each time

    # newBurning = (p_grid == 1)

    # burningChappral = (grid[newBurning] == 5) #we do p_grid here because we only want to set the durations of things that just started burning
    # durations[burningChappral] = 2 #2 iterations (2 hrs??)

    # burningForest = (grid[newBurning]== 7)
    # durations[burningForest] = 100

    # burningLake = (grid[newBurning] == 6)
    # durations[burningLake] = 0 #doesnt burn

    # burningCanyon = (grid[newBurning] == 8)
    # durations[burningCanyon] = 1

    # burningTown = (grid[newBurning] == 9)
    # durations[burningTown] = 10

    # #decrement all durations by 1

    # durations = durations - np.ones((200,200))

    # #turn fire off if duration ran out

    # ranOut = (durations <= 0)
    # grid[ranOut] -= 5


    ###########

    # p_grid[:,:] = 0

    # p_grid[to_burnt] = grid[to_burnt]
    # if p_grid[to_burnt].size > 0:

    #     #using the state stored it outputs either 1 or 0 e.g. [1,3] might equal [0,1]
    #     p_grid[to_burnt] = apply_probability_burnt(p_grid[to_burnt])
    # grid[p_grid==1] = 10

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