#! /usr/bin/env python3

# main.py

import json, logging, subprocess, sys
from typing import List, Tuple


def execute(command: List[str], shell: bool=False) -> Tuple[int, str, str]:
    logging.debug(f'Running {command}')
    result = subprocess.run(command, capture_output=True, shell=shell)
    code = result.returncode
    out = result.stdout.decode()
    err = result.stderr.decode()
    if len(err) > 0:
        logging.error(err)
    logging.debug(f'Return code: {code}')
    logging.debug(f'Output: {out}')
    return code, out, err


class Asana:
    def __init__(self, pat: str) -> None:
        self.accept = 'accept: application/json'
        self.auth = f'authorization: Bearer {pat}'
        self.url = 'https://app.asana.com/api/1.0/'

    def __do_query__(self, query: str) -> dict:
        _, response, _ = execute(['curl', '--header', self.accept, '--header', self.auth, '--request', 'GET', '--silent', '--url', f'{self.url}{query}'])
        return json.loads(response)

    def start(self, output: str) -> None:
        try:
            data = self.__do_query__('users/me')
            logging.info(f'Running as {data['data']['name']}')
            with open(output, 'w') as f:
                f.write('"Workspace","Team","Asana ID","Project","Status","Owner","Start Date","Due Date","Remarks"\n')
                user_gid = data['data']['gid']
                data = self.__do_query__('workspaces')
                for workspace in data['data']:
                    workspace_name = workspace['name']
                    logging.info(f'Exploring workspace {workspace_name}')
                    gid = workspace['gid']
                    data = self.__do_query__(f'users/{user_gid}/teams?organization={gid}')
                    for team in data['data']:
                        team_name = team['name']
                        logging.info(f'Checking team {team_name}')
                        projects = self.__do_query__(f'projects?team={team['gid']}&archived=false')
                        for project in projects['data']:
                            project_name = project['name']
                            project_gid = project['gid']
                            logging.info(f'Project #{project_gid}: {project_name}')
                            project_data = self.__do_query__(f'projects/{project['gid']}')
                            owner = project_data['data']['owner']
                            project_owner = '' if owner == None else owner['name']
                            status = project_data['data']['current_status']
                            color = None if status == None else status['color']
                            project_status = 'On track' if color == 'green' \
                                else 'At risk' if color == 'yellow' \
                                else 'Off track' if color == 'red' \
                                else 'On hold' if color == 'blue' \
                                else None
                            f.write(f'"{workspace_name}","{team_name}","{project_gid}","{project_name}","{project_status}","{project_owner}","{project_data['data']['start_on']}","{project_data['data']['due_date']}"\n')
        except Exception as e:
            logging.exception(e, exc_info=True, stack_info=True)


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(lineno)03d %(message)s')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
    if len(sys.argv) < 2:
        logging.fatal(f'Usage: {sys.argv[0]} <output file>')
        exit(1)
    asana = Asana('<insert your personal access token here>')
    asana.start(sys.argv[1])
