# pip install github3.py
import github3
import pandas as pd
import sys, os
import subprocess as sp
import json
from github import Github
from typing import Dict, Optional, List
import base64

def init():
    git_config = sp.run(["git","config","-l"], capture_output=True).stdout
    split_config = git_config.decode().split("\n")
    git_dict = {s[0]:s[1] for s in [ s.split('=') for s in split_config[:-11] ]}

    gh_username = git_dict['user.email']
    gh_password = git_dict['user.token']

    return gh_username, gh_password

def find_forks(repo_url: str):
    gh_username, gh_password = init()

    user, repo = repo_url.split('/')[-2:]

    g = github3.login(gh_username, gh_password)
    r = g.repository(user, repo)
    total_list = list(r.forks(sort='commits', number=r.fork_count))
    data = [ (i,i.updated_at,
            i.pushed_at, i.updated_at == i.created_at) for i in total_list ]
    df = pd.DataFrame(data,columns=['name','updated_at','pushed_at','ever_changed'])

    df = df.sort_values('ever_changed')
    print(df.ever_changed.value_counts())
    return df

def fork_status(repo_url: str):
    cmd = 'for branch in `git branch -r | grep -v HEAD`;do echo -e `git show --format="%ci %cr" $branch | head -n 1` \\t$branch; done | sort -r\n'
    os.system(cmd)

def find_contributors(repo_url: str):
    from .sshconf import SshConfig
    # gh_username, gh_password = init()

    user, repo = repo_url.split('/')[-2:]
    f = open('/Users/jakub/.gitconfig').read().splitlines()
    c = SshConfig(f)

    g = github3.login(gh_username, gh_password)
    r = g.repository(user, repo) 

def dir_diff(cwd: str, action = 'status') -> json:
    # get all dirs in cwd
    output = []
    all_directories = os.listdir(cwd)

    # check that all are directories
    dirs_only = [ d for d in all_directories if len(d.split('.'))==1 and d!='swap2' ]

    for dir in dirs_only:
        dir_path = os.path.abspath(dir)
        try:
            git_stash = sp.run(["git",action], cwd=dir_path, capture_output=True)
        except NotADirectoryError:
            print('Not a directory:', dir_path)
            continue
        output.append([dir_path, git_stash.stdout.decode()])

    diff_df = pd.DataFrame(output, columns=['dir',action])
    if action == 'status':
        # remove if up to master
        diff_df = diff_df[~diff_df.status.str.contains('On branch master')]
        
        # remove if main
        diff_df = diff_df[~diff_df.status.str.contains('On branch main')]
        
        # drop rows with empty ('') status
        diff_df = diff_df[diff_df.status != '']
        
        # create column up to date with True/False
        diff_df['up_to_date'] = diff_df.status.str.contains('up to date')
        diff_df = diff_df.sort_values(by='up_to_date')
        diff_df.reset_index(inplace=True)
        
        return diff_df
        
    else:
        non_empty_diffs = diff_df.loc[diff_df['diff'].str.len() > 0]
        dict_diffs = non_empty_diffs.to_dict(orient='index')

        # map 'dir' value to key in dict_diffs
        dict_diffs = {v['dir']:v['diff'] for k,v in dict_diffs.items()}

    return dict_diffs

def see_if_merged(repo_url: str):
    # see if branches have been merged to master
    cmd = 'git branch -r --merged master'
    output = sp.run([cmd], cwd=repo_url, shell=True, capture_output=True).stdout.decode().splitlines()
    branches = [ o.split('\t') for o in output ]
    df = pd.DataFrame(branches, columns=['branch'])
    df['branch'] = df['branch'].str.replace('origin/','').str.strip()
    
    df['merged'] = True
    
    return df

