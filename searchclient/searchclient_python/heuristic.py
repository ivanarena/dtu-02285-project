from abc import ABCMeta, abstractmethod
import sys
from state import State
import pprint as pp

class Heuristic(metaclass=ABCMeta):    
    def __init__(self, initial_state: 'State'):        
        pass
    
    @abstractmethod
    def f(self, state: 'State') -> 'int': pass
    
    @abstractmethod
    def __repr__(self): raise NotImplementedError

class HeuristicAStar(Heuristic):
    def __init__(self, initial_state: 'State'):
        super().__init__(initial_state)
    
    def f(self, state: 'State') -> 'int':
        return state.g + self.h(state)

    def h(self, state: 'State') -> 'int':
        if state.agents_only:
            agent_to_goal = abs(state.goals_map[0].row - state.agents_map['0'].row) + abs(state.goals_map[0].col - state.agents_map['0'].col)
            return agent_to_goal
        else:
            agent_to_box = abs(state.boxes_map[0].row - state.agents_map['0'].row) + abs(state.boxes_map[0].col - state.agents_map['0'].col)
            box_to_goal = abs(state.goals_map[0].row - state.boxes_map[0].row) + abs(state.goals_map[0].col - state.boxes_map[0].col)
            return agent_to_box + box_to_goal
    
    def __repr__(self):
        return 'A* evaluation'