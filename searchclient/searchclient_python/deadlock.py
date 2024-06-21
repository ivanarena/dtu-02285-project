from state import State
from action import *
from entities import *
import sys
from substate import get_reduced_state, find_best_match
from algorithms import subsearch
from frontier import FrontierBestFirst
from heuristic import HeuristicAStar

def get_deadlock_valid_locations(state: State, agent_loc: tuple[int, int], box_loc: tuple[int, int], locked_locations: list[tuple[int, int]]) -> list[tuple[int, int]]:
    neighbors = [
        [(box_loc[0] + 1, box_loc[1]),(box_loc[0] + 2, box_loc[1])],
        [(box_loc[0] - 1, box_loc[1]),(box_loc[0] - 2, box_loc[1])],
        [(box_loc[0], box_loc[1] + 1),(box_loc[0], box_loc[1] + 2)],
        [(box_loc[0], box_loc[1] - 1),(box_loc[0], box_loc[1] - 2)],
    ]
    valid_locations = []
    for neighbor in neighbors:
        # the first or is because you can pull 
        if (state.is_free(neighbor[0][0], neighbor[0][1]) or neighbor[0] == agent_loc) and neighbor[0] not in locked_locations:
            if state.is_free(neighbor[1][0], neighbor[1][1]) and neighbor[1] not in locked_locations:
                valid_locations.append(neighbor[0])
                valid_locations.append(neighbor[1])
    return valid_locations


def solve_deadlock(state: State, plans: dict, locations: dict, box: Box, locked_agent: str, locked_plan: list[Action], locked_locations: list[tuple[int, int]], index: int) -> dict:
    solver_agent = find_best_match(state, box, plans)
    print(f"Agent {solver_agent.type} will solve deadlock", file=sys.stderr, flush=True)

    subgoal = Goal(id=0, type=solver_agent.type, row=box.row, col=box.col)
    reduced_state = get_reduced_state(state, {"agent": solver_agent, "goal": subgoal}, state.g)
    frontier = FrontierBestFirst(HeuristicAStar(reduced_state))
    
    solving_plan, solving_locations = subsearch(reduced_state, frontier)
    if len(solving_plan) < 2: # agent is already at box
        solving_plan = []
        solving_locations = []
        # solver_agent_loc = State.initial_agents_locs[solver_agent.type]
        solver_agent_loc = (solver_agent.row, solver_agent.col)
        t = 0
        box_loc = (box.row, box.col)
        while (box_loc == locked_locations[index]):
            box_neighbors = get_deadlock_valid_locations(state, solver_agent_loc, box_loc, locked_locations)

            if box_neighbors:
                if box_neighbors[0] == solver_agent_loc: # pull
                    solving_plan.append([get_pull_from_box_loc(box_loc, box_neighbors[0], solver_agent_loc)])
                    solving_plan.append([get_pull_from_box_loc(box_neighbors[0], box_neighbors[1], box_neighbors[1])])
                    solving_locations.append(box_neighbors[0])
                    solving_locations.append(box_neighbors[1])
                else: # push
                    solving_plan.append([get_push_from_box_loc(box_loc, box_neighbors[0], solver_agent_loc)])
                    solving_plan.append([get_push_from_box_loc(box_neighbors[0], box_neighbors[1], box_loc)])
                    solving_locations.append(box_loc)
                    solving_locations.append(box_neighbors[0])
                box_loc = box_neighbors[1]
            t += 1
            index += 1
            if index >= len(locked_locations):
                break

        full_solving_plan = solving_plan
        full_solving_locations = solving_locations
        
    else:
        solving_plan = solving_plan[:-1]
        rev_solving_plan = solving_plan[::-1]
        solving_locations = solving_locations[:-1]
        rev_solving_locations = solving_locations[::-1]

        box_loc = (box.row, box.col)
        t = 0
        while (box_loc == locked_locations[index]):
            rev_solving_plan[t] = [get_opposite_move_action(rev_solving_plan[t][0])]
            rev_solving_plan[t] = [get_pull_from_loc(
                rev_solving_locations[t],
                rev_solving_locations[t+1],
                rev_solving_plan[t][0] if t == 0 else rev_solving_plan[t-1][0]
            )]
            box_loc = rev_solving_locations[t]
            t += 1
            index += 1

        rev_solving_plan = rev_solving_plan[:t]
        rev_solving_locations = rev_solving_locations[1:t+1]

        full_solving_plan = solving_plan + rev_solving_plan
        full_solving_locations = solving_locations + rev_solving_locations

    if locked_agent in plans.keys():
        plans[locked_agent] = plans[locked_agent] + [[Action.NoOp]] * len(solving_plan) + locked_plan
        locations[locked_agent] = locations[locked_agent] + [State.initial_agents_locs[locked_agent]] * len(solving_plan) + locked_locations
    else:
        plans[locked_agent] = [[Action.NoOp]] * len(solving_plan) + locked_plan
        locations[locked_agent] = [State.initial_agents_locs[locked_agent]] * len(solving_plan) + locked_locations
    if solver_agent.type in plans.keys():
        plans[solver_agent.type] += full_solving_plan
        locations[solver_agent.type] += full_solving_locations
    else:
        locations[solver_agent.type] = full_solving_locations
        plans[solver_agent.type] = full_solving_plan

    state.agents_map[solver_agent.type].row = full_solving_locations[-1][0] if full_solving_locations else state.agents_map[solver_agent.type].row
    state.agents_map[solver_agent.type].col = full_solving_locations[-1][1] if full_solving_locations else state.agents_map[solver_agent.type].col    
    state.boxes[box.row][box.col] = ''
    state.boxes_map[box.id].row = box_loc[0]
    state.boxes_map[box.id].col = box_loc[1]
    state.boxes[box_loc[0]][box_loc[1]] = box.id    

    return plans, locations, state

def find_deadlock(state: State, agent: Agent, agent_locations: list[tuple[int, int]], agent_plan: list[Action], plans: dict, locations: dict):
    for t in range(len(agent_locations)):
        if state.boxes[agent_locations[t][0]][agent_locations[t][1]] != '':
            if state.boxes_map[state.boxes[agent_locations[t][0]][agent_locations[t][1]]].color == agent.color:
                # maybe push just once to valid neighbors to clear path
                print('not implemented yet', file=sys.stderr, flush=True)
                pass
            else:
                if t > 10: return None
                return t
    return None        
    