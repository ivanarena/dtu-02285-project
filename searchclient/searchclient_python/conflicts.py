from action import get_box_result_location
import sys
from state import State
import copy
from algorithms import noop, sidestep, backtrack, backtrack_with_boxes


def count_consecutive_conflicts(conflicts: list[dict]) -> int:
    def is_neighbor(loc1, loc2):
        return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1]) == 1

    count = 1
    loc = conflicts[0]["location"]
    for i in range(1, len(conflicts)):
        if is_neighbor(conflicts[i]["location"], loc):
            count += 1
            loc = conflicts[i]["location"]
        else:
            break
    return count

def get_valid_locations(
    state: State,
    target: str,
    target_locs: list[tuple[int, int]],
    leader_locs: list[tuple[int, int]],
    index: int,
    ghost: bool
) -> list[tuple[int, int]]:
    
    if ghost:
        target_loc = target_locs[index-2] if index > 1 else State.initial_agents_locs[target]
        prev_loc = target_locs[index-3] if index> 2 else State.initial_agents_locs[target]
    else:
        target_loc = target_locs[index-1] if index > 0 else State.initial_agents_locs[target]
        prev_loc = target_locs[index-2] if index> 1 else State.initial_agents_locs[target]
    conflict_loc = leader_locs[index]
    
    neighbors = []
    if target_loc[0] > 0:
        neighbors.append((target_loc[0] - 1, target_loc[1]))
    if target_loc[0] < State.num_rows - 1:
        neighbors.append((target_loc[0] + 1, target_loc[1]))
    if target_loc[1] > 0:
        neighbors.append((target_loc[0], target_loc[1] - 1))
    if target_loc[1] < State.num_cols - 1:
        neighbors.append((target_loc[0], target_loc[1] + 1))

    valid_neighbors = []
    for loc in neighbors:
        if  loc != conflict_loc and loc != prev_loc and state.is_free(loc[0], loc[1]) and loc not in leader_locs:
            valid_neighbors.append(loc)
    return valid_neighbors

def find_conflicts(plans: dict, locations: dict) -> dict:
    print("Looking for conflicts...", file=sys.stderr, flush=True)
    conflicts = {}

    # Find the maximum length of locations among all agents
    max_locations_length = max(len(locs) for locs in locations.values() if locs)        
    for i in range(max_locations_length):
        for first, locs in locations.items():
            if i < len(locs):  # ! Check if the agent has a location at index i, if it doesn't use last location !!
                for second, other_locs in locations.items():
                    if first != second and i < len(other_locs):  # Check if the leader agent has a location at index i
                        conflict_type = None

                        if 'M' in str(plans[first][i][0]):
                            if 'M' in str(plans[second][i][0]): # move conflict
                                if locs[i] == other_locs[i]: 
                                    conflict_type = "two_agents_same_location"
                                else:
                                    first_prev_loc = locs[i-1] if i > 0 else State.initial_agents_locs[first]
                                    second_prev_loc = other_locs[i-1] if i > 0 else State.initial_agents_locs[second]
                                    if locs[i] == second_prev_loc or other_locs[i] == first_prev_loc:
                                        conflict_type = "agent_through_agent"
                            elif 'NoOp' in str(plans[second][i][0]): # 2nd agent is static
                                if locs[i] == other_locs[i]: 
                                    conflict_type = "agent_through_static_agent"
                        elif 'M' in str(plans[second][i][0]): # move conflict
                            if 'NoOp' in str(plans[first][i][0]): # 1st agent is static
                                if locs[i] == other_locs[i]: 
                                    conflict_type = "static_agent_through_agent"
                                # Store conflict details
                        if 'M' not in str(plans[first][i][0]) or 'M' not in str(plans[second][i][0]): # push/pull conflict
                            first_box_loc = get_box_result_location(plans[first][i][0], locations[first][i]) if 'M' not in str(plans[first][i][0]) else None
                            second_box_loc = get_box_result_location(plans[second][i][0], locations[second][i]) if 'M' not in str(plans[second][i][0]) else None
                            first_prev_loc = locs[i-1] if i > 0 else State.initial_agents_locs[first]
                            second_prev_loc = other_locs[i-1] if i > 0 else State.initial_agents_locs[second]
                            
                            if first_box_loc and not second_box_loc:
                                if first_box_loc == other_locs[i]:
                                    if 'Pull' in plans[second][i]:
                                        conflict_type = "two_boxes_same_location"
                                    else: 
                                        conflict_type = "box_through_agent"

                            elif not first_box_loc and second_box_loc:
                                if locs[i] == second_box_loc: conflict_type = "agent_through_box"
                            elif first_box_loc and second_box_loc:
                                if first_box_loc == second_box_loc:
                                    conflict_type = "two_boxes_same_location"
                                elif locs[i] == second_box_loc:
                                    conflict_type = "agent_through_box"
                                elif first_box_loc == other_locs[i]:
                                    conflict_type = "box_through_agent"
                                elif first_box_loc == second_prev_loc: 
                                    conflict_type = 'first_box_through_second_agent_prev'
                                elif first_prev_loc == second_box_loc: 
                                    conflict_type = 'second_box_through_first_agent_prev'
                        if conflict_type:
                            if first not in conflicts:
                                conflicts[first] = {}
                            if second not in conflicts[first]:
                                conflicts[first][second] = []
                            print(f"Conflict between agent {first} and agent {second} at location {locs[i]}, index {i} of type {conflict_type}", file=sys.stderr, flush=True)
                            conflicts[first][second].append({
                                "index": i,
                                "location": locs[i],
                                "type": conflict_type
                            })

        # TODO: check for boxes conflicts (compare moves with previous locations)
        # ...
    return conflicts