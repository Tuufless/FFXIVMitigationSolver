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
        
class DamageEvents(object):
    """
    This class encapsulates a list of DamageEvents, and provides some useful
    utility functions that operate on the collection.
    """
    def __init__(self, filename):
        self.damage_events = []
        with open(filename, "r") as f:
            for event_info in yaml.safe_load(f):
                damage_event = DamageEvent(event_info["name"], 
                                           event_info["time"], 
                                           event_info["damage"], 
                                           DamageType.UNIQUE)
            
                if event_info["damage_type"] == "physical":
                    damage_event.damage_type = DamageType.PHYSICAL
                elif event_info["damage_type"] == "magical":
                    damage_event.damage_type = DamageType.MAGICAL

                self.damage_events.append(damage_event)

    def __iter__(self):
        return self.damage_events.__iter__()
    
    def __next__(self):
        return self.damage_events.__next__()

    def has_lethal_damage(self, effective_hp: int) -> bool:
        """
        Returns true if any damage event is lethal.
        """
        for event in self.damage_events:
            if event.get_damage() >= effective_hp:
                return True
        return False

    def get_most_effective_mitigation_for_event(self, 
                                                mitigations: List[Mitigation], 
                                                damage_event: DamageEvent) -> tuple[DamageEvent, Mitigation, int]:
        """
        Identify the starting damage event and mitigation that would reduce the
        most damage for a specified damage event.

        Note that this may mean that the mitigation should be used at an earlier damage event
        if it will also cover the specified event.

        Returns a tuple containing:
            - The damage event the mitigation should be applied on (but will still mitigate the input damage_event)
            - The mitigation that should be used
            - The total amount of damage mitigated as a result
        """
        best_mitigation = None
        best_mitigated_event = None
        best_mitigation_score = -9999

        for mitigation in mitigations:
            # check to see if the mitigation is on cooldown
            if not self.mitigation_available_for_event(damage_event, mitigation):
                continue

            # Consider all events that would also mitigate the specified damage event
            for event in self.damage_events:
                if (event.time <= damage_event.time - mitigation.duration or event.time > damage_event.time):
                    continue

                mitigated_damage = self.get_mitigated_damage(mitigation, event)
                if mitigated_damage > 0 and mitigated_damage > best_mitigation_score:
                    best_mitigation_score = mitigated_damage
                    best_mitigation = mitigation
                    best_mitigated_event = event

        return best_mitigated_event, best_mitigation, best_mitigation_score

    def get_mitigated_damage(self, 
                             mitigation: Mitigation, 
                             damage_event: DamageEvent) -> int:
        """
        Calculates the damage mitigated assuming the mitigation is used at the
        specified damage event.

        Returns the total damage mitigated.
        """
        total_damage_reduced = 0

        for event in self.damage_events:
            if damage_event.time <= event.time and event.time < damage_event.time + mitigation.duration:
                total_damage_reduced += self.score_mitigation(mitigation, event)

        return total_damage_reduced

    def score_mitigation(self, mitigation: Mitigation, damage_event: DamageEvent) -> int:
        """
        Returns the total damage reduced if the mitigation was used at the 
        provided damage event.
        """
        total_damage_reduced = 0
        for event in self.damage_events:
            if (event.time >= damage_event.time and event.time < damage_event.time + mitigation.duration):
                total_damage_reduced += event.apply_mitigation(mitigation)

        return total_damage_reduced
    
    def get_max_overkill_event(self, effective_hp: int) -> Optional[DamageEvent]:
        max_overkill_damage = None
        max_overkill_event = None

        for event in self.damage_events:
            # identify the event that has the most overkill damage
            overkill_damage = event.get_damage() - effective_hp
            if max_overkill_damage is None or (overkill_damage >= 0 and overkill_damage > max_overkill_damage):
                max_overkill_damage = overkill_damage
                max_overkill_event = event

        return max_overkill_event
    
    def apply_mitigation(self, mitigation: Mitigation, damage_event: DamageEvent) -> None:
        """
        Applies a mitigation to the specified event, and any other events that
        fall within the mitigation's duration.
        """
        mitigation.used_times.append(damage_event.time)
        for event in self.damage_events:
            if event.time >= damage_event.time and event.time < damage_event.time + mitigation.duration:
                event.mitigations.append(mitigation)

    @staticmethod
    def mitigation_available_for_event(damage_event: DamageEvent, mitigation: Mitigation) -> bool:
        for used_time in mitigation.used_times:
            if abs(damage_event.time - used_time) < mitigation.recast:
                return False
        return True
