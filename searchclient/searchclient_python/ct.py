import heapq
import sys
from ct_node import Node
from state import State
import copy
from conflicts import find_conflicts
class CBS:
    def __init__(self, initial_state: State, plans: dict, locations: dict, conflicts: dict):
        self.initial_state = initial_state
        self.plans = plans
        self.locations = locations
        self.frontier = []
        self.conflicts = conflicts
        
        self.root = Node(
            state=initial_state,
            target=None,
            leader=None,
            locations=locations,
            plans=plans,
            cost=0,
            conflicts=conflicts,    
        )  # Assume cost starts at 0
        heapq.heappush(self.frontier, (0, self.root))
    
    def print_tree(self, node, depth=0):
        if node is None:
            return
        # Print current node with indent based on depth
        indent = "  " * depth
        print(f"{indent}Node ID: {node.id}, Cost: {node.cost}, Target: {node.target}, Leader: {node.leader}, Parent ID: {node.parent.id if node.parent else 'None'}", file=sys.stderr)
        # Recursively print each child (this requires that children are easily accessible; see note below)
        for child in node.children:  # This requires that you maintain a list of children in each node
            self.print_tree(child, depth + 1)

    def run(self):
        print("Running CBS...", file=sys.stderr, flush=True)

        while self.frontier:
        
            current_cost, current_node = heapq.heappop(self.frontier)

            if not current_node.conflicts:
                print("Solution found", file=sys.stderr, flush=True)
                return current_node.plans, current_node.locations  # SOLUTION FOUND

            # conflict is a tuple with both conflicts
            conflict1, conflict2 = current_node.pick_conflict()

            if conflict1 and conflict2:
                # Creating two new nodes: one resolving conflict for the target, another for the leader
                new_plans1, new_locations1 = current_node.solve_conflict(
                    target = conflict1["target"], 
                    leader = conflict1["leader"],
                    conflict = conflict1["conflict"],
                    plans = current_node.plans,
                    locations =  current_node.locations
                )
                node1_cost = current_cost + len(new_locations1[conflict1['target']]) - len(current_node.locations[conflict1["target"]]) 
                node1 = Node(
                    state=self.initial_state,
                    leader=conflict1["leader"],
                    target=conflict1["target"],
                    plans=new_plans1, 
                    locations=new_locations1, 
                    cost=node1_cost,
                    conflicts=find_conflicts(new_plans1, new_locations1), 
                    parent=current_node
                )
                heapq.heappush(self.frontier, (node1.cost, node1)) # Push new node
                print(f"Pushed new node with cost {node1.cost}, and ID {node1.id}", file=sys.stderr, flush=True)

                new_plans2, new_locations2 = current_node.solve_conflict(
                    target = conflict2["target"], 
                    leader = conflict2["leader"],
                    conflict = conflict2["conflict"],
                    plans = current_node.plans,
                    locations =  current_node.locations
                )


                node2_cost = current_cost + len(new_locations2[conflict2['target']]) - len(current_node.locations[conflict2["target"]]) 
                node2 = Node(
                    state=self.initial_state,
                    leader=conflict2["leader"],
                    target=conflict2["target"],
                    plans=new_plans2, 
                    locations=new_locations2, 
                    cost=node2_cost, 
                    conflicts=find_conflicts(new_plans2, new_locations2),
                    parent=current_node
                )
                
                if not node1.conflicts and not node2.conflicts:
                    if node1.cost > node2.cost:
                        return node2.plans, node2.locations
                    else:
                        return node1.plans, node1.locations
                elif not node1.conflicts:
                    return node1.plans, node1.locations
                elif not node2.conflicts:
                    return node2.plans, node2.locations
                    
                heapq.heappush(self.frontier, (node2.cost, node2)) # Push new node
                print(f"Pushed new node with cost {node2.cost}, and ID {node2.id}", file=sys.stderr, flush=True)
            print("Updated CBS Tree:", file=sys.stderr)
            self.print_tree(current_node)