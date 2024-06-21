import random
from action import Action, ActionType
import copy
import sys
class State:
    _RNG = random.Random(1)
    
    def __init__(
        self,
        boxes,
        agents_map,
        boxes_map,
    ):
        """
            Initial state parameters from level parser (fixed for all states):

            self.walls = walls
            self.colors = colors
            self.goals = goals
            self.num_agents = len(agents_map)
            self.num_boxes = len(boxes_map)
            self.num_goals = len(goals_map)
        """
        self.boxes = boxes
        self.agents_map = agents_map
        self.boxes_map = boxes_map
        self.marked = {}
        
        # other parameters
        self.parent = None
        self.joint_action = None
        self.g = 0
        self._hash = None


    
    def result(self, joint_action: '[Action, ...]') -> 'State':
        '''
        Returns the state resulting from applying joint_action in this state.
        Precondition: Joint action must be applicable and non-conflicting in this state.
        '''
        
        # Copy this state.
        boxes = [row[:] for row in self.boxes]
        
        # Apply each action.
        agents_map = copy.deepcopy(self.agents_map)
        boxes_map = copy.deepcopy(self.boxes_map)
        goals_map = copy.deepcopy(self.goals_map)
        goals = self.goals
        for agent, action in enumerate(joint_action):
            agent = str(agent)
            if action.type is ActionType.NoOp:
                pass
            
            elif action.type is ActionType.Move:
                agents_map[agent].row += action.agent_row_delta
                agents_map[agent].col += action.agent_col_delta
            
            elif action.type is ActionType.Push:
                agents_map[agent].row += action.agent_row_delta
                agents_map[agent].col += action.agent_col_delta
                
                box_id = boxes[agents_map[agent].row][agents_map[agent].col]
                box = boxes_map[box_id]

                # update old box cell
                boxes[box.row][box.col] = ''

                box.row = agents_map[agent].row + action.box_row_delta
                box.col = agents_map[agent].col + action.box_col_delta
                
                # update new box cell
                boxes[box.row][box.col] = box_id
        
            elif action.type is ActionType.Pull:
                box_original_row = agents_map[agent].row - action.box_row_delta
                box_original_col = agents_map[agent].col - action.box_col_delta

                box_id = boxes[box_original_row][box_original_col]
                box = boxes_map[box_id]
                box.row = agents_map[agent].row
                box.col = agents_map[agent].col
                
                # update old box cell
                boxes[box_original_row][box_original_col] = ''
                # update new box cell
                boxes[box.row][box.col] = box_id

                agents_map[agent].row += action.agent_row_delta
                agents_map[agent].col += action.agent_col_delta

            
        copy_state = State(boxes, agents_map, boxes_map)
        copy_state.parent = self
        copy_state.joint_action = joint_action[:]
        copy_state.g = self.g + 1
        copy_state.goals_map = goals_map
        copy_state.goals = goals
        copy_state.num_agents = len(agents_map)
        copy_state.num_goals = len(goals_map)
        copy_state.num_boxes = len(boxes_map)
        copy_state.marked = self.marked
        copy_state.agents_only = self.agents_only

        return copy_state
    
    def is_goal_state(self) -> 'bool':
        for idx, goal in State.goals_map.items():
            if State.agents_only: # agents-only levels
                agent = self.agents_map[goal.type]
                if agent.row != goal.row or agent.col != goal.col:
                    return False
            else:
                box = self.boxes[goal.row][goal.col]
                if box == '':
                    return False
                else:
                    box = self.boxes_map[box]
                    if box.type != goal.type:
                        return False
        return True
    
    def is_subgoal_state(self) -> 'bool':
        for idx, goal in self.goals_map.items():
            if self.agents_only: # agents-only levels
                agent = self.agents_map[str(0)]
                if agent.row != goal.row or agent.col != goal.col:
                    return False
            else: 
                box = self.boxes[goal.row][goal.col]
                if box == '':
                    return False
                else:
                    box = self.boxes_map[box]
                    if box.type != goal.type:
                        return False
            return True
        
    def get_expanded_states(self) -> '[State, ...]':
        # Determine list of applicable action for each individual agent.
        applicable_actions = [[action for action in Action if self.is_applicable(agent, action)] for agent in range(self.num_agents)]
        # Iterate over joint actions, check conflict and generate child states.
    
        joint_action = [None for _ in range(self.num_agents)]
        actions_permutation = [0 for _ in range(self.num_agents)]
        expanded_states = []
        while True:
            for agent in range(self.num_agents):
                joint_action[agent] = applicable_actions[agent][actions_permutation[agent]]
                
            if not self.is_conflicting(joint_action):
                expanded_states.append(self.result(joint_action))
            
            # Advance permutation.
            done = False
            for agent in range(self.num_agents):
                if actions_permutation[agent] < len(applicable_actions[agent]) - 1:
                    actions_permutation[agent] += 1
                    break
                else:
                    actions_permutation[agent] = 0
                    if agent == self.num_agents - 1:
                        done = True
            
            # Last permutation?
            if done:
                break
        
        State._RNG.shuffle(expanded_states)
        return expanded_states
    
    def is_applicable(self, agent: 'int', action: 'Action') -> 'bool':
        agent_row = self.agents_map[str(agent)].row
        agent_col = self.agents_map[str(agent)].col
        agent_color = self.agents_map[str(agent)].color
        
        if action.type is ActionType.NoOp:
            return True
            
        elif action.type is ActionType.Move:
            destination_row = agent_row + action.agent_row_delta
            destination_col = agent_col + action.agent_col_delta
            return self.is_free(destination_row, destination_col)

        elif action.type is ActionType.Push:
            agent_destination_row = agent_row + action.agent_row_delta
            agent_destination_col = agent_col + action.agent_col_delta

            if self.boxes[agent_destination_row][agent_destination_col] != '':
                box_color = self.boxes_map[self.boxes[agent_destination_row][agent_destination_col]].color
                if box_color == agent_color:
                    box_destination_row = agent_destination_row + action.box_row_delta
                    box_destination_col = agent_destination_col + action.box_col_delta
                    return self.is_free(box_destination_row, box_destination_col)            
            return False
        
        elif action.type is ActionType.Pull:
            agent_destination_row = agent_row + action.agent_row_delta
            agent_destination_col = agent_col + action.agent_col_delta
            opposite_dir_row = agent_row - action.box_row_delta
            opposite_dir_col = agent_col - action.box_col_delta

            if self.is_free(agent_destination_row, agent_destination_col) and self.boxes[opposite_dir_row][opposite_dir_col] != '':
                box_color = self.boxes_map[self.boxes[opposite_dir_row][opposite_dir_col]].color
                if box_color == agent_color:
                    return self.is_free(agent_destination_row, agent_destination_col)
            return False

    def is_conflicting(self, joint_action: '[Action, ...]') -> 'bool':
        destination_rows = [None for _ in range(self.num_agents)] # row of new cell to become occupied by action
        destination_cols = [None for _ in range(self.num_agents)] # column of new cell to become occupied by action
        box_rows = [None for _ in range(self.num_agents)] # current row of box moved by action
        box_cols = [None for _ in range(self.num_agents)] # current column of box moved by action
        
        # Collect cells to be occupied and boxes to be moved.
        for agent in range(self.num_agents):
            action = joint_action[agent]
            agent_row = self.agents_map[str(agent)].row
            agent_col = self.agents_map[str(agent)].col
            
            if action.type is ActionType.NoOp:
                pass
            
            elif action.type is ActionType.Move:
                destination_rows[agent] = agent_row + action.agent_row_delta
                destination_cols[agent] = agent_col + action.agent_col_delta
                box_rows[agent] = agent_row # Distinct dummy value.
                box_cols[agent] = agent_col # Distinct dummy value.
                    
        for a1 in range(self.num_agents):
            if joint_action[a1] is Action.NoOp:
                continue
            
            for a2 in range(a1 + 1, self.num_agents):
                if joint_action[a2] is Action.NoOp:
                    continue
                
                # Moving into same cell?
                if destination_rows[a1] == destination_rows[a2] and destination_cols[a1] == destination_cols[a2]:
                    return True
                        
        return False
    
    def is_free(self, row: 'int', col: 'int') -> 'bool':
        no_wall = not State.walls[row][col] 
        no_box = self.boxes[row][col] == ''
        no_agent = self.agent_at(row, col) is None
        no_marked = (row,col) not in self.marked
        if not no_marked:
            if self.marked[(row,col)] >= self.g: # only mark if its after solving goal
                no_marked = True
        return no_wall and no_box and no_agent and no_marked
    
    def agent_at(self, row: 'int', col: 'int') -> 'char':
        for idx, agent in self.agents_map.items():
            if agent.row == row and agent.col == col:
                return chr(int(agent.type) + ord('0'))
        return None
    
    def extract_plan(self) -> '[Action, ...]':
        plan = [None for _ in range(self.g)]
        state = self
        while state.joint_action is not None:
            plan[state.g - 1] = state.joint_action
            state = state.parent
        return plan
    
    def extract_plan_with_locations(self):
        plan = []
        locations = []
        state = self
        while state.joint_action is not None:
            plan.append(state.joint_action)
            # this function is only used by subgoal planner so it's safe to assume there's always only one agent
            locations.append((state.agents_map['0'].row, state.agents_map['0'].col))
            state = state.parent
        plan.reverse()
        locations.reverse()
        return plan, locations
        
    def __hash__(self):
        if self._hash is None:
            prime = 31
            _hash = 1
            _hash = _hash * prime + hash(tuple((agent.color, agent.row, agent.col) for agent in self.agents_map.values()))
            _hash = _hash * prime + hash(tuple(tuple(row) for row in self.boxes))
            _hash = _hash * prime + hash(tuple(State.colors))
            _hash = _hash * prime + hash(tuple(tuple(row) for row in State.goals))
            _hash = _hash * prime + hash(tuple(tuple(row) for row in State.walls))
            self._hash = _hash
        return self._hash
    
    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, State): 
            return False
        if self.agents_map != other.agents_map: 
            return False
        if State.walls != other.walls: 
            return False
        if self.boxes != other.boxes: 
            return False
        if State.colors != other.colors: 
            return False
        if self.goals_map != other.goals_map: 
            return False
        return True
    
    def __repr__(self):
        lines = []
        for row in range(len(self.boxes)):
            line = []
            for col in range(len(self.boxes[row])):
                if self.boxes[row][col] != '': line.append(str(self.boxes[row][col]))
                elif State.walls[row][col]: line.append('+')
                elif self.agent_at(row, col) is not None: line.append(self.agent_at(row, col))
                else: line.append(' ')
            lines.append(''.join(line))
        return '\n'.join(lines)
