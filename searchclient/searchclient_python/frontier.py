from abc import ABCMeta, abstractmethod
from collections import deque
from heapq import heappop, heappush
import itertools

class Frontier(metaclass=ABCMeta):
    @abstractmethod
    def add(self, state: 'State'): raise NotImplementedError
    
    @abstractmethod
    def pop(self) -> 'State': raise NotImplementedError
    
    @abstractmethod
    def is_empty(self) -> 'bool': raise NotImplementedError
    
    @abstractmethod
    def size(self) -> 'int': raise NotImplementedError
    
    @abstractmethod
    def contains(self, state: 'State') -> 'bool': raise NotImplementedError
    
    @abstractmethod
    def get_name(self): raise NotImplementedError
    
    @abstractmethod
    def clear(self): raise NotImplementedError

class FrontierBFS(Frontier):
    def __init__(self):
        super().__init__()
        self.queue = deque()
        self.set = set()
    
    def add(self, state: 'State'):
        self.queue.append(state)
        self.set.add(state)
    
    def pop(self) -> 'State':
        state = self.queue.popleft()
        self.set.remove(state)
        return state
    
    def is_empty(self) -> 'bool':
        return len(self.queue) == 0
    
    def size(self) -> 'int':
        return len(self.queue)
    
    def contains(self, state: 'State') -> 'bool':
        return state in self.set
    
    def get_name(self):
        return 'breadth-first search'
    
    def clear(self):
        self.queue.clear()
        self.set.clear()

class FrontierDFS(Frontier):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.set = set()
    
    def add(self, state: 'State'):
        self.stack.append(state)
        self.set.add(state)
    
    def pop(self) -> 'State':
        if len(self.stack) < 1:
            return None
        return self.stack.pop()

    def is_empty(self) -> 'bool':
        return len(self.stack) == 0
    
    def size(self) -> 'int':
        return len(self.stack)

    def contains(self, state: 'State') -> 'bool':
        return state in self.set
    
    def get_name(self):
        return 'depth-first search'
    
    def clear(self):
        self.stack.clear()
        self.set.clear()

class FrontierBestFirst(Frontier):
    def __init__(self, heuristic: 'Heuristic'):
        super().__init__()
        self.heuristic = heuristic
        self.pq = [] # priority queue using heapq
        self.entry_finder = {}  # mapping of states to entries
        self.counter = itertools.count()  # unique sequence count
        
    def add(self, state: 'State'):
        count = next(self.counter)
        entry = (self.heuristic.f(state), count, state)
        self.entry_finder[state] = entry
        heappush(self.pq, entry)
    
    def pop(self) -> 'State':
        (h, count, state) = heappop(self.pq)
        return state
    
    def is_empty(self) -> 'bool':
        return len(self.pq) == 0
    
    def size(self) -> 'int':
        return len(self.pq)
    
    def contains(self, state: 'State') -> 'bool':
        return state in self.entry_finder 
    
    def get_name(self):
        return 'best-first search using {}'.format(self.heuristic)

    def clear(self):
        self.pq.clear()
        self.entry_finder.clear()
        self.counter = itertools.count()
