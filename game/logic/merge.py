import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

def countMoves(pos1: Position, pos2: Position):
    return abs(pos1.x-pos2.x) + abs(pos1.y-pos2.y)

class Merge(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None

    def weghtcalcTel(self,curpos:Position,diampos:Position,weight,posbase:Position, closTelPos:Position, farTelPos:Position,
                     closTelDiam:Position,farTelDiam:Position):
        distd = countMoves(curpos,closTelPos) + countMoves(farTelPos,diampos)
        distb = countMoves(diampos,closTelDiam) + countMoves(farTelDiam,posbase)
        if (distd==0 or distb==0):
            return 0
        else:
            return float(weight/(distd*(distb**(1/2))))
    
    def weghtcalc(self,curpos:Position,diampos:Position,weight,posbase:Position):
        distd = countMoves(curpos,diampos)
        distb = countMoves(diampos,posbase)
        if (distd==0 or distb==0):
            return 0
        else:    
            return float(weight/(distd*(distb**(1/2))))
    
    def next_move(self, board_bot: GameObject, board: Board):
        
        # bot props

        props = board_bot.properties
        # positions
        current_position = board_bot.position
        base = board_bot.properties.base

        # Ketika sudah berada di base dan masih tersisa waktu, goal position akan di assign ke (7,7) tengah map
        if (current_position.x==base.x and current_position.y==base.y and (board_bot.properties.milliseconds_left/1000)<= 1.5):
            print("Sudah di base")
            if (base.x!=7 and base.y !=7):
                self.goal_position.x = 7
                self.goal_position.y = 7
            else:
                self.goal_position.x = 6
                self.goal_position.y = 6
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
            return delta_x,delta_y
        else:
            # teleporters
            teleporters = [d for d in board.game_objects if d.type == "TeleportGameObject"]

            teleporter0_moves = countMoves(current_position, teleporters[0].position)
            teleporter1_moves = countMoves(current_position, teleporters[1].position)

            #Mencari teleport terdekat dari bot
            if (teleporter0_moves < teleporter1_moves):
                teleport_enter = teleporters[0].position
                teleport_exit = teleporters[1].position

                moves_to_teleporter = teleporter0_moves
            else:
                teleport_enter = teleporters[1].position
                teleport_exit = teleporters[0].position

                moves_to_teleporter = teleporter1_moves

            #waktu yang tersisa
            
            remain_time = board_bot.properties.milliseconds_left/1000
            print(remain_time," s")
            print(countMoves(current_position,base))
            # Jika diamond sudah full atau waktu yang tersisa tinggal sedikit -> balik, ditambah jeda 2 detik untuk antisipasi
            if (props.diamonds == 5 or (((remain_time-2) <= countMoves(current_position, base))
                                        and ((remain_time-2 ) <= countMoves(teleport_enter,current_position) + countMoves(teleport_exit,base)))):
                #jika belum di base
                if (current_position != base):
                    #Mencari rute terdekat (lewat teleporter atau jalan kaki)
                    if countMoves(current_position, base) > countMoves(current_position, teleport_enter) + countMoves(teleport_exit, base) and current_position != teleport_enter:
                        self.goal_position = teleport_enter
                    else:
                        self.goal_position = base

                #jika sedang di base, target diubah ke titik tengah (agar tidak diam di base)
                else:
                    if (base.x!=7 and base.y !=7):
                        self.goal_position.x = 7
                        self.goal_position.y = 7
                    else:
                        self.goal_position.x = 6
                        self.goal_position.y = 6

            else:
                # Mencar diamond terdekat, greed by weight/distance yang dikalkulasi pada 
                # fungsi : weghtcalc (distance diukur dengan jalan kaki) dan weghtcalcTel (distance diukur dengan lewat teleporter)
                # Lalu dibandingkan mana yang lebih besar pada setiap diamond

                diamonds = board.diamonds

                # Inisasi variabel
                closest_diamond = diamonds[0]
                closest_diamond_via_teleport = diamonds[0]

                curr_moves = countMoves(current_position, closest_diamond.position)
                curr_moves_via_teleport = moves_to_teleporter + countMoves(teleport_exit, closest_diamond_via_teleport.position)

                # Iterasi
                for diamond in diamonds:

                    #kondisi ketika ada diamond merah tetapi diamond yang didapat sudah 4
                    if diamond.properties.points + props.diamonds == 6:
                        # menuju base (pulang)
                        return_home_flag = True

                    else:
                        # cek teleporter terdekat dari diamond
                        if (countMoves(teleporters[0].position,diamond.position) > countMoves(teleporters[1].position,diamond.position)):
                            teleporter_diamond_closest = teleporters[1].position
                            teleporter_diamond_farest = teleporters[0].position
                        else:
                            teleporter_diamond_closest = teleporters[0].position
                            teleporter_diamond_farest = teleporters[1].position

                        return_home_flag = False

                        # weight = point diamond
                        weight = diamond.properties.points
                        maxw = closest_diamond.properties.points
                        # jumlah step move baru
                        new_moves = countMoves(current_position, diamond.position)
                        new_moves_via_teleport = moves_to_teleporter + countMoves(teleport_exit, diamond.position)
                        
                        #Kalkulasi Skor greed jika jalan kaki 
                        greedWalkMax = self.weghtcalc(current_position,closest_diamond.position,maxw,base)
                        greedWalkNext = self.weghtcalc(current_position,diamond.position,weight,base)
                        # Komparasi dan simpan
                        if (greedWalkNext > greedWalkMax
                            or closest_diamond.properties.points + props.diamonds == 6):
                            curr_moves = new_moves
                            closest_diamond = diamond
                        
                        # Kalkulasi Skor greed jika pakai teleporter
                        greedTelMax = self.weghtcalcTel(current_position,diamond.position,maxw,base,teleport_enter,teleport_exit,teleporter_diamond_closest,teleporter_diamond_farest)
                        greedTelNext = self.weghtcalcTel(current_position,diamond.position,weight,base,teleport_enter,teleport_exit,teleporter_diamond_closest,teleporter_diamond_farest)
                        #Komparasi dan simpan
                        if ( (greedTelNext < greedTelMax)  or closest_diamond_via_teleport.properties.points + props.diamonds == 6):
                            curr_moves_via_teleport = new_moves_via_teleport
                            closest_diamond_via_teleport = diamond

                # jika tidak ingin pulang
                if not(return_home_flag):
                    if ((countMoves(current_position,teleport_enter)+countMoves(teleport_exit,closest_diamond_via_teleport.position)) < countMoves(current_position,closest_diamond.position) and current_position != teleport_enter):
                        print("Go via teleport")
                        self.goal_position = teleport_enter
                    else:
                        print("Go via diamond")
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
        # 
        if (delta_x !=0):
            if ((current_position.x + delta_x == teleport_enter.x) and (current_position.y == teleport_enter.y) and (self.goal_position.y - current_position.y)!=0 ):
                delta_x = 0
                delta_y = (self.goal_position.y - current_position.y) / abs(self.goal_position.y - current_position.y)
        print(self.goal_position)
        print("Curr: ")
        print(current_position)
        
        return delta_x, delta_y