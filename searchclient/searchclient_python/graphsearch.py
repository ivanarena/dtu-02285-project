
import time
import sys
import copy
from action import Action
from ct import CBS
from substate import update_state, get_reduced_state, match_goal
from algorithms import subsearch
from state import State
from conflicts import find_conflicts
from deadlock import solve_deadlock, find_deadlock

def merge(plans: dict, max_plan_length: int) -> list[list[Action]]:
    # plans is a dict with a list of actions for each agent like this
    # { '0': [action0, action1, ...], '1': [action0, action1, ...], ... } 
    # agents are represented by their id ('0', '1', ...)

    # full plan should be a list of lists of actions where each list of actions is like
    # [ agent0_action0, agent1_action0, ... ]
    # [ agent0_action1, agent1_action1, ... ]
    # [ agent0_action2, agent1_action2, ... ]

    # Initialize a list to hold the full plan
    full_plan = []
    for step in range(max_plan_length):
        actions = []
        for agent in range(State.num_agents):
            if str(agent) not in plans.keys() or len(plans[str(agent)]) <= step:
                # for now do NoOp but it's probably wrong, an idea could be going backwards to the starting position
                actions.append(Action.NoOp)
            else:
                # actions is always a list but in this case is always gonna be of length 1 because it's the plan for a single agent
                # so we can just append the first element [0] of the list
                actions.append(plans[str(agent)][step][0]) 
        full_plan.append(actions)
    return full_plan  

def count_neighbors(state: State, loc: tuple[int, int]) -> int:
    count = 0
    if loc[0] > 0 and state.walls[loc[0] - 1][loc[1]] == False:
        count += 1
    if loc[0] < State.num_rows - 1 and state.walls[loc[0] + 1][loc[1]] == False:
        count += 1
    if loc[1] > 0 and state.walls[loc[0]][loc[1] - 1] == False:
        count += 1
    if loc[1] < State.num_cols - 1 and state.walls[loc[0]][loc[1] + 1] == False:
        count += 1
    return count

def search(state: State, frontier) -> list[list[Action]]:
    initial_state = copy.deepcopy(state)
    plans = {}
    locations = {}
    goals = state.goals_map
    solving_queue = list(goals.keys())
    seen = []

    for key in solving_queue:
        # 1. Match each goal with a box and an agent
        print(f'solving goal {goals[key].type}', file=sys.stderr, flush=True)
        
        match = match_goal(state, goals[key], plans)

        if "box" not in match:
            if key not in seen:
                solving_queue.append(key)
                seen.append(key)
                continue

        if count_neighbors(state, (match["goal"].row, match["goal"].col)) < 3:
            if key not in seen:
                solving_queue.insert(-(len(seen)), key)
                seen.append(key)
                continue
        
        if match["agent"] is None:
            print(f'No agent needed for goal {goals[key].type}', file=sys.stderr, flush=True)
            continue
        
        g = 0
        if match["agent"].type in plans.keys():
            g = len(plans[match["agent"].type]) 
        reduced_state = get_reduced_state(state, match, g)
        
        # 2. Find the best action plan for each agent to make its box reach the goal using best first with some kind of heuristic (we can use the same as warmup for now)
        if reduced_state.is_subgoal_state():
            continue
        
        agent_plan, agent_locations = subsearch(reduced_state, frontier)
        
        # 4. find and solve deadlocks
        solved_deadlock = False
        deadlock = find_deadlock(
            state=state, 
            agent=match["agent"],
            agent_locations=agent_locations, 
            agent_plan=agent_plan, 
            plans=plans, 
            locations=locations, 
        )
        if deadlock is not None:
            plans, locations, state = solve_deadlock(
                state=state,
                plans=plans, 
                locations=locations, 
                box=state.boxes_map[state.boxes[agent_locations[deadlock][0]][agent_locations[deadlock][1]]],
                locked_agent=match["agent"].type,
                locked_plan=agent_plan,
                locked_locations=agent_locations,
                index=deadlock
            )
            print(f"Deadlock solved", file=sys.stderr, flush=True)
            solved_deadlock = True
        
        if not solved_deadlock:
            if match["agent"].type in plans.keys(): # if agent already has a plan append to it
                plans[match["agent"].type] += agent_plan
                locations[match["agent"].type] += agent_locations
            else: # if agent doesn't have a plan yet, create a new one
                locations[match["agent"].type] = agent_locations
                plans[match["agent"].type] = agent_plan

        state = update_state(state, match, agent_locations)
        frontier.clear()

    goalless_agents = [agent for agent in state.agents_map if agent not in plans.keys()]
    goal_agents = [agent for agent in state.agents_map if agent in plans.keys()]
    max_length = max(len(locs) for locs in locations.values() if locs)
    for agent in goalless_agents:
        if agent not in plans.keys():
            plans[agent] = [[Action.NoOp]] * max_length
            locations[agent] = [State.initial_agents_locs[agent]] * max_length
        
    
    # 5. find and solve conflicts
    conflicts = find_conflicts(plans=plans, locations=locations)

    # 6. Run CBS
    tree = CBS(initial_state=initial_state, plans=plans, locations=locations, conflicts=conflicts)
    solving_plans, solving_locations = tree.run()

    max_length = 0
    for agent, loc in solving_locations.items():
        if agent in goal_agents:
            max_length = max(max_length, len(loc))

    # 7. Merge the plans with some strategy (we can get it from papers or come up with a simple one)
    final_plan = merge(solving_plans, max_length)
    return final_plan

