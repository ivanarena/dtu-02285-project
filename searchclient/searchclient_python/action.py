from enum import Enum, unique
import sys

@unique
class ActionType(Enum):
    NoOp = 0
    Move = 1
    Push = 2
    Pull = 3

@unique
class Action(Enum):
    #   List of possible actions. Each action has the following parameters, 
    #    taken in order from left to right:
    #    1. The name of the action as a string. This is the string sent to the server
    #    when the action is executed. Note that for Pull and Push actions the syntax is
    #    "Push(X,Y)" and "Pull(X,Y)" with no spaces.
    #    2. Action type: NoOp, Move, Push or Pull (only NoOp and Move initially supported)
    #    3. agentRowDelta: the vertical displacement of the agent (-1,0,+1)
    #    4. agentColDelta: the horisontal displacement of the agent (-1,0,+1)
    #    5. boxRowDelta: the vertical displacement of the box (-1,0,+1)
    #    6. boxColDelta: the horisontal discplacement of the box (-1,0,+1) 
    #    Note: Origo (0,0) is in the upper left corner. So +1 in the vertical direction is down (S) 
    #    and +1 in the horisontal direction is right (E).
    NoOp = ("NoOp", ActionType.NoOp, 0, 0, 0, 0)

    MoveN = ("Move(N)", ActionType.Move, -1, 0, 0, 0)
    MoveS = ("Move(S)", ActionType.Move, 1, 0, 0, 0)
    MoveE = ("Move(E)", ActionType.Move, 0, 1, 0, 0)
    MoveW = ("Move(W)", ActionType.Move, 0, -1, 0, 0)

    PushSS = ("Push(S,S)", ActionType.Push, 1, 0, 1, 0)
    PushNN = ("Push(N,N)", ActionType.Push, -1, 0, -1, 0)
    PushEE = ("Push(E,E)", ActionType.Push, 0, 1, 0, 1)
    PushWW = ("Push(W,W)", ActionType.Push, 0, -1, 0, -1)

    PushEN = ("Push(E,N)", ActionType.Push, 0, 1, -1, 0)
    PushES = ("Push(E,S)", ActionType.Push, 0, 1, 1, 0)
    PushWN = ("Push(W,N)", ActionType.Push, 0, -1, -1, 0)
    PushWS = ("Push(W,S)", ActionType.Push, 0, -1, 1, 0)

    PushNE = ("Push(N,E)", ActionType.Push, -1, 0, 0, 1)
    PushSE = ("Push(S,E)", ActionType.Push, 1, 0, 0, 1)
    PushNW = ("Push(N,W)", ActionType.Push, -1, 0, 0, -1)
    PushSW = ("Push(S,W)", ActionType.Push, 1, 0, 0, -1)

    PullNN = ("Pull(N,N)", ActionType.Pull, -1, 0, -1, 0)
    PullSS = ("Pull(S,S)", ActionType.Pull, 1, 0, 1, 0)
    PullEE = ("Pull(E,E)", ActionType.Pull, 0, 1, 0, 1)
    PullWW = ("Pull(W,W)", ActionType.Pull, 0, -1, 0, -1)

    PullWS = ("Pull(W,S)", ActionType.Pull, 0, -1, 1, 0)
    PullWN = ("Pull(W,N)", ActionType.Pull, 0, -1, -1, 0)
    PullEN = ("Pull(E,N)", ActionType.Pull, 0, 1, -1, 0)
    PullES = ("Pull(E,S)", ActionType.Pull, 0, 1, 1, 0)
    
    PullSW = ("Pull(S,W)", ActionType.Pull, 1, 0, 0, -1)
    PullNW = ("Pull(N,W)", ActionType.Pull, -1, 0, 0, -1)
    PullSE = ("Pull(S,E)", ActionType.Pull, 1, 0, 0, 1)
    PullNE = ("Pull(N,E)", ActionType.Pull, -1, 0, 0, 1)

    
    def __init__(self, name, type, ard, acd, brd, bcd):
        self.name_ = name
        self.type = type
        self.agent_row_delta = ard # horisontal displacement agent (-1,0,+1)
        self.agent_col_delta = acd # vertical displacement agent (-1,0,+1)
        self.box_row_delta = brd # horisontal displacement box (-1,0,+1)
        self.box_col_delta = bcd # vertical displacement box (-1,0,+1)

