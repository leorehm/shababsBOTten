# Beginn Deep Learning
# featureset is an input vector to the neural network and the labels will be the output layer.
# Featuresets must all be identical, and each index in each featureset must be of identical type to the next featureset's index.


# imports
#bringing in hlt to use the built-in functions, logging for logging, we want to have an ordered dictionary,
# numpy for number crunching things, random to make random choices, and os to delete some files to start fresh.
import hlt
import logging
from collections import OrderedDict
import numpy as np
import random
import os


VERSION = 1
# compute the bot against himself

HM_ENT_FEATURES = 5 # how many features per type of entity are we interested in --> have features like "open ülanets" and "enemy planets" -->  is how many to care about per feature type
PCT_CHANGE_CHANCE = 30  #what % chance to change the ships plans
DESIRED_SHIP_COUNT = 20

#basic game data
game = hlt.Game("shabab".format(VERSION))
logging.info("Shabab-{} Start".format(VERSION))
# like to keep track of plans for the ship
ship_plans = {}

#track moves and save the winner's move at the end
if os.path.exists("c{}_input.vec".format(VERSION)):
    os.remove("c{}_input.vec".format(VERSION))

if os.path.exists("c{}_out.vec".format(VERSION)):
    os.remove("c{}_out.vec".format(VERSION))

# help Functions
# grabs a dictionary's key by a value, used to grab an entity's distance
def key_by_value(dictionary, value):
    for k, v in dictionary.items():
        if v[0] == value:
            return k
    return -99

# appends to the lists of data if there aren't enough entities.
# For example, if we set HM_ENT_FEATURES to 5, this would mean we expect to have things like 5 enemy planets.
# There are going to be times when we simply don't have 5 enemy planets, so that function just pads out whatever values we do have.
def fix_data(data):
    new_list = []
    last_known_idx = 0
    for i in range(HM_ENT_FEATURES):
        try:
            if i < len(data):
                last_known_idx = i
            new_list.append(data[last_known_idx])
        except:
            new_list.append(0)

    return new_list


while True:
    game_map = game.update_map()
    command_queue = []
    #  grab how many ships we and our enemies have
    team_ships = game_map.get_me().all_ships()
    all_ships = game_map._all_ships()
    enemy_ships = [ship for ship in game_map._all_ships() if ship not in team_ships]

    my_ship_count = len(team_ships)
    enemy_ship_count = len(enemy_ships)
    all_ship_count = len(all_ships)
    # gather planet information
    my_id = game_map.get_me().id

    empty_planet_sizes = {}
    our_planet_sizes = {}
    enemy_planet_sizes = {}

    for p in game_map.all_planets():
        radius = p.radius
        if not p.is_owned():
            empty_planet_sizes[radius] = p
        elif p.owner.id == game_map.get_me().id:
            our_planet_sizes[radius] = p
        elif p.owner.id != game_map.get_me().id:
            enemy_planet_sizes[radius] = p

    hm_our_planets = len(our_planet_sizes)
    hm_empty_planets = len(empty_planet_sizes)
    hm_enemy_planets = len(enemy_planet_sizes)

    empty_planet_keys = sorted([k for k in empty_planet_sizes])[::-1]
    our_planet_keys = sorted([k for k in our_planet_sizes])[::-1]
    enemy_planet_keys = sorted([k for k in enemy_planet_sizes])[::-1]

    # Informationen die wir pro Schiff brauchen
    # we care about the closest "X" enemies to each ship, not just a random "X" enemies.
    # Same with planets, we're really interested in the closest ones, in order by distance.

    for ship in game_map.get_me().all_ships():
        try:
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                # Skip this ship ->  leave docked ships docked
                continue

            shipid = ship.id
            change = False
            if random.randint(1, 100) <= PCT_CHANGE_CHANCE: # Now we determine if we'd like to change this ship's plans, if it has any.
                change = True

