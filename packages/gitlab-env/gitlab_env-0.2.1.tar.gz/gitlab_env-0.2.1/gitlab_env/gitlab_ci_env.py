#!/usr/bin/python3
import gitlab, os, re, argparse, sys, yaml
from git import Repo


class GitlabProject:
    def __init__(self, url, path, vars_file):
        '''
        Create Gitlab instanse.
        "keep_base_url=True" needs to resolve warning:
        "UserWarning: The base URL in the server response differs from the user-provided base URL (https://gitlab.example.com -> http://gitlab.example.com)."
        '''
        self.gl = gitlab.Gitlab(url, private_token=os.environ['GITLAB_TOKEN'], keep_base_url=True)
        self.project = self.gl.projects.get(path, lazy=True)                          # Create project's object
        self.project_variables = self.project.variables.list(get_all=True)            # Get variables
        self.vars_dict = {}
        self.parse_dict = {}
        self.vars_file = vars_file

    def gen_vars_dict(self):
        for variable in self.project_variables:                                  # Create dict of environment scopes
            scope = variable.environment_scope
            
            if scope not in self.vars_dict:
                self.vars_dict[scope] = {}
            self.vars_dict[scope][variable.key] = {
                'value': variable.value,
                'type': variable.variable_type,
                'protected': variable.protected,
                'masked': variable.masked,
                'raw': variable.raw
            }

    def gen_varfile_yaml(self):
        output = {'environments': self.vars_dict}
        with open(self.vars_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(output, f,
                           default_flow_style=False,
                           allow_unicode=True,
                           sort_keys=False,
                           explicit_start=True,
                           width=1000)
        print(f'Variables written to: {self.vars_file}')

    def parse_varfile_yaml(self, force=False):
        with open(self.vars_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        raw_envs = data.get('environments', {})
        self.parse_dict = {}

        for scope, variables in raw_envs.items():
            self.parse_dict[scope] = {}
            for key, val in variables.items():
                if isinstance(val, dict):
                    self.parse_dict[scope][key] = {
                        'value': val.get('value'),
                        'type': val.get('type', 'env_var'),
                        'protected': val.get('protected', False),
                        'masked': val.get('masked', False),
                        'raw': val.get('raw', False)
                    }
                else:
                    self.parse_dict[scope][key] = {
                        'value': val,
                        'type': 'env_var',
                        'protected': False,
                        'masked': False,
                        'raw': False
                    }

        if not force:
            for env in list(self.vars_dict.keys()):
                if env not in self.parse_dict:
                    del self.vars_dict[env]

    def print_stdout_json(self):
        for env in self.vars_dict:
            print(f'###  Environment scope: "{env}" ###')
            for key, meta in self.vars_dict[env].items():
                print(f'# {key}: "{meta["value"]}"')
            print()

    def print_envs(self):
        print('List of environment scopes: ')
        for env in self.vars_dict:
            print(env)

    def select_envs(self, envs):
        del_list = [env for env in self.vars_dict if env not in envs]
        for env in del_list:
            del self.vars_dict[env]
            print(f'Env "{env}" deleted from output.')
        print()

    def gen_push_list(self):
        push_list = []

        for env_scope in self.parse_dict:
            for key, parsed_var in self.parse_dict[env_scope].items():
                parsed_value = parsed_var['value']
                parsed_type = parsed_var.get('type', 'env_var')
                parsed_protected = parsed_var.get('protected', False)
                parsed_masked = parsed_var.get('masked', False)
                parsed_raw = parsed_var.get('raw', False)

                existing = self.vars_dict.get(env_scope, {}).get(key)

                if not existing:
                    push_list.append({
                        'key': key,
                        'value': parsed_value,
                        'variable_type': parsed_type,
                        'environment_scope': env_scope,
                        'protected': parsed_protected,
                        'masked': parsed_masked,
                        'raw': parsed_raw,
                        'action': 'create'
                    })
                else:
                    if (
                        existing['value'] != parsed_value or
                        existing.get('type', 'env_var') != parsed_type or
                        existing.get('protected', False) != parsed_protected or
                        existing.get('masked', False) != parsed_masked or
                        existing.get('raw', False) != parsed_raw
                    ):
                        push_list.append({
                            'key': key,
                            'value': parsed_value,
                            'variable_type': parsed_type,
                            'environment_scope': env_scope,
                            'protected': parsed_protected,
                            'masked': parsed_masked,
                            'raw': parsed_raw,
                            'action': 'update'
                        })

        for env_scope in self.vars_dict:
            for key in self.vars_dict[env_scope]:
                if env_scope not in self.parse_dict or key not in self.parse_dict[env_scope]:
                    push_list.append({
                        'key': key,
                        'environment_scope': env_scope,
                        'action': 'delete'
                    })

        return push_list

    def push_vars(self, push_list):
        for i in push_list:
            if i['action'] == 'create':
                self.project.variables.create({
                    'key': i['key'],
                    'value': i['value'],
                    'variable_type': i.get('variable_type', 'env_var'),
                    'environment_scope': i['environment_scope'],
                    'protected': i.get('protected', False),
                    'masked': i.get('masked', False),
                    'raw': i.get('raw', False)
                })
                print('Created:', i)

            elif i['action'] == 'update':
                self.project.variables.update(i['key'], {
                    'value': i['value'],
                    'variable_type': i.get('variable_type', 'env_var'),
                    'protected': i.get('protected', False),
                    'masked': i.get('masked', False),
                    'raw': i.get('raw', False)
                }, filter={'environment_scope': i['environment_scope']})
                print('Updated:', i)

            elif i['action'] == 'delete':
                self.project.variables.delete(i['key'], filter={'environment_scope': i['environment_scope']})
                print('Deleted:', i)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str, default='.gitlab-ci-variables.yml')
    parser.add_argument('-e', '--envs', nargs='+', help='Choose environment scope (Try --list before).', type=str)
    parser.add_argument('-g', '--get', help='Fetch variables from gitlab.', action='store_true')
    parser.add_argument('-p', '--push', help='Push variables to gitlab.', action='store_true')
    parser.add_argument('--force', help='Force push (delete vars not in file)', action='store_true')
    parser.add_argument('-l', '--list', help='List environment scopes.', action='store_true')

    args = parser.parse_args()
    repo = Repo(os.getcwd())
    _, domain, path = re.split('@|:', repo.remote().url.split('.git')[0])
    url = 'https://' + domain

    project = GitlabProject(url, path, args.file)
    project.gen_vars_dict()

    if args.envs and args.get:
        project.select_envs(args.envs)
        project.gen_varfile_yaml()
    elif args.get:
        project.gen_varfile_yaml()
    elif args.push:
        project.parse_varfile_yaml(args.force)
        push_list = project.gen_push_list()
        project.push_vars(push_list)
    elif not len(sys.argv) > 1:
        project.print_stdout_json()
    elif args.list:
        project.print_envs()
    elif args.envs:
        project.select_envs(args.envs)
        project.print_stdout_json()


if __name__ == '__main__':
    main()