def find_branches(cwd: str, remote: bool, remove: bool) -> pd.DataFrame:
    # get branches in this git repo and their last commit
    if remote: cmd = 'for branch in `git branch -r | grep -v HEAD`;do echo -e `git show --format="%ci %cr" $branch | head -n 1` \\t$branch; done | sort -r\n'
    else: cmd = 'for branch in `git branch | grep -v HEAD`;do echo -e `git show --format="%ci %cr" $branch | head -n 1` \\t$branch; done | sort -r\n'
    output = sp.run([cmd], cwd=cwd, shell=True, capture_output=True).stdout.decode().splitlines()
    branches = [ o.split('\t') for o in output ]
    df = pd.DataFrame(branches, columns=['to_parse'])
    # split line '-e 2022-11-14 22:58:45 +0000 5 days ago torigin/f/file_cai'
    # to datetime and branch name
    
    df[['e','year','month','day_time','branch']] = df.to_parse.str.split('[+|-]', expand=True)
    # split day_time to day and time
    df[['day','time','None']] = df.day_time.str.split(' ', expand=True)
     
    # remove 'e' column
    df.drop('e', axis=1, inplace=True)
    df.drop('None', axis=1, inplace=True)

    # remove 'e' from the start of year column
    df['year'] = df.year.str[2:]
    
    # remove 'torigin/' from branch name
    if remote: df['branch'] = df.branch.str.replace('torigin/','').str[4:]
    else: df['branch'] = df.branch.str.replace('tf/','f/')
    df['timedelta'] = df.branch.str.split(' ').str[:-1].str.join(' ')
    df['branch'] = df.branch.str.split(' ').str[-1]
    
    # convert to datetime
    df['datetime'] = pd.to_datetime(df['year'] + ' ' + df['month'] + ' ' + df['day'] + ' ' + df['time'])
    
    # remove redundant columns
    df = df[['branch','datetime','timedelta']]
    
    merged_df = see_if_merged(cwd)
    df = df.merge(merged_df, on='branch', how='left')
    
    # drop None in branch column
    df = df[df['branch'].notna()]
    
    # sort by datetime
    df = df.sort_values(by='datetime', ascending=False)
    
    # if remove is True, remove branches that have been merged to master
    if remove=="True": df = df[df['merged'] != True]
    
    df.reset_index(inplace=True)
    df.drop('index', axis=1, inplace=True)
    
    return df

def validate_github_token(token: str, repo_url: str = None) -> bool:
    """Validate GitHub token has required permissions"""
    try:
        g = Github(token)
        user = g.get_user()
        
        # Test basic access
        _ = user.login
        
        # If repo_url is provided, test specific repo access
        if repo_url:
            parts = repo_url.rstrip('/').split('/')
            if len(parts) < 2:
                raise ValueError(f"Invalid repository URL format: {repo_url}")
                
            owner = parts[-2]
            repo_name = parts[-1]
            
            try:
                repo = g.get_repo(f"{owner}/{repo_name}")
                # Test repo access by getting a basic property
                _ = repo.full_name
                return True
            except Exception as e:
                if "404" in str(e):
                    print(f"Error: No access to repository {owner}/{repo_name}")
                elif "403" in str(e):
                    print("Error: Token lacks required permissions for this repository")
                return False
        
        # If no repo_url, just validate basic token access
        return True
        
    except Exception as e:
        if "401" in str(e):
            print("Error: Invalid GitHub token")
        elif "403" in str(e):
            print("Error: Token lacks required permissions")
        else:
            print(f"Error validating token: {str(e)}")
        return False

