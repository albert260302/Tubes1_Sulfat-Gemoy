import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

def countMoves(pos1: Position, pos2: Position):
    return abs(pos1.x-pos2.x) + abs(pos1.y-pos2.y)


class ClosestDiamond_Rafi(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None

    def next_move(self, board_bot: GameObject, board: Board):
        

        # bot props
        props = board_bot.properties

        # positions
        current_position = board_bot.position
        base = board_bot.properties.base

        # teleporters
        teleporters = [d for d in board.game_objects if d.type == "TeleportGameObject"]

        teleporter0_moves = countMoves(current_position, teleporters[0].position)
        teleporter1_moves = countMoves(current_position, teleporters[1].position)

        if (teleporter0_moves < teleporter1_moves):
            teleport_enter = teleporters[0].position
            teleport_exit = teleporters[1].position

            moves_to_teleporter = teleporter0_moves
        else:
            teleport_enter = teleporters[1].position
            teleport_exit = teleporters[0].position

            moves_to_teleporter = teleporter1_moves

        # Analyze new state
        if props.diamonds == 5:

            if countMoves(current_position, base) > countMoves(current_position, teleport_enter) + countMoves(teleport_exit, base) and current_position != teleport_enter:
                self.goal_position = teleport_enter
            else:
                self.goal_position = base
        else:
            # Find Closest
            diamonds = board.diamonds
            
            closest_diamond = diamonds[0]
            closest_diamond_via_teleport = diamonds[0]

            curr_moves = countMoves(current_position, closest_diamond.position)
            curr_moves_via_teleport = moves_to_teleporter + countMoves(teleport_exit, closest_diamond_via_teleport.position)

            for diamond in diamonds:

                if diamond.properties.points + props.diamonds == 6:
                    return_home_flag = True
                    
                else:
                    return_home_flag = False

                    new_moves = countMoves(current_position, diamond.position)
                    new_moves_via_teleport = moves_to_teleporter + countMoves(teleport_exit, diamond.position)

                    if (new_moves < curr_moves or closest_diamond.properties.points + props.diamonds == 6):
                        curr_moves = new_moves
                        closest_diamond = diamond

                    if (new_moves_via_teleport < curr_moves_via_teleport  or closest_diamond_via_teleport.properties.points + props.diamonds == 6):
                        curr_moves_via_teleport = new_moves_via_teleport
                        closest_diamond_via_teleport = diamond

            # print("No teleporter moves: ", countMoves(current_position, self.goal_position))
            # print("Teleporter moves: ", curr_moves_via_teleport)
            
            if not(return_home_flag):
                if (curr_moves_via_teleport < curr_moves and current_position != teleport_enter):
                    self.goal_position = teleport_enter
                else:
                    self.goal_position = closest_diamond.position
            else:
                if countMoves(current_position, base) < countMoves(current_position, teleport_enter) + countMoves(teleport_exit, base):
                    self.goal_position = base
                else:
                    self.goal_position = teleport_enter

        # We are aiming for a specific position, calculate delta
        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )

        return delta_x, delta_y