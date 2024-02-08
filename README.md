# FFXIVMitigationSolver

This script was initially written to try and solve for a mitigation plan for
the final phase of The Omega Protocol (Ultimate).

Usage:
```
python solver.py > output.txt
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