def get_github_token(repo_url: str = None) -> str:
    """Get GitHub token from config file"""
    config_path = os.path.expanduser('~/.dt_config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            token = config.get('github_token')
            if not token:
                raise Exception(
                    "GitHub token not found in config file.\n"
                    f"Please add 'github_token' to {config_path}\n"
                    "You can create a token at: https://github.com/settings/tokens\n"
                    "Required scopes: repo, admin:org"
                )
            
            if not validate_github_token(token, repo_url):
                raise Exception(
                    "Invalid GitHub token or insufficient permissions.\n"
                    "Please ensure your token has access to this repository"
                )
                
            return token
    except FileNotFoundError:
        raise Exception(f"Config file not found at {config_path}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON in config file at {config_path}")
    except Exception as e:
        raise Exception(f"Error reading config: {str(e)}")

def get_repo(repo_url: str):
    """Get GitHub repository object"""
    try:
        token = get_github_token(repo_url)  # Pass repo_url to validate specific access
        g = Github(token)
        
        # Extract owner and repo name from URL
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 2:
            raise ValueError(f"Invalid repository URL format: {repo_url}")
            
        owner = parts[-2]
        repo_name = parts[-1]
        
        try:
            repo = g.get_repo(f"{owner}/{repo_name}")  # Use get_repo directly instead of get_user().get_repo()
            return repo
        except Exception as e:
            if "404" in str(e):
                raise Exception(
                    f"Repository not found or not accessible: {owner}/{repo_name}\n"
                    "Please check:\n"
                    "1. The repository exists\n"
                    "2. The URL is correct\n"
                    "3. Your GitHub token has access to this repository\n"
                    "4. The repository is not private or you have proper permissions"
                )
            raise
            
    except Exception as e:
        raise Exception(f"Error accessing repository: {str(e)}")

def show_secrets(repo_url: str):
    """Show all secrets for a repository"""
    try:
        repo = get_repo(repo_url)
        try:
            secrets = repo.get_secrets()
            
            print(f"\nSecrets for {repo_url}:")
            count = 0
            for secret in secrets:
                print(f"- {secret.name} (Updated: {secret.updated_at})")
                count += 1
            
            if count == 0:
                print("No secrets found in this repository")
                
        except Exception as e:
            if "404" in str(e):
                print("Error: Unable to access repository secrets.")
                print("Please check that your GitHub token has the 'repo' and 'admin:org' scopes")
                print("You can update your token at: https://github.com/settings/tokens")
            else:
                raise
            
    except Exception as e:
        print(f"Error: {str(e)}")

def load_secrets_from_py(config_path: str, name_list: Optional[List[str]] = None, preserve_case: bool = True) -> Dict[str, str]:
    """Load secrets from a Python config file
    
    Args:
        config_path: Path to the Python config file
        name_list: Optional list of specific secret names to extract
        preserve_case: If True, maintains original case of secret names
    """
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        if name_list:
            # Filter secrets by name list
            secrets = {}
            for name in name_list:
                name = name.strip()  # Just remove whitespace, preserve case
                if hasattr(config, name):
                    secrets[name] = getattr(config, name)
                else:
                    # Try case-insensitive match if not found
                    all_vars = vars(config)
                    matches = [var for var in all_vars if var.lower() == name.lower()]
                    if matches:
                        secrets[name] = getattr(config, matches[0])
                    else:
                        print(f"Warning: Secret '{name}' not found in config file")
        else:
            # Get all variables (not just uppercase)
            secrets = {name: value for name, value in vars(config).items() 
                      if not name.startswith('_')}
        
        return secrets
    except Exception as e:
        raise Exception(f"Error loading Python config file: {str(e)}")

def add_secrets(repo_url: str, secrets: Dict[str, str] = None, config_path: Optional[str] = None, 
                secret_name: str = None, secret_value: str = None, name_list: Optional[List[str]] = None,
                preserve_case: bool = True):
    """Add secrets to a repository from a config file, dictionary, or single value"""
    try:
        # Handle single secret addition
        if secret_name and secret_value:
            secrets = {secret_name: secret_value}
        # Handle config file
        elif config_path:
            if config_path.endswith('.py'):
                secrets = load_secrets_from_py(config_path, name_list, preserve_case)
            else:
                with open(config_path, 'r') as f:
                    all_secrets = json.load(f)
                    if name_list:
                        secrets = {}
                        for name in name_list:
                            name = name.strip()
                            if name in all_secrets:
                                secrets[name] = all_secrets[name]
                            else:
                                matches = [k for k in all_secrets if k.lower() == name.lower()]
                                if matches:
                                    secrets[name] = all_secrets[matches[0]]
                                else:
                                    print(f"Warning: Secret '{name}' not found in config file")
                    else:
                        secrets = all_secrets
        elif not secrets:
            raise Exception("No secrets provided. Use either config file, secrets dict, or name/value pair")
        
        if not secrets:
            print("No secrets found to add")
            return
            
        repo = get_repo(repo_url)
        
        print(f"\nAdding secrets to {repo_url}:")
        for name, value in secrets.items():
            try:
                # Create the secret directly with the unencrypted value
                # The GitHub API will handle the encryption
                repo.create_secret(
                    secret_name=name,
                    unencrypted_value=str(value),
                    secret_type='actions'
                )
                print(f"✓ Added secret: {name}")
            except Exception as e:
                print(f"✗ Failed to add secret {name}: {str(e)}")
                
    except Exception as e:
        print(f"Error adding secrets: {str(e)}")

def delete_secret(repo_url: str, secret_name: str):
    """Delete a secret from a repository"""
    try:
        repo = get_repo(repo_url)
        repo.delete_secret(secret_name)
        print(f"Successfully deleted secret: {secret_name}")
    except Exception as e:
        print(f"Error deleting secret: {str(e)}")

def update_secret(repo_url: str, secret_name: str, new_value: str):
    """Update an existing secret in a repository"""
    try:
        repo = get_repo(repo_url)
        public_key = repo.get_public_key()
        
        repo.create_secret(secret_name, new_value, public_key.key_id, public_key.key)
        print(f"Successfully updated secret: {secret_name}")
    except Exception as e:
        print(f"Error updating secret: {str(e)}")

def git_summary(cwd: str = '.', filters: Optional[List[str]] = None) -> pd.DataFrame:
    """Get compact git status summary for all folders"""
    import shutil
    output = []
    dirs = [d for d in os.listdir(cwd) if os.path.isdir(d) and not d.startswith('.')]
    
    # Also check the current directory
    if os.path.exists(f"{cwd}/.git"):
        dirs.append('.')
    
    # Use custom filters if provided, otherwise use defaults
    default_filters = ['.DS_Store', '__pycache__/', '.pyc', '.pytest_cache/', '.vscode/', '.idea/']
    filter_list = filters if filters is not None else default_filters
    
    # Get terminal width
    try:
        term_width = shutil.get_terminal_size().columns
    except:
        term_width = 80
    
    for dir in dirs:
        git_path = f"{dir}/.git" if dir != '.' else '.git'
        if not os.path.exists(git_path):
            continue
        try:
            # Get branch
            branch_cmd = sp.run(["git", "branch", "--show-current"], cwd=dir, capture_output=True, text=True)
            branch = branch_cmd.stdout.strip() or "detached"
            
            # Get status
            status_cmd = sp.run(["git", "status", "--porcelain"], cwd=dir, capture_output=True, text=True)
            status_lines = status_cmd.stdout.strip().split('\n') if status_cmd.stdout.strip() else []
            
            # Extract files and apply filters
            if status_lines and status_lines[0]:
                all_files = [line[3:] for line in status_lines if line.strip()]  # Remove status prefix
                # Filter out files matching filter list
                filtered_files = [f for f in all_files if not any(filter_item in f for filter_item in filter_list)]
                changes = len(filtered_files)
                
                if changes > 0:
                    first_5_files = filtered_files[:5]
                    has_changes_info = f"{changes} files: {', '.join(first_5_files)}"
                    
                    # Truncate to fit terminal width, accounting for other columns
                    max_width = max(term_width - 40, 20)  # Leave space for folder, branch, num_changes columns
                    if len(has_changes_info) > max_width:
                        has_changes_info = has_changes_info[:max_width-3] + '...'
                else:
                    has_changes_info = "-"
            else:
                changes = 0
                has_changes_info = "-"
            
            output.append([dir, branch, has_changes_info, changes])
        except:
            continue
    
    return pd.DataFrame(output, columns=['folder', 'branch', 'has_changes', 'num_changes'])