def get_move_from_loc(from_loc: tuple[int, int], to_loc: tuple[int, int]) -> Action:
    if from_loc == to_loc:
        return Action.NoOp
    elif from_loc[0] == to_loc[0]:
        if from_loc[1] > to_loc[1]:
            return Action.MoveW
        else:
            return Action.MoveE
    else:
        if from_loc[0] > to_loc[0]:
            return Action.MoveN
        else:
            return Action.MoveS

def get_pull_from_loc(from_loc: tuple[int, int], to_loc: tuple[int, int], prev: Action) -> Action:
    if 'M' in str(prev):
        if prev == Action.MoveN:
            return Action.PullNN
        if prev == Action.MoveS:
            return Action.PullSS
        if prev == Action.MoveE:
            return Action.PullEE
        if prev == Action.MoveW:
            return Action.PullWW
    elif from_loc[0] == to_loc[0]:
        if from_loc[1] > to_loc[1]:
            if prev == Action.PullWW or prev == Action.PullWS or prev == Action.PullWN:
                return Action.PullWW
            if prev == Action.PullNW or prev == Action.PullNN or prev == Action.PullNE:
                return Action.PullWN
            if prev == Action.PullSW or prev == Action.PullSS or prev == Action.PullSE:
                return Action.PullWS
        else:
            if prev == Action.PullEE or prev == Action.PullES or prev == Action.PullEN:
                return Action.PullEE
            if prev == Action.PullNE or prev == Action.PullNN or prev == Action.PullNW:
                return Action.PullEN
            if prev == Action.PullSE or prev == Action.PullSS or prev == Action.PullSW:
                return Action.PullES
    else:
        if from_loc[0] > to_loc[0]:
            if prev == Action.PullNN or prev == Action.PullNE or prev == Action.PullNW:
                return Action.PullNN
            if prev == Action.PullEN or prev == Action.PullEE or prev == Action.PullES:
                return Action.PullNE
            if prev == Action.PullWN or prev == Action.PullWW or prev == Action.PullWS:
                return Action.PullNW
        else:
            if prev == Action.PullSS or prev == Action.PullSE or prev == Action.PullSW:
                return Action.PullSS
            if prev == Action.PullES or prev == Action.PullEE or prev == Action.PullEN:
                return Action.PullSE
            if prev == Action.PullWS or prev == Action.PullWW or prev == Action.PullWN:
                return Action.PullSW


def get_pull_from_box_loc(box_from_loc: tuple[int, int], box_to_loc: tuple[int, int], agent_loc: tuple[int, int]) -> Action:
    if box_from_loc[0] == box_to_loc[0]:
        if box_from_loc[1] > box_to_loc[1]:
            if agent_loc[1] > box_from_loc[1]:
                return Action.PullWW
            else:
                return Action.PullSW
        else:
            if agent_loc[1] < box_from_loc[1]:
                return Action.PullEE
            else:
                return Action.PullSE
    else:
        if box_from_loc[0] > box_to_loc[0]:
            if agent_loc[0] > box_from_loc[0]:
                return Action.PullNN
            else:
                return Action.PullNW
        else:
            if agent_loc[0] < box_from_loc[0]:
                return Action.PullSS
            else:
                return Action.PullSW


def get_push_from_box_loc(box_from_loc: tuple[int, int], box_to_loc: tuple[int, int], agent_loc: tuple[int, int]) -> Action:
    if box_from_loc[0] == box_to_loc[0]:
        if box_from_loc[1] > box_to_loc[1]:
            if agent_loc[1] > box_from_loc[1]:
                return Action.PushWW
            else:
                return Action.PushSW
        else:
            if agent_loc[1] < box_from_loc[1]:
                return Action.PushEE
            else:
                return Action.PushSE
    else:
        if box_from_loc[0] > box_to_loc[0]:
            if agent_loc[0] > box_from_loc[0]:
                return Action.PushNN
            else:
                return Action.PushNW
        else:
            if agent_loc[0] < box_from_loc[0]:
                return Action.PushSS
            else:
                return Action.PushSW

