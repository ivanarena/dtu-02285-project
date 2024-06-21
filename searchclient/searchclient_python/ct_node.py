import copy
import heapq
import sys
from algorithms import backtrack, backtrack_with_boxes, noop, sidestep
from conflicts import count_consecutive_conflicts, get_valid_locations
from state import State
import state
import itertools as ite
from action import get_box_result_location


class Node:
    _id_counter = ite.count()

    def __init__(self, state: State, target: str, leader: str, locations: dict, plans: dict, cost: int, conflicts: dict, parent=None):
        self.state = state
        self.id = next(Node._id_counter)
        self.locations = locations
        self.plans = plans
        self.cost = cost
        self.parent = parent
        self.children = []
        self.target = target
        self.leader = leader
        self.conflicts = conflicts
        if parent:
            parent.children.append(self)  # Automatically add this node to the parent's children list


    def __lt__(self, other):
        return (self.cost, self.id) < (other.cost, other.id)


    def pick_conflict(self):
        # Ideally, pick the most severe or earliest conflict
        conflicts = self.conflicts
        for agent1, conflicts_with_others in conflicts.items():
            for agent2, conflict in conflicts_with_others.items():
                conflict1 = {"leader": agent1, "target": agent2, "conflict": conflict[0]}
                conflict2 = {"leader": agent2, "target": agent1, "conflict": conflicts[agent2][agent1][0]}
                return conflict1, conflict2
        return None  # No conflicts to pick

    
    def solve_conflict(self, target: str, leader: str, conflict: dict, plans: dict, locations: dict) -> dict:
        """
            Returns updated plans and locations after solving the conflict
        """
        copy_conflict = copy.deepcopy(conflict)
        copy_plans = copy.deepcopy(plans)
        copy_locations = copy.deepcopy(locations)

        index = copy_conflict["index"]
        conflict_type = copy_conflict["type"]

        ghost = True if conflict_type == "agent_through_agent" else False
        noop_count = 0
        if conflict_type == "first_box_through_second_agent_prev":
            noop_count = 1
            leader, target = target, leader
        if conflict_type == "second_box_through_first_agent_prev": noop_count = 1
        elif conflict_type == "box_through_agent":
            noop_count = 2
            leader, target = target, leader
        # elif conflict_type == "agent_through_box": noop_count = 2
        elif conflict_type == "two_boxes_same_location": noop_count = 3

        if noop_count > 0: # box conflict
            return noop(
                target=target, # leader stops this time since it's the one causing the conflict
                plans=copy_plans,
                locations=copy_locations,
                noop_count=noop_count,
                start=index
            )

        else:
            # NB: get_valid_locations doesnt care for the previous location of the agent so if that's the only cell available then
            # sidestep will coincide with backtrack and backtrack will be called, as len(neighbors) == 0
            neighbors = get_valid_locations(
                state=self.state, 
                target=target,
                target_locs=copy_locations[target],
                leader_locs=copy_locations[leader],
                index=index,
                ghost=ghost
            )
            if len(neighbors):
                return sidestep(
                    target=target,
                    index=index,
                    plans=copy_plans,
                    locations=copy_locations,
                    neighbors=neighbors,
                    ghost=ghost
                )
            else:
                if conflict_type == "agent_through_box":
                    return backtrack_with_boxes(
                        target=target,
                        leader=leader,
                        index=index,
                        plans=copy_plans,
                        locations=copy_locations,
                        ghost=ghost,
                    )
                else:  
                    return backtrack(
                        target=target,
                        leader=leader,
                        index=index,
                        plans=copy_plans,
                        locations=copy_locations,
                        ghost=ghost,
                    )


