from pyglet.window.key import symbol_string
from pyglet.event import EventDispatcher

from cocos import layer, scene
from cocos.director import director
from cocos.actions import MoveBy, MoveTo, CallFunc, RotateBy
from cocos.sprite import Sprite

from random import randrange
from functools import partial
import math

from pathfinding import pathfind_to_target
from database_ideas import move_level_to_database
from observer_class import Observer

from visibility import calculate_visibility
import starting_stats
from create_character import Player
from map_generation import LevelMap
from interract_layer import InteractableLayer
from effect_layer import EffectLayer
from visibility_layer import VisibilityLayer
from inventories import InventoryLayer
from equiped_layer import EquipedLayer
from create_monster import Monster
import items



class PlayingLayer(layer.Layer, EventDispatcher, Observer):
    is_event_handler = True

    def __init__(self, player1, map_layer, subj1 = False, subj2 = False):
        layer.Layer.__init__(self)
        EventDispatcher.__init__(self)
        Observer.__init__(self, subject1 = subj1, subject2 = subj2)

        self.handling_moves = True
        self.inv_open = False

        self.map_layer = map_layer
        self.interactive_layer = False
        self.effect_layer = False

        self.player = player1
        self.add(self.player)
        self.player.current_map = self.map_layer.map

        self.mobs = []

        self.this_turn = self.player.turn


        #FOR TESTS: infinite health
        #self.player.health = math.inf

    def spawn_items(self):
        self.dispatch_event('generate_items_open_area')
        #TO DO: MAKE IT SPAWN ITEMS DIFFERENTLY WITH EACH TYPE OF LEVEL


    def spawn_initial_mobs(self):#+ initial visibility

        i_p = self.player.tile()['i'] + len(self.map_layer.map)
        j_p = self.player.tile()['j']
        vis_map = calculate_visibility(i_p, j_p, self.map_layer)
        self.dispatch_event('draw_player_vision',vis_map)

        max_mobs = self.map_layer.level + 2
        amount_mobs = 0
        for i in range(0,len(self.map_layer.map)):
            for j in range(0,len(self.map_layer.map[0])):
                if self.map_layer[i][j] == 0 and randrange(100)>96 and\
                   len(self.mobs) < max_mobs and \
                   self.player.tile()['j'] != j and \
                   self.player.tile()['i'] + len(self.map_layer.map) != i:
                    amount_mobs += 1
                    mob = Monster(starting_stats.Gnoll_hunter.monster_sprite,
                                  starting_stats.Gnoll_hunter,
                                  self.map_layer.level)
                    self.mobs.append(mob)
                    mob.position = (j+1)*50, (len(self.map_layer.map)-i)*50
                    self.add(mob)
        #for m in range(0,len(self.mobs)-1):
         #   self.mobs[m+1].new_observer_init(subj2 = self.mobs[m])

    def check_tile_for_mob(self,j,i):
        result = [False]
        for mob in self.mobs:
            if mob.tile()['j'] == j and \
               mob.tile()['i'] + len(self.map_layer.map) == i:
                result = [True, mob]
        return result

    def move(self, d1, d2):#NOT CURRENTLY USED
        self.player.direction = (d1, d2)
        for child in self.get_children():
            child.move()
        self.player.move()

    def check_passability(self,x1,y1):
        result = False
        i = self.player.tile()['i'] + len(self.map_layer.map) - y1
        j = self.player.tile()['j'] + x1
        a_mob_here = self.check_tile_for_mob(j,i)[0]
        if self.map_layer[i][j] == 0 and not a_mob_here:
            result = True
        return result

    def do_after_turn(self):
        self.handling_moves = False

        i_p = self.player.tile()['i'] + len(self.map_layer.map)
        j_p = self.player.tile()['j']
        vis_map = calculate_visibility(i_p, j_p, self.map_layer)
        self.dispatch_event('draw_player_vision', vis_map)

        print('turn:',self.player.turn)
        print('health:',self.player.health)
        for mob in self.mobs:   
            if mob.check_for_death(self.player):
                self.remove(mob)
                self.mobs.remove(mob)
                print('You killed the',mob.name,'!')

        if self.mobs == []:
            self.handling_moves = True
        if self.mobs != []:
            self.mobs[0].move_if_close_range()

        if self.player.check_for_death() == True:
            self.remove(self.player)
            self.handling_moves = False
            print('You died!')#for now
        if self.mobs == []:
            print('You win!')#for now
        self.this_turn += 1

    def player_do_turn(self, x, y):
        player1.current_map = map_layer.map
        self.player.direction = x,y
        mob_tile = self.check_tile_for_mob(self.player.tile()['j'] + x,
                                           self.player.tile()['i'] - y + len(self.map_layer.map))
        self.player.move_if_possible()
        # hit if there is a mob
        if  mob_tile[0]:
            mob = mob_tile[1]
            print('You hit the', mob.name, '!')
            self.player.close_range_attack(mob)
            x1, y1 = mob.position
            self.effect_layer.normal_strike(x1, y1, True)
            self.player.check_moves()
            if self.this_turn == self.player.turn - 1:
                self.do_after_turn()
            #TO DO: MAKE IT SO THST THIS IS DONE WITHIN THE PLAYER

    def on_key_press(self, key, modifiers):#move with keys
        buttons = {'D':(1,0), 'E':(1,1), 'W':(0,1), 'Q':(-1,1),
                   'A':(-1,0), 'Z':(-1,-1), 'X':(0,-1), 'C':(1,-1)}
        print(self.handling_moves)
        if self.handling_moves and self.this_turn == self.player.turn:
            if symbol_string(key) in buttons and self.handling_moves:
                x,y = buttons[symbol_string(key)]
                self.player.direction = x, y
                self.player_do_turn(x,y)

        if symbol_string(key) == 'I':#switch to inventory
            if not self.inv_open:
                self.inv_open = True
                self.handling_moves = False
                self.parent.add(self.player.inventory, z = 5)
                inventory_layer.handling_events = True
            elif self.inv_open:
                self.inv_open = False
                self.handling_moves = True
                self.parent.remove(self.player.inventory)

        if symbol_string(key) == 'P' and self.handling_moves:#pick up item
            for item in self.interactive_layer.items:
                print(item.tile)
                print(len(self.map_layer.map) + self.player.tile()['i'],
                                  self.player.tile()['j'])
                if item.tile == ( len(self.map_layer.map) + self.player.tile()['i'],
                                  self.player.tile()['j'] ):
                    if self.player.inventory.add_to_inventory(item):
                        self.interactive_layer.items.remove(item)
                        self.interactive_layer.remove(item)
                        self.do_after_turn()
                        self.player.turn += 1
        #__________________________#TEMPORARY
        if symbol_string(key) == 'S':#TEMPORARY
            fireball = Sprite('Sprites/Effect_Blue_Fireball.png')
            fireball.scale = 0.05
            x,y = self.player.race_sprite.position
            fireball.position = x,y
            effect_layer.add(fireball)
            fireball.do(RotateBy(90,0)+MoveBy((600,0),3))
        #___________________________#TEMPORARY

