from enum import Enum
from typing import List, Optional
import yaml

class DamageType(Enum):
    PHYSICAL = 0
    MAGICAL = 1
    UNIQUE = 2

class Mitigation(object):
    def __init__(self, name: str, actor: str, physical_multiplier: int, 
                 magical_multiplier: int, duration: int, recast: int):
        self.name = name
        self.actor = actor
        self.physical_multiplier = physical_multiplier
        self.magical_multiplier = magical_multiplier
        self.duration = duration
        self.recast = recast
        self.used_times = []

class DamageEvent(object):
    def __init__(self, name: str, time: int, damage: int, 
                 damage_type: DamageType):
        self.name = name
        self.time = time
        self.damage = damage
        self.damage_type = damage_type
        self.mitigations = []

    def get_damage(self) -> int:
        """
        Returns the amount of damage (after mitigations)
        """
        damage = self.damage
        for mitigation in self.mitigations:
            if self.damage_type is DamageType.PHYSICAL:
                mitigated_damage = int(damage * (1.0 - mitigation.physical_multiplier))
                damage -= mitigated_damage
            elif self.damage_type is DamageType.MAGICAL:
                mitigated_damage = int(damage * (1.0 - mitigation.magical_multiplier))
                damage -= mitigated_damage
        return damage

    def apply_mitigation(self, mitigation) -> int:
        """
        Returns the amount of damage if the provided mitigation were to be
        applied (on top of any existing mitigations on the damage event).
        """
        for m in self.mitigations:
            if m.name == mitigation.name:
                # no extra damage mitigated with duplicate mits
                return 0

        if self.damage_type is DamageType.PHYSICAL:
            return int(self.get_damage() * (1.0 - mitigation.physical_multiplier))
        elif self.damage_type is DamageType.MAGICAL:
            return int(self.get_damage() * (1.0 - mitigation.magical_multiplier))
        else:
            return 0


def load_party_config(filename: str) -> dict:
    with open(filename, "r") as f:
        return yaml.safe_load(f)
    

