# FFXIVMitigationSolver

This script was initially written to try and solve for a mitigation plan for
the final phase of The Omega Protocol (Ultimate).

Usage:
```
python solver.py > output.txt
```

This is still a work in progress. The mitigations are randomly shuffled each
execution. So far, the closest solution found looks like the following:
```
Effective HP = 76200 (68000 HP + 8200 shield)

  [  0] Cosmo Memory              - Damage = 71641,                   Mitigations: ['Reprisal (ST)']
  [ 30] Cosmo Dive 1              - Damage = 75453,                   Mitigations: ['Reprisal (MT)', 'Addle (D4)', 'ST 90s (ST)']
  [ 68] Wave Cannon 1 (spread)    - Damage = 67069,                   Mitigations: ['H2 120s (H2)', 'H2 30s (H2)', 'Tactician (D3)']
  [ 76] Wave Cannon 1 (stack)     - Damage = 73240,                   Mitigations: ['H2 120s (H2)', 'H2 30s (H2)', 'Tactician (D3)', 'Reprisal (ST)', 'Feint (D2)']
  [101] Wave Cannon 2 (spread)    - Damage = 74521,                   Mitigations: ['H1 120s (H1)', 'H2 30s (H2)']
  [110] Wave Cannon 2 (stack)     - Damage = 73240,                   Mitigations: ['H1 120s (H1)', 'H2 30s (H2)', 'Reprisal (MT)', 'MT 90s (MT)', 'Feint (D1)']
  [144] Cosmo Dive 2              - Damage = 75453,                   Mitigations: ['Addle (D4)', 'ST 90s (ST)', 'Reprisal (ST)']
* [169] Cosmo Meteor 1            - Damage = 76874 (Overkill:   674), Mitigations: ['Reprisal (MT)', 'H2 30s (H2)', 'Tactician (D3)', 'Feint (D2)']
  [175] Cosmo Meteor 2            - Damage = 69187,                   Mitigations: ['Reprisal (MT)', 'H2 30s (H2)', 'Tactician (D3)', 'Feint (D2)', 'H2 120s (H2)']
  [187] Cosmo Meteor (Flares)     - Damage = 70201,                   Mitigations: ['H2 120s (H2)']
```

## Configuration

There are three configuration YAMLs that are used by the script:

### damage_events.yaml

This file contains an array of all the damage events encountered. Right now,
this data is manually generated from log data from FFLogs.

### mitigation_config.yaml

This file contains the mitigations available to the party.

### party_config.yaml

This file contains information about the party (max HP, shield strength), and
also a configuration parameter.

- `buffer`: This value simulates how far in advance the mitigation will be used.
  A value of 0 means that the mitigation is used at the very last second, while
  a value of N means that the mitigation will be used at t - N time.