PlayingLayer.register_event_type('generate_items_open_area')
PlayingLayer.register_event_type('draw_player_vision')


if __name__=="__main__":
    director.init(width=1250, height=800, autoscale=True, resizable=True)
    player1 = Player(starting_stats.Human,starting_stats.Warlock)
                
    map_layer = LevelMap(1, subject1 = player1)
    map_layer.generate_map()
    play_layer = PlayingLayer(player1, map_layer, subj1 = player1)
    interactive_layer = InteractableLayer(map_layer, subj1=player1, subj2=play_layer)
    effect_layer = EffectLayer(map_layer)
    visibility_layer = VisibilityLayer(map_layer, subj1 = play_layer, subj2 = player1)
    equip_layer = EquipedLayer()
    inventory_layer = InventoryLayer(play_layer, interactive_layer, equip_layer)

    player1.equip_layer = equip_layer
    play_layer.effect_layer = effect_layer
    play_layer.player.inventory = inventory_layer
    play_layer.interactive_layer = interactive_layer
    play_layer.spawn_initial_mobs()
    play_layer.spawn_items()

    main_scene = scene.Scene()
    main_scene.add(map_layer, z = 0)
    main_scene.add(interactive_layer, z = 1)
    main_scene.add(play_layer, z = 2)
    main_scene.add(effect_layer, z = 3)
    main_scene.add(visibility_layer, z = 4)
    main_scene.add(equip_layer, z = 6)

    director.show_FPS = True

    import profile
    #profile.run('director.run(main_scene)', sort='cumtime')

    director.run(main_scene)