def get_push_from_loc(from_loc: tuple[int, int], to_loc: tuple[int, int], prev: Action) -> Action:
    if 'M' in str(prev):
        if prev == Action.MoveN:
            return Action.PushNN
        if prev == Action.MoveS:
            return Action.PushSS
        if prev == Action.MoveE:
            return Action.PushEE
        if prev == Action.MoveW:
            return Action.PushWW
    elif from_loc[0] == to_loc[0]:
        if from_loc[1] > to_loc[1]:
            if prev == Action.PushWW or prev == Action.PushWS or prev == Action.PushWN:
                return Action.PushWW
            if prev == Action.PushNW or prev == Action.PushNN or prev == Action.PushNE:
                return Action.PushWN
            if prev == Action.PushSW or prev == Action.PushSS or prev == Action.PushSE:
                return Action.PushWS
        else:
            if prev == Action.PushEE or prev == Action.PushES or prev == Action.PushEN:
                return Action.PushEE
            if prev == Action.PushNE or prev == Action.PushNN or prev == Action.PushNW:
                return Action.PushEN
            if prev == Action.PushSE or prev == Action.PushSS or prev == Action.PushSW:
                return Action.PushES
    else:
        if from_loc[0] > to_loc[0]:
            if prev == Action.PushNN or prev == Action.PushNE or prev == Action.PushNW:
                return Action.PushNN
            if prev == Action.PushEN or prev == Action.PushEE or prev == Action.PushES:
                return Action.PushNE
            if prev == Action.PushWN or prev == Action.PushWW or prev == Action.PushWS:
                return Action.PushNW
        else:
            if prev == Action.PushSS or prev == Action.PushSE or prev == Action.PushSW:
                return Action.PushSS
            if prev == Action.PushES or prev == Action.PushEE or prev == Action.PushEN:
                return Action.PushSE
            if prev == Action.PushWS or prev == Action.PushWW or prev == Action.PushWN:
                return Action.PushSW
            
def get_opposite_move_action(action: Action) -> Action:
    if action == Action.MoveN:
        return Action.MoveS
    elif action == Action.MoveS:
        return Action.MoveN
    elif action == Action.MoveE:
        return Action.MoveW
    elif action == Action.MoveW:
        return Action.MoveE
    else:
        return Action.NoOp
    
def get_pull_from_push(action: Action) -> Action:
    if action == Action.PushSS:
        return Action.PullNN
    elif action == Action.PushNN:
        return Action.PullSS
    elif action == Action.PushEE:
        return Action.PullWW
    elif action == Action.PushWW:
        return Action.PullEE
    elif action == Action.PushEN:
        return Action.PullWS
    elif action == Action.PushES:
        return Action.PullWN
    elif action == Action.PushWN:
        return Action.PullES
    elif action == Action.PushWS:
        return Action.PullEN
    elif action == Action.PushNE:
        return Action.PullSW
    elif action == Action.PushNW:
        return Action.PullSE
    elif action == Action.PushSE:
        return Action.PullNW
    elif action == Action.PushSW:
        return Action.PullNE
    else:
        return Action.NoOp

def get_box_result_location(action: Action, loc: tuple[int, int]) -> tuple[int, int]:
    if (action == Action.PushSS or action == Action.PushES or action == Action.PushWS or
        action == Action.PullNW or action == Action.PullNN or action == Action.PullNE):
        return (loc[0] + 1, loc[1])

    elif (action == Action.PushSE or action == Action.PushEE or action == Action.PushNE or
        action == Action.PullWS or action == Action.PullWW or action == Action.PullWN):
        return (loc[0], loc[1] + 1)

    elif (action == Action.PushSW or action == Action.PushWW or action == Action.PushNW or
        action == Action.PullES or action == Action.PullEE or action == Action.PullEN):
        return (loc[0], loc[1] - 1)

    elif (action == Action.PushEN or action == Action.PushWN or action == Action.PushNN or
        action == Action.PullSS or action == Action.PullSE or action == Action.PullSW):
        return (loc[0] - 1, loc[1])