def load_damage_events(filename: str) -> List[DamageEvent]:
    with open(filename, "r") as f:
        events = []
        for event in yaml.safe_load(f):
            ev = DamageEvent(event["name"],
                             event["time"],
                             event["damage"],
                             DamageType.UNIQUE)
            
            if event["damage_type"] == "physical":
                ev.damage_type = DamageType.PHYSICAL
            elif event["damage_type"] == "magical":
                ev.damage_type = DamageType.MAGICAL

            events.append(ev)

        return events

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
    buffer: This value shortens the mitigation durations. This essentially
            models how accurate players must be when using the mitigation.
            A buffer of 0 means the mitigation will be applied exactly when
            the damage event resolves.
    """
    with open(filename, "r") as f:
        mitigations = []
        for mit in yaml.safe_load(f):
            mitigation = Mitigation(mit["name"], 
                                    mit["actor"], 
                                    mit["physical_multiplier"], 
                                    mit["magical_multiplier"], 
                                    max(1, mit["duration"] - buffer),
                                    mit["recast"])
            mitigations.append(mitigation)

        mitigations.sort(key=lambda m: m.recast, reverse=False)
        return mitigations
    
def score_mitigation(mitigation: Mitigation, damage_event: DamageEvent, damage_events: List[DamageEvent]) -> int:
    """
    Returns the total damage reduced if the mitigation was used at the damage
    event at the provided index.
    """
    total_damage_reduced = 0
    for event in damage_events:
        if (event.time >= damage_event.time and event.time < damage_event.time + mitigation.duration):
            total_damage_reduced += event.apply_mitigation(mitigation)

    return total_damage_reduced

def get_max_overkill_event(effective_hp: int, damage_events: List[DamageEvent]) -> Optional[DamageEvent]:
    max_overkill_damage = None
    max_overkill_event = None

    for event in damage_events:
        # identify the event that has the most overkill damage
        overkill_damage = event.get_damage() - effective_hp
        if max_overkill_damage is None or (overkill_damage >= 0 and overkill_damage > max_overkill_damage):
            max_overkill_damage = overkill_damage
            max_overkill_event = event

    return max_overkill_event

    
def get_mitigated_damage(mitigation: Mitigation, damage_event: DamageEvent, 
                         damage_events: List[DamageEvent]) -> int:
    """
    Calculates the damage mitigated assuming the mitigation is used at the
    specified starting damage event index."""
    total_damage_reduced = 0

    for event in damage_events:
        if damage_event.time <= event.time and event.time < damage_event.time + mitigation.duration:
            total_damage_reduced += score_mitigation(mitigation, event, damage_events)

    return total_damage_reduced


def mitigation_available_for_event(damage_event: DamageEvent, mitigation: Mitigation) -> bool:
    for used_time in mitigation.used_times:
        if abs(damage_event.time - used_time) < mitigation.recast:
            return False
    return True


def get_most_effective_mitigation_for_event(mitigations: List[Mitigation], damage_event: DamageEvent,
                                            damage_events: List[DamageEvent]) -> tuple[DamageEvent, Mitigation, int]:
    """
    Identify the starting damage event and mitigation that would reduce the
    most damage for a specified damage event.

    Note that this may mean that the mitigation should be used at an earlier damage event
    if it will also cover the specified event.
    """
    best_mitigation = None
    best_mitigated_event = None
    best_mitigation_score = -9999

    for mitigation in mitigations:
        # check to see if the mitigation is on cooldown
        if not mitigation_available_for_event(damage_event, mitigation):
            continue

        # Consider all events that would also mitigate the specified damage event
        for event in damage_events:
            if (event.time <= damage_event.time - mitigation.duration or event.time > damage_event.time):
                continue

            mitigated_damage = get_mitigated_damage(mitigation, event, damage_events)
            if mitigated_damage > 0 and mitigated_damage > best_mitigation_score:
                best_mitigation_score = mitigated_damage
                best_mitigation = mitigation
                best_mitigated_event = event

    return best_mitigated_event, best_mitigation, best_mitigation_score

def is_lethal_damage(damage_events: List[DamageEvent], effective_hp: int) -> bool:
    for event in damage_events:
        if event.get_damage() >= effective_hp:
            return True
    return False
    
if __name__ == "__main__":
    party_config = load_party_config("party_config.yaml")
    mitigations = load_mitigations("mitigation_config.yaml", party_config["buffer"])
    damage_events = load_damage_events("damage_events.yaml")

    effective_hp = party_config["max_hp"] + party_config["shield_strength"]

    while is_lethal_damage(damage_events, effective_hp):
        # 1. Identify the event that has the most overkill damage
        max_overkill_event = get_max_overkill_event(effective_hp, damage_events)
        print("Max overkill event = {} (Overkill: {}, Time: {})".format(
            max_overkill_event.name, max_overkill_event.get_damage() - effective_hp, max_overkill_event.time))

        # 2. Identify the most effective (available) mitigation that covers that event
        # Note that the returned event_idx may not be the same index as the most damaging event
        # as we could mitigate backwards (i.e: catch the most damage event with the tail end of the mitigation)
        damage_event, most_effective_mit, mitigated_damage = get_most_effective_mitigation_for_event(
            mitigations, max_overkill_event, damage_events)
   
        if most_effective_mit is None:
            print("Out of mitigations - unsolvable!")
            break
        else:
            print("Most effective mit = {} ({}) used at {} to reduce {} damage (existing mits: {})\n".format(
                most_effective_mit.name, most_effective_mit.actor, damage_event.name, mitigated_damage,
                ["{} ({})".format(m.name, m.actor) for m in damage_event.mitigations]))

            # 3. Apply that mitigation to the event (and any other events that fall
            # in the mitigation's duration)
            most_effective_mit.used_times.append(damage_event.time)
            for ev in damage_events:
                if ev.time >= damage_event.time and ev.time < damage_event.time + most_effective_mit.duration:
                    ev.mitigations.append(most_effective_mit)

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
