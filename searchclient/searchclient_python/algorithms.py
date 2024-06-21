from action import *
from state import State
from heuristic import HeuristicAStar
from entities import Box, Goal
from substate import find_best_match
from frontier import FrontierBestFirst
from substate import get_reduced_state
import sys
import memory
import time
globals().update(Action.__members__)
start_time = time.perf_counter()
goal_counter = 0

def noop(target: str, plans: dict, locations: dict, noop_count: int, start: int) -> dict:
    """
        Add noop actions to the beginning of the plan of the target agent
    """
    print(f"Agent {target} will noop", file=sys.stderr, flush=True)
    plans[target] = [[Action.NoOp]] * noop_count + plans[target]
    if start != 0:
        locations[target] = [locations[target][0]] * noop_count + locations[target] 
    else: 
        locations[target] = [State.initial_agents_locs[target]] * noop_count + locations[target]
    return plans, locations


def sidestep(target: str, index: int, plans: dict, locations: dict, neighbors: list, ghost: bool) -> dict:
    print(f"Agent {target} will sidestep with neighbors {neighbors}", file=sys.stderr, flush=True)
    if ghost: index -= 1
    from_loc = locations[target][index-1]
    to_loc = neighbors[0]
    noop_count = 2 if not ghost else 3
    # understand direction
    action = get_move_from_loc(from_loc, to_loc)
    opposite_action = get_opposite_move_action(action)

    plans[target] = plans[target][:index] + [[action]] + [[Action.NoOp]] * noop_count + [[opposite_action]] + plans[target][index:]
    locations[target] = locations[target][:index] + [to_loc] * (noop_count+1) + [from_loc] + locations[target][index:]
    return plans, locations


def backtrack_with_boxes(target: str, leader: str, index: int, plans: dict, locations: dict, ghost: bool) -> dict:
    print(f"Agent {target} will backtrack with boxes", file=sys.stderr, flush=True)
    backtrack_actions = []
    backtrack_locations = []
    noop_count = 2
    
    up = index
    down = index
    
    box_loc = get_box_result_location(plans[target][down][0], locations[target][down])
    last_action = plans[target][down][0] if down > 0 else None
    while (locations[leader][up] == box_loc and down >= 0):
        up += 1
        down -= 1
        opposite_action = get_pull_from_push(plans[target][down][0])
        last_action = opposite_action if opposite_action != Action.NoOp else last_action
        backtrack_actions.append([opposite_action])
        box_loc = get_box_result_location(plans[target][down][0], locations[target][down])
        if down == 0:
            noop_count += 1
            backtrack_locations.append(State.initial_agents_locs[target])
        else:
            backtrack_locations.append(locations[target][down-1])
    
    if down < 0:
        down += 1
    else:
        noop_count = 1
    backtrack_actions += [[Action.NoOp]] * noop_count
    backtrack_locations += [backtrack_locations[-1]] * noop_count

    plans[target] = plans[target][:index] + backtrack_actions + plans[target][down+1:]
    locations[target] = locations[target][:index] + backtrack_locations + locations[target][down+1:]

    return plans, locations


def backtrack(target: str, leader: str, index: int, plans: dict, locations: dict, ghost: bool) -> dict:
    print(f"Agent {target} will backtrack", file=sys.stderr, flush=True)
    backtrack_actions = []
    backtrack_locations = []
    noop_count = 0
    up = index
    down = index
    if ghost:
        down -= 1
    last_action = plans[target][down][0] if down > 0 else None
    while (locations[leader][up] == locations[target][down] and down >= 0):
        up += 1
        down -= 1
        opposite_action = get_opposite_move_action(plans[target][down][0])
        last_action = opposite_action if opposite_action != Action.NoOp else last_action
        backtrack_actions.append([get_opposite_move_action(plans[target][down][0])])
        if down <= 0:
            noop_count += 1
            backtrack_locations.append(State.initial_agents_locs[target])
        else:
            backtrack_locations.append(locations[target][down-1])
    
    if down < 0:
        down += 1
    else:
        noop_count = 1
    backtrack_actions += [[Action.NoOp]] * noop_count
    backtrack_locations += [backtrack_locations[-1]] * noop_count

    if ghost:
        plans[target] = plans[target][:index-1] + backtrack_actions + plans[target][down:]
        locations[target] = locations[target][:index-1] + backtrack_locations + locations[target][down:]
    else:
        plans[target] = plans[target][:index] + backtrack_actions + plans[target][down:]
        locations[target] = locations[target][:index] + backtrack_locations + locations[target][down:]

    return plans, locations


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
        plans[locked_agent] = [[Action.NoOp]] * len(solving_plan) + locked_plan + plans[locked_agent]
        locations[locked_agent] = [State.initial_agents_locs[locked_agent]] * len(solving_plan) + locked_locations + locations[locked_agent]
    else:
        plans[locked_agent] = [[Action.NoOp]] * len(solving_plan) + locked_plan
        locations[locked_agent] = [State.initial_agents_locs[locked_agent]] * len(solving_plan) + locked_locations
    if solver_agent.type in plans.keys():
        plans[solver_agent.type] += full_solving_plan
        locations[solver_agent.type] += full_solving_locations
    else:
        locations[solver_agent.type] = full_solving_locations
        plans[solver_agent.type] = full_solving_plan

    state.agents_map[solver_agent.type].row = full_solving_locations[-1][0]
    state.agents_map[solver_agent.type].col = full_solving_locations[-1][1]
    state.boxes[box_loc[0]][box_loc[1]] = state.boxes[box.row][box.col]
    state.boxes[box.row][box.col] = ''
    state.boxes_map[state.boxes[box_loc[0]][box_loc[1]]].row = box_loc[0]
    state.boxes_map[state.boxes[box_loc[0]][box_loc[1]]].col = box_loc[1]
    return plans, locations, state


def subsearch(initial_state: State, frontier) -> State:
    iterations = 0
    # count how many agents are at their destination
    frontier.add(initial_state)
    explored = set()
    
    while True:
        iterations += 1
        if iterations % 1000  == 0:
            print_search_status(explored, frontier)

        if memory.get_usage() > memory.max_usage:
            print_search_status(explored, frontier)
            print('Maximum memory usage exceeded.', file=sys.stderr, flush=True)
            return None
        
        if frontier.is_empty():
            return None

        # choose new state, and remove it from frontier
        current_state = frontier.pop()
        if (current_state.is_subgoal_state()):
            print_search_status(explored, frontier)
            return current_state.extract_plan_with_locations()
        
        for child in current_state.get_expanded_states():
            if (not frontier.contains(child) and (child not in explored)):
                explored.add(child) # this wasnt used, weird
                frontier.add(child)


def print_search_status(explored, frontier):
    status_template = '#Expanded: {:8,}, #Frontier: {:8,}, #Generated: {:8,}, Time: {:3.3f} s\n[Alloc: {:4.2f} MB, MaxAlloc: {:4.2f} MB]'
    elapsed_time = time.perf_counter() - start_time
    print(status_template.format(len(explored), frontier.size(), len(explored) + frontier.size(), elapsed_time, memory.get_usage(), memory.max_usage), file=sys.stderr, flush=True)