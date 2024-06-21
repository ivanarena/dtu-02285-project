import re
import subprocess as sp
import os

def run_level(level='MAPF00.lvl', strategy='astar'):
    time_regex = r"\[server\]\[info\] Time to solve: (\d+\.\d+) seconds"
    actions_regex = r"\[server\]\[info\] Actions used: ([\d,]+)\."
    solved_regex = r"\[server\]\[info\] Level solved: (Yes|No)\."
    generated_regex = r"#Generated:\s*([\d,]+)"

    command = f'java -jar ../server.jar -l ../levels/{level} -c "python3 ./searchclient.py -{strategy} --max-memory 8192" -s 300 -t 180'
    competition_command = f'java -jar ../server.jar -l ../levels/competition/{level} -c "python3 ./searchclient.py -{strategy} --max-memory 8192" -s 300 -t 180'
    try:
        process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True, universal_newlines=True)

        results = {'level': level, 'strategy': strategy}

        for line in process.stdout:
            generated = re.search(generated_regex, line)
            time = re.search(time_regex, line)
            actions = re.search(actions_regex, line)
            solved = re.search(solved_regex, line)

            if generated:
                results["generated"] = int(generated.group(1).replace(',', ''))
            
            if actions:
                results["actions"] = int(actions.group(1).replace(',', ''))
            elif solved:
                results["solved"] = solved.group(1)
            elif time:
                results["time"] = float(time.group(1))
                process.kill() 
                break

        print(results)

    except Exception as e:
        print("Exception occurred:", e)
        return e


solved_levels = [
    # our test levels
    'TCBS0.lvl',
    'TCBS0B.lvl',
    'TCBS0C.lvl',
    'TCBS1.lvl',
    'TCBS1B.lvl',
    'TCBS2.lvl',
    'TCBS2B.lvl',
    'TCBS3.lvl',
    'TCBS3B.lvl',
    'TCBS4.lvl',
    'TAmjed.lvl',
    'TAmjedB.lvl',
    'TAmjedC.lvl',
    'TSAD1S.lvl',
    'BFSfriendly.lvl',
    'TMAExample.lvl',
    'TMAsimple3.lvl',
    'TMAsimple6.lvl',
    'TMAsimple7.lvl',
    'TMAsimple8.lvl',
    'TMAsimple9.lvl',
    'TMAsimple9B.lvl',
    'TMAsimple10_no_deadlocks.lvl',
    'TMAsimple10B_no_deadlocks.lvl',
    'TMAsimple11_no_deadlocks.lvl',
    'PIAForiginal.lvl',
    'PIAF2.lvl',
    'TSAD1S.lvl',
    
    # course test levels
    'MAsimple1.lvl',
    'MAsimple2.lvl',
    'MAsimple3.lvl',
    'MAsimple4.lvl',
    'MAExample.lvl',
    'MAPF00.lvl',
    'MAPF01.lvl',
    'MAPF02.lvl',
    'MAPF02B.lvl',
    'MAPF03.lvl',
    'MAPF03B.lvl',
    'RoboMatic.lvl',

    # single agent
    'SAsimple0.lvl',
    'SAsimple1.lvl',
    'SAsimple2.lvl',
    'SAsimple4.lvl',
    'SAmicromouseContest2011.lvl',
    'SAlabyrinth.lvl',
    'SAchoice.lvl',
    'SAD1.lvl',
    'SAlabyrinthOfStBertin.lvl',
    'SAsoko1_04.lvl',
    'SAsoko1_08.lvl',
    'SAsoko1_16.lvl',
    'SAsoko1_32.lvl',
    'SAsoko1_64.lvl',
    'SAsoko1_128.lvl',
    'SAsoko2_04.lvl',
    'SAsoko2_08.lvl',
    'SAsoko2_16.lvl',
    'SAsoko2_32.lvl',
    'SAsoko2_64.lvl',
    'SAsoko2_128.lvl',
    'SAsoko3_04.lvl',
    'SAsoko3_06.lvl',
    'SAsoko3_07.lvl',
    'SAsoko3_08.lvl',
    'SAsoko3_16.lvl',
    'SAsoko3_32.lvl',
    'SAsoko3_64.lvl',
]

levels_directory = '../levels'
competition_levels_directory = '../levels/competition'
levels = [f for f in os.listdir(levels_directory) if os.path.isfile(os.path.join(levels_directory, f))]
competition_levels = [os.path.join('competition', f) for f in os.listdir(competition_levels_directory) if os.path.isfile(os.path.join(competition_levels_directory, f))]
levels.sort()
competition_levels.sort()

solved_competition_levels = [
    'competition/PIAF.lvl',
    'competition/OnlyLast.lvl',
    'competition/JarvisExe.lvl',
    'competition/Spds.lvl',
    'competition/Raffaello.lvl',
]
solved_levels = solved_competition_levels + solved_levels

for lvl in solved_levels:
# for lvl in competition_levels:
    run_level(lvl, 'astar')
