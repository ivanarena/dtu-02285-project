from state import State
import copy
import sys
from entities import Box, Goal, Agent

def update_state(state: State, match: dict, agent_locations: dict) -> State:
    state.agents_map[match["agent"].type].row = agent_locations[-1][0]
    state.agents_map[match["agent"].type].col = agent_locations[-1][1]
    state.marked[(match["goal"].row, match["goal"].col)] = len(agent_locations)

    if 'box' in match.keys():
        state.boxes[match["box"].row][match["box"].col] = ''
        state.boxes_map.pop(match["box"].id)
        state.num_boxes -= 1
    return state



def get_reduced_state(state: State, match: dict, g: int) -> State:
    copied = copy.deepcopy(state)
    copied.boxes = [['' for _ in range(state.num_cols)] for _ in range(state.num_rows)]
    copied.boxes_map = {}

    if 'box' in match.keys():
        copied.boxes[match['box'].row][match['box'].col] = 0 # rename box to 0
        copied.boxes_map = { 0: match['box'] } # rename box to 0
    
    # Rename agents to 0 for compatibility with existing state.py functions
    agent = copy.deepcopy(match['agent'])
    agent.type = '0'
    copied.agents_map = {'0': agent}

    # Build new state
    reduced_state = State(copied.boxes, copied.agents_map, copied.boxes_map)
    reduced_state.goals = [['' for _ in range(state.num_cols)] for _ in range(state.num_rows)]
    reduced_state.goals[match['goal'].row][match['goal'].col] = match['goal'].type
    reduced_state.goals_map = { 0: match['goal'] }
    
    reduced_state.num_rows = copied.num_rows
    reduced_state.num_cols = copied.num_cols
    reduced_state.cells = copied.cells
    reduced_state.neighbors = copied.neighbors
    reduced_state.walls = copied.walls
    reduced_state.colors = copied.colors
    reduced_state.marked = copied.marked
    
    reduced_state.num_agents = 1
    reduced_state.num_boxes = 1
    reduced_state.num_goals = 1
    reduced_state.agents_only = False if 'box' in match.keys() else True
    reduced_state.g = g

    return reduced_state



def find_best_match(state: State, entity: Box | Goal, plans: dict) -> Agent | Box:
    if not hasattr(entity, 'color'): # if entity is a goal (goals don't have colors)
        min_distance = float('inf')
        if entity.type.isdigit(): # match agent to agent goal
            for idx, agent in state.agents_map.items():
                if agent.type == entity.type:
                    distance = abs(agent.row - entity.row) + abs(agent.col - entity.col)
                    if agent.type in plans.keys():
                        distance += len(plans[agent.type])
                    if distance < min_distance:
                        min_distance = distance
                        best_agent = agent
            return best_agent
        best_box = None
        for idx, box in state.boxes_map.items(): # match box to goal
            if box.type == entity.type:
                distance = abs(box.row - entity.row) + abs(box.col - entity.col)
                if distance < min_distance:
                    min_distance = distance
                    best_box = box
        return best_box
    else: # if entity is a box match agent to box
        min_distance = float('inf')
        best_agent = None
        for idx, agent in state.agents_map.items():
            if agent.color == entity.color:
                distance = abs(agent.row - entity.row) + abs(agent.col - entity.col)
                if agent.type in plans.keys():
                    distance += len(plans[agent.type])
                if distance < min_distance:
                    min_distance = distance
                    best_agent = agent
        return best_agent

def match_goal(state: State, goal: Goal, plans: dict) -> dict:
    if goal.type.isdigit():
        best_agent = find_best_match(state, goal, plans)
        return { "goal": goal, "agent": best_agent }
    else: 
        best_box = find_best_match(state, goal, plans)
        best_agent = find_best_match(state, best_box, plans)
        return { "goal": goal, "box": best_box, "agent": best_agent }
