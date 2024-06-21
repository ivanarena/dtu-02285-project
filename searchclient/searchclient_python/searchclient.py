import argparse
import io
import sys
import time
import copy
import cProfile

import memory
from color import Color
from ct import CBS
from state import State
from frontier import FrontierBFS, FrontierDFS, FrontierBestFirst
from heuristic import HeuristicAStar #, HeuristicWeightedAStar, HeuristicGreedy
from graphsearch import search
from entities import Agent, Box, Goal


class SearchClient:
    @staticmethod
    def parse_level(server_messages) -> 'State':
        # We can assume that the level file is conforming to specification, since the server verifies this.
        # Read domain.
        server_messages.readline() # #domain
        server_messages.readline() # hospital
        
        # Read Level name.
        server_messages.readline() # #levelname
        server_messages.readline() # <name>
        
        # Read colors.
        server_messages.readline() # #colors

        colors = {}
        line = server_messages.readline()
        while not line.startswith('#'):
            split = line.split(':')
            color = Color.from_string(split[0].strip())
            entities = [e.strip() for e in split[1].split(',')]
            for e in entities:
                colors[e] = color
            line = server_messages.readline()
        
        # Read initial state.
        # line is currently "#initial".
        num_rows = 0
        num_cols = 0
        level_lines = []
        line = server_messages.readline()
        while not line.startswith('#'):
            line = line[:-1] # ignore '\r\n'
            level_lines.append(line)
            num_cols = max(num_cols, len(line))
            num_rows += 1
            line = server_messages.readline()

        walls = [[False for _ in range(num_cols)] for _ in range(num_rows)]
        boxes = [['' for _ in range(num_cols)] for _ in range(num_rows)]
        
        cells = {}
        agents_map = {}
        boxes_map = {}
        cell_id = 0
        box_id = 0
        row = 0
        initial_agents_locs = {}
        for line in level_lines:
            for col, c in enumerate(line):
                # cells
                if c != '+' and row > 0 and row < len(level_lines) - 1:
                    cells[cell_id] = (row, col)
                    cell_id += 1 
                
                    # agents
                    if '0' <= c <= '9':
                        agent = Agent(type=c, color=colors[c], row=row, col=col)
                        agents_map[c] = agent
                        initial_agents_locs[c] = (row, col)
                    # boxes
                    elif 'A' <= c <= 'Z':
                        box = Box(id=box_id, color=colors[c], row=row, col=col, type=c)
                        boxes_map[box_id] = box
                        boxes[row][col] = box_id
                        
                        box_id += 1 # Increment box id
                # walls 
                elif c == '+':
                    walls[row][col] = True            
            row += 1
        
        # Read goal state.
        # line is currently "#goal".
        goals_map = {}
        goal_id = 0
        goals = [['' for _ in range(num_cols)] for _ in range(num_rows)]
        line = server_messages.readline()
        row = 0
        agents_only = False
        while not line.startswith('#'):
            for col, c in enumerate(line):
                if '0' <= c <= '9': # agent goal
                    agents_only = True
                    goal = Goal(id=goal_id, type=c, row=row, col=col)
                    goals_map[goal_id] = goal
                    goal_id += 1
            
                    goals[row][col] = c
                
                elif 'A' <= c <= 'Z': # box goal
                    goal = Goal(id=goal_id, type=c, row=row, col=col)
                    goals_map[goal_id] = goal
                    goal_id += 1

                    goals[row][col] = c
            
            row += 1
            line = server_messages.readline()
        
        # End.
        # line is currently "#end".

        # These are fixed for all states
        State.num_rows = num_rows
        State.num_cols = num_cols
        State.cells = cells
        State.neighbors = SearchClient.get_cells_neighbors(num_rows, num_cols, cells)
        State.walls = walls
        State.colors = colors
        State.goals = goals
        State.agents_only = agents_only
        State.num_agents = len(agents_map)
        State.num_boxes = len(boxes_map)
        State.num_goals = len(goals_map)
        State.initial_agents_locs = initial_agents_locs
        State.manhattan = {}
        
        # These are instantiated every time a new state is created
        State.agents_map = agents_map
        State.boxes_map = boxes_map
        State.goals_map = goals_map

        return State(boxes, agents_map, boxes_map)

    @staticmethod
    def get_cells_neighbors(num_rows, num_cols, cells):
        neighbors = {cell_id: [] for cell_id in cells.keys()}

        for cell_id, (row, col) in cells.items():
            # Define the possible directions of neighbors: up, down, left, and right
            directions = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]

            for neighbor_row, neighbor_col in directions:
                # Check if the neighboring cell is within the bounds of the grid
                if 0 <= neighbor_row < num_rows and 0 <= neighbor_col < num_cols:
                    # Find the cell ID of the neighboring cell
                    for id, (r, c) in cells.items():
                        if (r, c) == (neighbor_row, neighbor_col):
                            neighbors[cell_id].append(id)
                            break
        return neighbors

    
    @staticmethod
    def print_search_status(start_time: 'int', explored: '{State, ...}', frontier: 'Frontier') -> None:
        status_template = '#Expanded: {:8,}, #Frontier: {:8,}, #Generated: {:8,}, Time: {:3.3f} s\n[Alloc: {:4.2f} MB, MaxAlloc: {:4.2f} MB]'
        elapsed_time = time.perf_counter() - start_time
        print(status_template.format(len(explored), frontier.size(), len(explored) + frontier.size(), elapsed_time, memory.get_usage(), memory.max_usage), file=sys.stderr, flush=True)

    @staticmethod
    def main(args) -> None:
        # Use stderr to print to the console.
        print('PIAF initializing. I am sending this using the error output stream.', file=sys.stderr, flush=True)
        
        # Send client name to server.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding='ASCII')
        print('PIAF', flush=True)
        
        # We can also print comments to stdout by prefixing with a #.
        #print('#This is a comment.', flush=True)
        
        # Parse the level.
        server_messages = sys.stdin
        if hasattr(server_messages, "reconfigure"):
            server_messages.reconfigure(encoding='ASCII')
        initial_state = SearchClient.parse_level(server_messages)
        
        # Select search strategy.
        frontier = None
        if args.bfs:
            frontier = FrontierBFS()
        elif args.dfs:
            frontier = FrontierDFS()
        elif args.astar:
            frontier = FrontierBestFirst(HeuristicAStar(initial_state))
        else:
            # Default to BFS search.
            frontier = FrontierBFS()
            print('Defaulting to BFS search. Use arguments -bfs, -dfs, -astar, -wastar, or -greedy to set the search strategy.', file=sys.stderr, flush=True)
        
        # Search for a plan.
        print('Starting {}.'.format(frontier.get_name()), file=sys.stderr, flush=True)
        plan = search(initial_state, frontier)
        
        # Print plan to server.
        if plan is None:
            print('Unable to solve level.', file=sys.stderr, flush=True)
            sys.exit(0)
        else:
            print('Found solution of length {}.'.format(len(plan)), file=sys.stderr, flush=True)
            
            for joint_action in plan:
                print("|".join(a.name_ + "@" + a.name_ for a in joint_action), flush=True)
                # We must read the server's response to not fill up the stdin buffer and block the server.
                response = server_messages.readline()

if __name__ == '__main__':
    # Program arguments.
    parser = argparse.ArgumentParser(description='Simple client based on state-space graph search.')
    parser.add_argument('--max-memory', metavar='<MB>', type=float, default=2048.0, help='The maximum memory usage allowed in MB (soft limit, default 2048).')
    
    strategy_group = parser.add_mutually_exclusive_group()
    strategy_group.add_argument('-bfs', action='store_true', dest='bfs', help='Use the BFS strategy.')
    strategy_group.add_argument('-dfs', action='store_true', dest='dfs', help='Use the DFS strategy.')
    strategy_group.add_argument('-astar', action='store_true', dest='astar', help='Use the A* strategy.')
    strategy_group.add_argument('-wastar', action='store', dest='wastar', nargs='?', type=int, default=False, const=5, help='Use the WA* strategy.')
    strategy_group.add_argument('-greedy', action='store_true', dest='greedy', help='Use the Greedy strategy.')
    
    args = parser.parse_args()
    
    # Set max memory usage allowed (soft limit).
    memory.max_usage = args.max_memory
    
    # Run client.
    SearchClient.main(args)
