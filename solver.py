from typing import List
from damage_events import DamageEvents, Mitigation
import yaml
import random

def load_party_config(filename: str) -> dict:
    with open(filename, "r") as f:
        return yaml.safe_load(f)


def load_mitigations(filename: str, buffer: int) -> List[Mitigation]:
    """
    filename: YAML file containing an array of objects with the following
              fields:
                    - name
                    - actor
                    - physical_multiplier
                    - magical_multiplier
                    - duration
                    - recast
    buffer: This value assumes the mitigation will be applied N seconds before
            the damage event occurs. A value of 0 means the mitigation will be
            applied exactly when the damage event resolves.
    """
    with open(filename, "r") as f:
        mitigations = []
        for mit in yaml.safe_load(f):
            mitigation = Mitigation(mit["name"], 
                                    mit["actor"], 
                                    mit["physical_multiplier"], 
                                    mit["magical_multiplier"], 
                                    max(1, mit["duration"] - buffer),
                                    mit["recast"] - buffer)
            mitigations.append(mitigation)

        # mitigations.sort(key=lambda m: m.recast, reverse=False)
        random.shuffle(mitigations)

        return mitigations

    
if __name__ == "__main__":
    party_config = load_party_config("party_config.yaml")
    mitigations = load_mitigations("mitigation_config.yaml", party_config["buffer"])
    damage_events = DamageEvents("damage_events.yaml")

    effective_hp = party_config["max_hp"] + party_config["shield_strength"]

    iteration = 0

    while damage_events.has_lethal_damage(effective_hp):
        iteration += 1
        print("Iteration {}".format(iteration))
        # 1. Identify the event that has the most overkill damage
        max_overkill_event = damage_events.get_max_overkill_event(effective_hp)
        print("Max overkill event = {} (Time: {}, Overkill: {})".format(
            max_overkill_event.name, max_overkill_event.time, max_overkill_event.get_damage() - effective_hp))

        # 2. Identify the most effective (available) mitigation that covers that event
        # Note that the returned event_idx may not be the same index as the most damaging event
        # as we could mitigate backwards (i.e: catch the most damage event with the tail end of the mitigation)
        most_effective_event, most_effective_mit, mitigated_damage = damage_events.get_most_effective_mitigation_for_event(
            mitigations, max_overkill_event)
   
        if most_effective_mit is None:
            print("Out of mitigations - unsolvable!")
            break
        else:
            print("{} ({}) used at {} to reduce {} damage (existing mits: {})\n".format(
                most_effective_mit.name, most_effective_mit.actor, most_effective_event.name, mitigated_damage,
                ["{} ({})".format(m.name, m.actor) for m in most_effective_event.mitigations]))

            # 3. Apply that mitigation to the event (and any other events that fall
            # in the mitigation's duration)
            damage_events.apply_mitigation(most_effective_mit, most_effective_event)

        for damage_event in damage_events:
            if damage_event.get_damage() < effective_hp:
                print("  [{:3}] {:25} - Damage = {},{}Mitigations: {}".format(
                    damage_event.time, 
                    damage_event.name, 
                    damage_event.get_damage(),
                    " " * 19,
                    ["{} ({})".format(m.name, m.actor) for m in damage_event.mitigations]))
            else:
                print("* [{:3}] {:25} - Damage = {} (Overkill: {:5}), Mitigations: {}".format(
                    damage_event.time, 
                    damage_event.name, 
                    damage_event.get_damage(), 
                    damage_event.get_damage() - effective_hp,
                    ["{} ({})".format(m.name, m.actor) for m in damage_event.mitigations]))
        print("----------")
