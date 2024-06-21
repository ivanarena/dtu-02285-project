# Final programming project

A project made for DTU course 02285 Artificial Intelligence and Multi-Agent Systems, spring 2024.

Made by group no. 5, group name PIAF.

## Instructions

### Run levels

From root folder:

```bash
cd searchclient/searchclient_python
```

Then run this command tweaking the parameters if necessary:

```bash
java -jar ../server.jar -l ../levels/MAPF00.lvl -c "python3 searchclient.py -astar" -g -s 300 -t 180
```

### Produce competition zip

The command run to produce the competition results is:

```bash
java -jar ../server.jar -c "python3 searchclient.py -astar" -l "../levels/competition/" -t 180 -o "PIAF.zip"
```

### Testing script

To use the testing script run from root folder:

```bash
cd searchclient/searchclient_python
python3 runner.py
```
