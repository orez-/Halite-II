"""
Welcome to your first Halite-II bot!

Note: Please do not place print statements here as they are used to
communicate with the Halite engine. If you need to log anything use the
logging module.
"""
import collections
import itertools
import logging

import hlt

# GAME START
game = hlt.Game("Orez[Scout]")
logging.info("Starting scout bot!")


def distance2(entity1, entity2):
    return (entity2.x - entity1.x) ** 2 + (entity2.y - entity1.y) ** 2


def get_closest_planets(ship, planets):
    return sorted(
        (
            planet for planet in planets
            if planet != ship
        ),
        key=lambda planet: distance2(ship, planet)
    )


def main():
    attackers = {}
    for i in itertools.count(1):
        # TURN START
        # Update the map for the new turn and get the latest version
        game_map = game.update_map()

        command_queue = collections.deque()
        # commands = {}
        # added_in = {}

        ships_to_move = {}

        me = game_map.get_me()
        attackers = {
            ship: planet
            for ship, planet in (
                (me.get_ship(ship.id), game_map.get_planet(planet.id))
                for ship, planet in attackers.items()
            )
            if ship and planet and planet.owner_id != game_map.my_id
        }

        dockable_planets = [
            planet for planet in game_map.all_planets()
            if planet.owner_id != game_map.my_id or planet.remaining_resources
        ]
        for ship in me.all_ships():
            # If the ship is docked
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                continue
            if ship in attackers:
                planet = attackers[ship]
                if ship.can_dock(planet) or planet.owner_id == game_map.my_id:
                    del attackers[ship]
                else:
                    continue
            ships_to_move[ship] = get_closest_planets(ship, dockable_planets)

        taken_planets = set()
        idlers_by_planet = collections.defaultdict(set)
        for ship, planets in ships_to_move.items():
            for planet in planets:
                if planet not in taken_planets and planet.remaining_resources:
                    break
            else:
                idlers_by_planet[planets[0]].add(ship)
                continue

            taken_planets.add(planet)
            if ship.can_dock(planet):
                command_queue.append(ship.dock(planet))
                # commands[ship] = ship.dock(planet)
                # added_in[ship] = 'dock'
            else:
                navigate_command = ship.navigate(
                    ship.closest_point_to(planet),
                    game_map,
                    speed=hlt.constants.MAX_SPEED,
                    ignore_ships=False,
                )
                if navigate_command:
                    command_queue.append(navigate_command)
                    # commands[ship] = navigate_command
                    # if ship in added_in:
                    #     raise Exception(added_in[ship])
                    # added_in[ship] = 'to-move'

        # divvy up strike forces
        for origin, idlers in idlers_by_planet.items():
            for destination in get_closest_planets(origin, game_map.all_planets()):
                if destination.owner_id != game_map.my_id:
                    logging.info(
                        "Shipping off %s %s units from %s to %s %s on turn %s",
                        len(idlers),
                        game_map.my_id,
                        origin,
                        destination.owner_id,
                        destination,
                        i,
                    )
                    for idler in idlers:
                        attackers[idler] = destination

        for attacker, planet in attackers.items():
            navigate_command = attacker.navigate(
                attacker.closest_point_to(planet),
                game_map,
                speed=hlt.constants.MAX_SPEED,
                ignore_ships=False,
            )
            if navigate_command:
                # commands[attacker] = navigate_command
                # if attacker in added_in:
                #     raise Exception(added_in[attacker])
                # added_in[attacker] = 'attacker'
                command_queue.append(navigate_command)


        game.send_command_queue(command_queue)
        # game.send_command_queue(commands.values())


if __name__ == '__main__':
    main()