#Next, we're ready to compute a bunch of features. Here are the ones I intend to track:
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))

            closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                     isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
                                     entities_by_distance[distance][0].is_owned()]
            closest_empty_planet_distances = [distance for distance in entities_by_distance if
                                              isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
                                              entities_by_distance[distance][0].is_owned()]

            closest_my_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                  isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and
                                  entities_by_distance[distance][0].is_owned() and (
                                              entities_by_distance[distance][0].owner.id == game_map.get_me().id)]
            closest_my_planets_distances = [distance for distance in entities_by_distance if
                                            isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and
                                            entities_by_distance[distance][0].is_owned() and (
                                                        entities_by_distance[distance][
                                                            0].owner.id == game_map.get_me().id)]

            closest_enemy_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                     isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and
                                     entities_by_distance[distance][0] not in closest_my_planets and
                                     entities_by_distance[distance][0] not in closest_empty_planets]
            closest_enemy_planets_distances = [distance for distance in entities_by_distance if
                                               isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and
                                               entities_by_distance[distance][0] not in closest_my_planets and
                                               entities_by_distance[distance][0] not in closest_empty_planets]

            closest_team_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                  isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and
                                  entities_by_distance[distance][0] in team_ships]
            closest_team_ships_distances = [distance for distance in entities_by_distance if
                                            isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and
                                            entities_by_distance[distance][0] in team_ships]

            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                   isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and
                                   entities_by_distance[distance][0] not in team_ships]
            closest_enemy_ships_distances = [distance for distance in entities_by_distance if
                                             isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and
                                             entities_by_distance[distance][0] not in team_ships]

            largest_empty_planet_distances = []
            largest_our_planet_distances = []
            largest_enemy_planet_distances = []

            for i in range(HM_ENT_FEATURES):
                try:
                    largest_empty_planet_distances.append(
                        key_by_value(entities_by_distance, empty_planet_sizes[empty_planet_keys[i]]))
                except:
                    largest_empty_planet_distances.append(-99)

                try:
                    largest_our_planet_distances.append(
                        key_by_value(entities_by_distance, our_planet_sizes[our_planet_keys[i]]))
                except:
                    largest_our_planet_distances.append(-99)

                try:
                    largest_enemy_planet_distances.append(
                        key_by_value(entities_by_distance, enemy_planet_sizes[enemy_planet_keys[i]]))
                except:
                    largest_enemy_planet_distances.append(-99)

            entity_lists = [fix_data(closest_empty_planet_distances),
                            fix_data(closest_my_planets_distances),
                            fix_data(closest_enemy_planets_distances),
                            fix_data(closest_team_ships_distances),
                            fix_data(closest_enemy_ships_distances),
                            fix_data(empty_planet_keys),
                            fix_data(our_planet_keys),
                            fix_data(enemy_planet_keys),
                            fix_data(largest_empty_planet_distances),
                            fix_data(largest_our_planet_distances),
                            fix_data(largest_enemy_planet_distances)]

            input_vector = []

            for i in entity_lists:
                for j in i[:HM_ENT_FEATURES]:
                    input_vector.append(j)

            input_vector += [my_ship_count,
                             enemy_ship_count,
                             hm_our_planets,
                             hm_empty_planets,
                             hm_enemy_planets]
            # sollten wir mehr Schiffe haben, als wir mindestens brauchen, sollten wir Angreifen
            # Aggressivere Variante entweder direkt 1 Schiff mehr oder doppelt so viele  Schiffe wie der Gegner?

            if my_ship_count > DESIRED_SHIP_COUNT:
                '''ATTACK: [1,0,0]'''

                output_vector = 3 * [0]  # [0,0,0]
                output_vector[0] = 1  # [1,0,0]
                ship_plans[ship.id] = output_vector

            elif change or ship.id not in ship_plans:
                '''
                pick new "plan"
                '''
                output_vector = 3 * [0]
                output_vector[random.randint(0, 2)] = 1
                ship_plans[ship.id] = output_vector

            else:
                '''continue to execute existing plan'''
                output_vector = ship_plans[ship.id]

            try:

                # ATTACK ENEMY SHIP #
                if np.argmax(output_vector) == 0:  # [1,0,0]
                    '''
                    type: 0
                    Find closest enemy ship, and attack!
                    '''
                    if not isinstance(closest_enemy_ships[0], int):
                        navigate_command = ship.navigate(
                            ship.closest_point_to(closest_enemy_ships[0]),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)



                # MINE ONE OF OUR PLANETS #
                elif np.argmax(output_vector) == 1:
                    '''
                    type: 1
                    Mine closest already-owned planet
                    '''
                    if not isinstance(closest_my_planets[0], int):
                        target = closest_my_planets[0]

                        if len(target._docked_ship_ids) < target.num_docking_spots:
                            if ship.can_dock(target):
                                command_queue.append(ship.dock(target))
                            else:
                                navigate_command = ship.navigate(
                                    ship.closest_point_to(target),
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                                if navigate_command:
                                    command_queue.append(navigate_command)
                        else:
                            # attack!
                            if not isinstance(closest_enemy_ships[0], int):
                                navigate_command = ship.navigate(
                                    ship.closest_point_to(closest_enemy_ships[0]),
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                                if navigate_command:
                                    command_queue.append(navigate_command)



                    elif not isinstance(closest_empty_planets[0], int):
                        target = closest_empty_planets[0]
                        if ship.can_dock(target):
                            command_queue.append(ship.dock(target))
                        else:
                            navigate_command = ship.navigate(
                                ship.closest_point_to(target),
                                game_map,
                                speed=int(hlt.constants.MAX_SPEED),
                                ignore_ships=False)

                            if navigate_command:
                                command_queue.append(navigate_command)

                    # attack!
                    elif not isinstance(closest_enemy_ships[0], int):
                        navigate_command = ship.navigate(
                            ship.closest_point_to(closest_enemy_ships[0]),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)




                # FIND AND MINE AN EMPTY PLANET #
                elif np.argmax(output_vector) == 2:
                    '''
                    type: 2
                    Mine an empty planet. 
                    '''
                    if not isinstance(closest_empty_planets[0], int):
                        target = closest_empty_planets[0]

                        if ship.can_dock(target):
                            command_queue.append(ship.dock(target))
                        else:
                            navigate_command = ship.navigate(
                                ship.closest_point_to(target),
                                game_map,
                                speed=int(hlt.constants.MAX_SPEED),
                                ignore_ships=False)

                            if navigate_command:
                                command_queue.append(navigate_command)

                    else:
                        # attack!
                        if not isinstance(closest_enemy_ships[0], int):
                            navigate_command = ship.navigate(
                                ship.closest_point_to(closest_enemy_ships[0]),
                                game_map,
                                speed=int(hlt.constants.MAX_SPEED),
                                ignore_ships=False)

                            if navigate_command:
                                command_queue.append(navigate_command)
# We try to find an empty planet. If there are none, we attack!


#  closes off the trys, saves the moves, and sends game commands
            except Exception as e:
                logging.info(str(e))

            with open("c{}_input.vec".format(VERSION), "a") as f:
                f.write(str([round(item, 3) for item in input_vector]))
                f.write('\n')

            with open("c{}_out.vec".format(VERSION), "a") as f:
                f.write(str(output_vector))
                f.write('\n')

        except Exception as e:
            logging.info(str(e))

    game.send_command_queue(command_queue)
    # TURN END
# GAME END

# inspired by https://pythonprogramming.net/deep-learning-halite-ii-artificial-intelligence-competition/