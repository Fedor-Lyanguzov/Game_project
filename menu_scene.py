from pyglet.event import EventDispatcher


from cocos import layer
from cocos.text import RichLabel

from util import util_starting_stats
from cocos.director import director
from main_scene import MainScene

class FirstLayer(layer.Layer, EventDispatcher):
    is_event_handler = True
    def __init__(self):
        layer.Layer.__init__(self)
        EventDispatcher.__init__(self)

        self.start_button = RichLabel('Click on a race to choose it')

        self.race_selection_dict = {'Human': (util_starting_stats.Human, 'image'),
                                  'Drwarf': (util_starting_stats.Dwarf, 'image'),
                                    'Elf': (util_starting_stats.Elf, 'image'),
                                    'Orc': (util_starting_stats.Orc, 'image'),
                                    'Goblin': (util_starting_stats.Goblin, 'image'),
                                    'Demon': (util_starting_stats.Demon, 'image'),
                                    'Vampire': (util_starting_stats.Vampire, 'image'),
                                    'Ghost': (util_starting_stats.Ghost, 'image')}
        button_y = 750
        for race_name, race in self.race_selection_dict.items():
            button = RichLabel(race_name, position=(1000, button_y), font_size=20)
            button_y -= 100
            self.add(button)

    def on_mouse_motion(self,x,y,dx,dy):
        #print(x,y)
        pass
        
    def on_mouse_press(self,x,y,buttons,modifiers):#on_mouse_press does not work
        print(666)                                 #for some reason
        button_y = 750
        for button in self.race_selection_dict:
            if 1000<x<1250 and button_y-20<y<button_y+20:
                print(9867889687668)
                chosen_race = self.race_selection_dict[button][0]
                print(chosen_race)
                director.push(MainScene(chosen_race = chosen_race))
            button_y -= 100
                                  # later needs to be changed so the player and inventory_layer stay,
                                  #and the mobs and and the map get added to a database







