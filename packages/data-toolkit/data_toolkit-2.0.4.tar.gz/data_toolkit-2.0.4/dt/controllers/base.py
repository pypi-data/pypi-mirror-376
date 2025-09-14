from regex import E
from dt.ext.aws_s3 import get_lastest_file
from cement import Controller, ex
from cement.utils.version import get_version_banner
from ..core.version import get_version
from pprint import pprint as pp
import os
import shutil

VERSION_BANNER = """
ML & data helper code! %s
%s
""" % (get_version(), get_version_banner())


class Base(Controller):
    class Meta:
        label = 'base'

        # text displayed at the top of --help output
        description = 'ML & data helper code!'

        # text displayed at the bottom of --help output
        epilog = 'Usage: dt command [args] [kwargs]'

        # controller level arguments. ex: 'dt --version'
        arguments = [
            ### add a version banner
            ( [ '-v', '--version' ],
              { 'action'  : 'version',
                'version' : VERSION_BANNER } ),
        ]


    def _default(self):
        """Default action if no sub-command is passed."""

        self.app.args.print_help()

    @ex(
        # TODO: implement `--home` for setting up home address
        help='AWS Security Groups helper functions',
        arguments=[
            (['action'],{
                "help" : "One of {update, show, ls}",
                "action": "store"
            }),
            (['-n','--name'],{
                "help" : "Name of the SG to act on",
                "action": "store"
            }),
            (['-ip'],{
                "help" : "IP to add to security group. Use 'anywhere' to allow from any IP.",
                "action": "store"
            }),
            (['-p','--profile'],{
                "help" : "Which AWS profile should boto3 use",
                "action" : "store"
            }),
            (['-P','--ports'],{
                "help" : "Which ports should AWS SG set",
                "action" : "store"
            }),
            (['-m','--messages'],{
                "help" : "Message to add to SG description, WARNing will not use default ports if used "
                         "Accepts port:messages pairs separated by commas. E.g. 42:answer to life, 22:memes",
                "action" : "store"
            }),
            (['-r','--region'],{
                "help": "Which AWS region should boto3 use",
                "action": "store"
            }),
            (['-i','--id'],{
                "help" : "ID of the SG to act on from the ls DataFrame",
                "action" : "store"
            }),
            (['-a', '--all'],{
                "help" : "Show all security groups, including those not associated with any instance",
                "action": "store_true"
            }),
        ]
    )
    def sg(self):
        from ..ext.aws_sg import sg_ls, update_sg_to_ip, get_sg

        profile = self.app.pargs.profile or 'default'
        region = self.app.pargs.region or 'eu-west-1'

        if self.app.pargs.action == 'ls':
            sg_ls(region, profile, show_all=self.app.pargs.all)
        elif self.app.pargs.action == 'show':
            sg_id = self.app.pargs.id
            sg_name = self.app.pargs.name
            if sg_id is None and sg_name is None:
                raise ValueError("Either sg_id or sg_name must be provided")
            get_sg(profile, sg_id=sg_id, sg_name=sg_name, region=region)
        elif self.app.pargs.action == 'update':
            sg_name = self.app.pargs.name
            sg_id = self.app.pargs.id
            ports = self.app.pargs.ports
            if ports:
                ports = [int(p) for p in ports.split(',')]
            else:
                ports = None  # Set to None if no ports specified
            messages = self.app.pargs.messages or ''
            ip = self.app.pargs.ip
            update_sg_to_ip(sg_name=sg_name, sg_id=sg_id, profile=profile,
                            ports=ports, messages=messages, region=region, ip=ip)
        else:
            print("Invalid action. Choose one of {update, show, ls}")

    @ex(
        help="GCP VM Instances helper commands."
        "These are currently in alpha and some may not work",
        arguments=[
            (['action'],{
                    "help" : "To show one of {ls, scp}.",
                    "action" : "store"
                }),
            (['--rpath'],{
                "help" : "What is the location on the remote server",
                "action": "store"
            }),
            (['-f','--filter'],{
                "help" : "One of {live, all}. Default: live",
                "action": "store"
            }),
            (['-id'],{
                "help": "InstanceId to be passed to ec2 start/stop",
                "action": "store"
            })
        ]
    )
    def gcp(self):
        from ..ext.gcp import gcp_ls, scp

        # profile = self.app.pargs.profile or 'default'
        # filt = self.app.pargs.filter or "live"

        if self.app.pargs.action=='ls':
            print(gcp_ls())

        # elif self.app.pargs.action=='update':
        #     print(update_ec2_ssh(profile))

        # elif self.app.pargs.action=='start':
        #     start_ec2(self.app.pargs.id, profile)

        elif self.app.pargs.action=='scp':
            scp(int(self.app.pargs.id), self.app.pargs.rpath)
            # stop_ec2(self.app.pargs.id, profile)

        else:
            raise NotImplementedError("Choose one of {ls, update, start, stop}")

    @ex(
        help='Tree helper/replacement functions',
        arguments= [
            (['loc'], {
                "help": "Location of the tree to act on",
                "action": "store"
            }),
            (['-n'],{
                "help": "Depth of the tree to print",
                "action": "store"
            }),
            (['-f'],{
                "help": "Print out full path",
                "action": "store"  
            })
        ]
    )
    def tree(self):
        from ..ext.tree import tree
        
        level = int(self.app.pargs.n or 2)
        full_path = int(self.app.pargs.f or 0)
        
        tree(self.app.pargs.loc, level, full_path)
        

    @ex(
        help="AWS EC2 helper commands.",
        arguments=[
            (['action'],{
                    "help" : "To show one of {ls, update}.",
                    "action" : "store"
                }),
            (['-p','--profile'],{
                "help" : "Which AWS profile should boto3 use.",
                "action": "store"
            }),
            (['-f','--filter'],{
                "help" : "One of {live, all}. Default: live",
                "action": "store"
            }),
            (['-id'],{
                "help": "InstanceId to be passed to ec2 start/stop",
                "action": "store"
            }),
            (['-r','--region'],{
                "help": "Which region to use",
                "action": "store"
            }),
        ]
    )
    def ec2(self):
        from ..ext.aws_ec2 import get_ec2, start_ec2, stop_ec2, update_ec2_ssh

        profile = self.app.pargs.profile or 'default'
        filt = self.app.pargs.filter or "live"
        region = self.app.pargs.region or "eu-west-1"

        if self.app.pargs.action=='ls':
            print(get_ec2('live', profile, filt, region))

        elif self.app.pargs.action=='update':
            print(update_ec2_ssh(profile))

        elif self.app.pargs.action=='start':
            start_ec2(self.app.pargs.id, profile)

        elif self.app.pargs.action=='stop':
            stop_ec2(self.app.pargs.id, profile)

        else:
            raise NotImplementedError("Choose one of {ls, update, start, stop}")

    @ex(
        help="Operations to easily work with remote servers / devices",
        arguments=[
            # TODO: maybe make grabable from ec2 ls
            (['ip'],{
                "help" : "IP of the target server",
                "action" : "store"
            }),
            (['-r','--remote'],{
                "help" : "Remote path on the target server",
                "action": "store"
            }),
            (['-u','--user'],{
                "help" : "Which user to ssh with.",
                "action" : "store"
            }),
            (['--server_name','-sn'],{
                "help" : "To give the SFTP server a name.",
                "action" : "store"
            }),
            (['-i', '--identity'],{
                "help" : "Path to the identity file to use for ssh.",
                "action" : "store"
            }),
            (['-p','--port'],{
                "help" : "Port over which to run SFTP.",
                "action" : "store"
            })
        ]
    )
    def sftp(self):
        ip = self.app.pargs.ip
        remote = self.app.pargs.__dict__.get('remote') or self.app.pargs.__dict__.get('r') or '/data/openpilot'
        port = self.app.pargs.__dict__.get('port') or self.app.pargs.__dict__.get('p') or 8022
        user = self.app.pargs.__dict__.get('user') or self.app.pargs.__dict__.get('u') or 'comma'
        server_name = self.app.pargs.__dict__.get('server_name') or self.app.pargs.__dict__.get('sn') or 'C3'
        identity = self.app.pargs.__dict__.get('identity') or self.app.pargs.__dict__.get('i') or os.path.expanduser("~/openpilot/tools/ssh/CL-key")

        from ..ext.sftp_conf import write_sftp
        
        write_sftp(name=server_name, ip=ip, port=port, user=user,
                    remote=remote, key_path=identity)

    @ex(
        help="OpenAI API operations (command suggestions, video transcription, model listing)",
        arguments=[
            (['action'],{
                "help": "'ls' to list models, 'cmd' for command suggestions, 'vid' for video transcription, 'whisper' for audio transcription",
                "action": "store"
            }),
            (['text'],{
                "help": "Description of the command you want (for 'cmd' action) or audio file path (for 'whisper' action)",
                "action": "store",
                "nargs": "?"
            }),
            (['-t', '--target'],{
                "help": "Video file to transcribe (required for 'vid' action)",
                "action": "store"
            }),
            (['-o', '--output'],{
                "help": "Save output to file instead of printing",
                "action": "store"
            }),
            (['-m', '--model'],{
                "help": "Model to use (default: gpt-4 for cmd, whisper-1 for vid/whisper)",
                "action": "store"
            }),
            (['--execute'],{
                "help": "Execute the suggested command (will ask for confirmation)",
                "action": "store_true"
            }),
            (['-y', '--yes'],{
                "help": "Automatically execute without confirmation",
                "action": "store_true"
            })
        ]
    )
    def oai(self):
        from ..ext.openai_helper import (get_command_suggestion, list_models, 
                                       execute_command, transcribe_video, 
                                       analyze_youtube_video, transcribe_local_audio)
        import os
        
        if self.app.pargs.action == 'ls':
            list_models()
        elif self.app.pargs.action == 'cmd':
            # Get current directory contents
            cwd = os.getcwd()
            files = os.listdir(cwd)
            
            # Build context with current directory info
            context = f"Current directory: {cwd}\nFiles: {', '.join(files)}\n"
            
            model = self.app.pargs.model or 'gpt-4'
            text = self.app.pargs.text
            
            if not text:
                print("Please provide a command description")
                return
            
            suggestion = get_command_suggestion(text, context, model)
            print(f"Suggested command:\n{suggestion}")
            
            if self.app.pargs.execute or self.app.pargs.yes:
                execute_command(suggestion, auto_confirm=self.app.pargs.yes)
        elif self.app.pargs.action == 'vid':
            video_file = self.app.pargs.target
            output_file = self.app.pargs.output
            model = self.app.pargs.model or 'whisper-1'
            
            if not video_file:
                print("Please provide a video file using -t/--target")
                return
            
            transcript = transcribe_video(video_file, model)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(transcript)
                print(f"Transcript saved to {output_file}")
            else:
                print("\nTranscript:")
                print(transcript)
        elif self.app.pargs.action == 'whisper':
            audio_file = self.app.pargs.text
            output_file = self.app.pargs.output
            model = self.app.pargs.model or 'whisper-1'
            
            if not audio_file:
                print("Please provide an audio file path")
                return
                
            if not os.path.exists(audio_file):
                print(f"Error: Audio file not found: {audio_file}")
                return
            
            transcript = transcribe_local_audio(audio_file, model)
            
            if transcript:
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(transcript)
                    print(f"Transcript saved to {output_file}")
                else:
                    print("\nTranscript:")
                    print(transcript)
        else:
            print("Invalid action. Use 'cmd' for command suggestions, 'ls' to list models, 'vid' for video transcription, or 'whisper' for audio transcription")

    @ex(
        help='Monitor lack of GPU activity. When there is none, runs -job',
        arguments=[
            (['-job'],{
                "help" : "Text of the command to run after no GPU activity",
                "action" : "store"
            }),
            (['-n'], {
                "help" : "Number of processes before 'no activity'.",
                "action" : "store"
            })
        ]
    )
    def monitor(self):
        from ..ext.monitor import submit
        submit(self.app.pargs.job)


    # number of files
    @ex(
        help='Displays the number of files',
        arguments=[
            (['-d'], {
            "help" : "which directory to show",
            "action" : "store" } )
        ]
    )
    def nf(self):
        loc = self.app.pargs.d or '.'
        os.system(f'ls {loc} | wc -l')

    @ex(
        help="Appends defaults: from zshrc.txt to ~/.bashrc or ~/.zshrc or tmux conf",
        arguments = [
            (['shell'], {
                "help" : "One of {sh, zsh, tmux}. Imports a DT version of zshrc into bashrc or zshrc. or tmux .conf into ~/",
                "action": "store"
            })
        ]
    )
    def load(self):
        # TODO: reload the file after.
        # TODO: load git aliases
        zshrc = os.path.abspath(__file__).split('/')[:-2] + ['ext', 'zshrc.txt']
        tmux = os.path.abspath(__file__).split('/')[:-2] + ['ext', 'tmux.conf']

        zshrc_path = os.path.join('/'.join(zshrc))
        tmux_path = os.path.join('/'.join(tmux))
        if self.app.pargs.shell == 'sh':
            os.system(f'cat {zshrc_path} >> ~/.bashrc ')
        elif self.app.pargs.shell == 'zsh':
            os.system(f'cat {zshrc_path} >> ~/.zshrc ')
        elif self.app.pargs.shell == 'tmux':
            os.system(f'cat {tmux_path} >> ~/.tmux.conf ')
        else:
            raise NotImplementedError("Try one of {sh, zsh, tmux}")


    @ex(
        help='Operations on CLI hist',
        arguments=[
            (['-s'],{
                "help" : "Which lines to save separated by commas",
                "action" : "store"
            }),
            (['-n'],{
                # TODO: probably better as mandatory
                "help" : "Which lines from the selected history to show/save",
                "action" : "store"
            }),
            (['-e'],{
                "help": "Which terns to exclude separated by commas",
                "action": "store"
            }),
            (['-a','--alias'],{
                "help": "Name for the snippet.",
                "action" : "store"
            })
        ]
    )
    def hist(self):
        if not self.app.pargs.s:
            from ..ext.hist import hist_tail
            import pprint as pp
            n_lines = int(self.app.pargs.n or 20)
            excluded_terms = self.app.pargs.e or []
            if isinstance(excluded_terms, str): excluded_terms = excluded_terms.split(',')
            pp.pprint(hist_tail(n_lines, excluded_terms))
        else:
            from ..ext.hist import hist_save
            import uuid
            
            n_lines = int(self.app.pargs.n or 20)
            lines_to_save = [int(x) for x in str(self.app.pargs.s).split(',')]
            snippet_name = self.app.pargs.__dict__.get('a') or self.app.pargs.__dict__.get('alias') or str(uuid.uuid4())
            print(f'Saving {lines_to_save} lines from history to snippet {snippet_name}')
            
            hist_save(lines_to_save, snippet_name, n_lines=n_lines)
            
    # function fd (fake data) to generate fake data based on a template or clipboard
    @ex(
        help='Generate fake data',
        arguments=[
            (['-n'],{
                "help" : "Number of lines to generate",
                "action" : "store"
            }),
            (['-t','--template'],{
                "help" : "Path to template for data generation",
                "action" : "store"
            }),
            (['-c','--columns'],{
                "help" : "Whether column names are NOT present",
                "action" : "store_true"
            }),
            (['--csv'],{
                'help' : "Whether to generate csv", 
                "action" : "store_true"
            }),
            (['-pk','--primary-key'],{
                "help" : "Primary key column name (-1 crate a new column)",
                "action" : "store"
            }),
            (['-d'],{
                "help" : "Delimiter for the generated data",
                "action" : "store"
            })
        ]
    )
    def fd(self):
        from ..ext.fake_data import generate_fake_data
        n_lines = int(self.app.pargs.__dict__.get('n') or 10)
        template = self.app.pargs.__dict__.get('t') or self.app.pargs.__dict__.get('template')
        columns = not (self.app.pargs.__dict__.get('c') or self.app.pargs.__dict__.get('columns')) 
        csv = self.app.pargs.__dict__.get('csv')
        primary_key = self.app.pargs.__dict__.get('pk') or self.app.pargs.__dict__.get('primary_key')
        delimiter = self.app.pargs.__dict__.get('d') or ','
        
        generate_fake_data(n_lines, template, columns, csv, primary_key, delimiter)
        

    @ex(
        help='Operations with snippets',
        arguments=[
            (['-n','--n_lines'],{
                "help" : "Which snippet to run/create. Using commas to seperate ids"
                "e.g. `dt run 13,23`",
                "action" : "store"
            }),
            (['-ssh'],{
                "help" : "Whether the command (includes?)/is? an SSH command",
                "action": "store"
            }),
            (['-c'],{
                # TODO: probably better as mandatory
                "help" : "Which lines from the selected history to show/save",
                "action" : "store"
            }),
            # TODO: what if non-default n lines has been pased to hist
            (['--save'],{
                "help" : "Whether to save the snippet to the history",
                # TODO: figure out if bool
                "action" : "store"   
            }),
            (['-a','--alias'],{
                "help": "Name of the alias to run",
                "action" : "store"
            })
        ]
    )
    def run(self):
        is_alias = self.app.pargs.__dict__.get('a') or self.app.pargs.__dict__.get('alias') or False
        
        if is_alias:
            from ..ext.run import run_command_from_alias
            run_command_from_alias(is_alias)
        else:
            from ..ext.run import run_command
            n_lines = [int(x) for x in str(self.app.pargs.n_lines).split(',')]
            run_command(n_lines)
            
    @ex(
        help='Operations with s3 buckets',
        arguments=[
            (['action'],{
                "help" : "One of {ls, link}",
                "action" : "store"
            }),
            (['target'],{
                "help" : "The target of the action. Can be {dongle_id, -1}",
                "action" : "store"
            }),
            (['--num_segments'],{
                "help" : "Number of recent files to show",
                "action" : "store",
                "default" : 10
            }),
            (['-n','--show_n'],{
                "help" : "Number of recent files to show",
                "action" : "store",
                "default" : 50
            }),
            (['-f','--filter'],{
                "help" : "Filter the files by this int",
                "action" : "store",
                "default" : 0
            }),
            (['-F','--file'],{
                "help": "File containing metadata",
                "action": "store",
                "default": "/home/jakub/data/devices.csv"
            })
        ]
    )
    def s3(self):
        if self.app.pargs.action == 'link':
            from ..ext.aws_s3 import get_lastest_file
            print(get_lastest_file(self.app.pargs.target))

        # ls actions for all dongle ids
        if self.app.pargs.action == 'ls':
            filter = self.app.pargs.__dict__.get('filter') or self.app.pargs.__dict__.get('f') or 0
            metadata_file = self.app.pargs.__dict__.get('file') or self.app.pargs.__dict__.get('F')
            
            from ..ext.aws_s3 import get_drives
            show_n = int(self.app.pargs.__dict__.get('show_n') or self.app.pargs.__dict__.get('n'))

            if self.app.pargs.target == '-1':
                get_drives(self.app.pargs.target, show_n=show_n, metadata_file=metadata_file, filter=filter)
            else:
                # TODO: potentially removed
                # num_segments = self.app.pargs.__dict__.get('n') or self.app.pargs.__dict__.get('num_segments')
                get_drives(self.app.pargs.target, show_n=show_n, metadata_file=metadata_file, 
                            filter=int(filter))

        if self.app.pargs.action == 'pull':
            from ..ext.aws_s3 import pull_latest
            pull_latest(self.app.pargs.target)

    @ex(
        help='Operations on the SSH config',
        arguments=[
            (['action'],{
                "help" : "To show one of {set, ls, update}. Set is for new remote value, update is to grab from AWS",
                "action" : "store"
            }),
            (['-host'],{
            "help" : "Which SSH config host to SET",
            "action": "store"
            }),
            (['-ip'],{
                "help" : "The IP to SET in the ssh config as HostName",
                "action" : "store"
            })
        ]
    )
    def ssh(self):
        from ..ext.sshconf import read_ssh_config
        from ..ext.sshconf import print_ls
        ssh_config_path = os.path.expanduser('~/.ssh/config')

        if self.app.pargs.action=='set':
            ssh_config_obj = read_ssh_config(ssh_config_path)
            ssh_config_obj.set(self.app.pargs.host, HostName=self.app.pargs.ip)
            ssh_config_obj.write(ssh_config_path)
            print_ls(ssh_config_obj)
            

        elif self.app.pargs.action=='update':
            from ..ext.aws_ec2 import update_ec2_ssh
            profile ='default' # or  self.app.pargs
            # print(update_ec2_ssh(profile))
            update_ec2_ssh(profile)
            ssh_config_obj = read_ssh_config(ssh_config_path)
            print_ls(ssh_config_obj)

        elif self.app.pargs.action=='ls':
            ssh_config_obj = read_ssh_config(ssh_config_path)
            print_ls(ssh_config_obj)

        else:
            # raise NotImplementedError()
            print('Arg out of {set, update} provided assuming an SSH command.')
            ssh_config_obj = read_ssh_config(ssh_config_path)
            target = self.app.pargs.action
            if not target in ssh_config_obj.hosts_: raise Exception(f'Host {target} not in configured hosts.')
            else:
                os.system('dt sg update')
                os.system(f'ssh {target}')

    @ex(
        help='Basic viz using streamlit for image comparisons',
        arguments = [
            (['images'], {
                'help' : 'Location of target images',
                'action' : "store"
            }),
            (['labels'], {
                'help' : 'Location of target labels',
                "action" : 'store'
            }),
            (['adapted'], {
                'help' : 'Location of domain adapted images',
                "action" : "store"
            })
            #     'action' : "store",
            #     "images" : '/efs/public_data/gta5/images',
            #     "labels" : '/efs/public_data/gta5/labels',
            #     "adapted" : '/efs/public_data/images'
            # })
        ]
    )
    def viz(self):
        args = self.app.pargs
        print(args.images)
        from ..ext.firelit import create_viz
        create_viz(args.images, args.labels, args.adapted)

    @ex(
        help="Download file from Google Drive",
        arguments=[
            (["file_id"], {
                "help" : "The file id of the file to download",
                "action" : "store"
            }),
            (["destination"], {
                "help": "The destination to download the file to",
                "action" : "store"
            })
        ]
    )
    def gdrive(self):
        from ..ext.gdrive_dl import download_file_from_google_drive
        download_file_from_google_drive(self.app.pargs.file_id, self.app.pargs.destination)


    @ex(
        help='Operations with config.',
        arguments = [
            (['action'], {
                "help" : "One of {show, set, loc}: \
                *show*: show configs Sentry DNS etc. \
                *set*: Resets the config from CLI. \
                *loc*: shows the location of the config",
                'action' : "store",
            })
        ]
    )
    def config(self):
        # TODO: setup Data-toolkit specific config
        # shows config
        
        if self.app.pargs.action=='show' or self.app.pargs.action=='ls':
            from ..ext.config import show_config
            show_config()

        # shows the path of the config
        if self.app.pargs.action=='loc':
            config_path = os.path.join(os.path.expanduser('~'), 'dt_config.json')
            print(config_path)

        # resets the config
        # TODO this config method needs programmatic acces for spot instances
        if self.app.pargs.action=='set':
            from ..ext.tracking import initialize
            initialize(overwrite=True)

        elif self.app.pargs.action not in ['set','loc', 'show','ls']:
            raise NotImplementedError("Try one of {show, set, loc}")


    @ex(
        help='All Github related operations',
        arguments=[
            (['action'],{
                "help" : """To show one of {ff, fs, contrib, diff, branches, secrets, summary}. \r\n
                ff: Finds the forks of a repo.  \r\n
                fs: Finds the last commit of a repo by fork. \r\n 
                contrib: Finds the contributors of a repo. \r\n
                diff: Finds the all the diffs in directories below. \r\n
                secrets: Manage repository secrets. \r\n
                summary: Show git branch and changes summary for all folders""",
                "action" : "store"
            }),
            (['-url'],{
                "help" : "Github URL to act on"
            }),
            (['-c', '--config'],{
                "help": "Path to config file (.py or .json) containing secrets",
                "action": "store"
            }),
            (['-n', '--name'],{
                "help": "Secret name to add/update",
                "action": "store"
            }),
            (['-v', '--value'],{
                "help": "Secret value to set",
                "action": "store"
            }),
            (['--delete'],{
                "help": "Delete the secret specified by -n/--name",
                "action": "store_true"
            }),
            (['--force'],{
                "help": "Skip confirmation for delete operation",
                "action": "store_true"
            }),
            (['-nl', '--name-list'],{
                "help": "Comma-separated list of secret names to extract from config",
                "action": "store"
            }),
            (['--preserve-case'],{
                "help": "Preserve original case of secret names (default: True)",
                "action": "store_true",
                "default": True
            }),
            (['--uppercase'],{
                "help": "Convert all secret names to uppercase",
                "action": "store_true"
            }),
            (['-f', '--filter-files'],{
                "help": "Comma-separated list of files/patterns to filter out (default: .DS_Store,__pycache__/,.pyc,.pytest_cache/,.vscode/,.idea/)",
                "action": "store"
            })
        ]
    )
    def gh(self):
        if self.app.pargs.action=='ff':
            from ..ext.github import find_forks
            print(find_forks(self.app.pargs.url))
        elif self.app.pargs.action=='fs':
            from ..ext.github import fork_status
            print(fork_status(self.app.pargs.url))
        elif self.app.pargs.action=='contrib':
            from ..ext.github import find_contributors
            print(find_contributors(self.app.pargs.url))
        elif self.app.pargs.action=='diff':
            from ..ext.github import dir_diff
            pp(dir_diff(self.app.pargs.url))
        elif self.app.pargs.action=='branches':
            from ..ext.github import find_branches
            
            if self.app.pargs.remote is None: remote = True
            else: remote = self.app.pargs.remote == 'True'
            
            remove = self.app.pargs.__dict__.get('remove', True)
            print(find_branches(self.app.pargs.url, remote, remove))
        elif self.app.pargs.action=='secrets':
            from ..ext.github import show_secrets, add_secrets, delete_secret
            
            if not self.app.pargs.url:
                print("Error: GitHub repository URL is required")
                return
                
            # Determine case preservation
            preserve_case = self.app.pargs.preserve_case and not self.app.pargs.uppercase
                
            if self.app.pargs.delete:
                if not self.app.pargs.name:
                    print("Error: Secret name (-n/--name) is required for delete operation")
                    return
                    
                if not self.app.pargs.force:
                    confirm = input(f"Are you sure you want to delete secret '{self.app.pargs.name}'? [y/N] ")
                    if confirm.lower() != 'y':
                        print("Delete operation cancelled")
                        return
                        
                delete_secret(self.app.pargs.url, self.app.pargs.name)
            elif self.app.pargs.config:
                # Add secrets from config file
                name_list = self.app.pargs.name_list.split(',') if self.app.pargs.name_list else None
                add_secrets(self.app.pargs.url, config_path=self.app.pargs.config, 
                          name_list=name_list, preserve_case=preserve_case)
            elif self.app.pargs.name and self.app.pargs.value:
                # Add/update single secret
                add_secrets(self.app.pargs.url, secret_name=self.app.pargs.name, 
                          secret_value=self.app.pargs.value, preserve_case=preserve_case)
            else:
                # Show all secrets
                show_secrets(self.app.pargs.url)
        elif self.app.pargs.action=='summary':
            from ..ext.github import git_summary
            filter_files = self.app.pargs.filter_files.split(',') if self.app.pargs.filter_files else None
            print(git_summary(self.app.pargs.url or '.', filter_files))

    # create notes that are organized into project folders and are stored in md files
    @ex(
        help='Create notes that are organized into project folders and are stored in md files',
        arguments=[
            (['action'],{
                "help" : "One of {add (screenshot), ls (notes), mk (project), rm (project), fin (note)}",
                "action": "store"
            }),
            (['-t'],{
                "help": "Text of the note",
                "action": "store"
            }),
            (['-p'],{
                "help" : "Project id. If not given, grabs the first one.",
                "action" : 'store'
            }),
            (['-i'],{
                "help" : "Id of the finished note",
                "action": "store"
            }),
            (['-ws'],{
                "help": "Workspace name (e.g. Daily) otherwiwise grabs the first one",
                "action": "store"
            })
        ]
    )
    def nt(self):
        from ..ext.notes import Note
        note = Note(self.app.pargs.p, )
        if self.app.pargs.action=='add':
            note.add_attachment(self.app.pargs.p)
        elif self.app.pargs.action=='ls':
            note.ls(self.app.pargs.p, self.app.pargs.ws)
        elif self.app.pargs.action=='mk':
            note.create_project(self.app.pargs.p, self.app.pargs.t)
        elif self.app.pargs.action=='up':
            note.up(self.app.pargs.i, self.app.pargs.t, self.app.pargs.ws)
        else:
            print("Try one of {add, ls, dn}")

    # create notes that are organized into project folders and are stored in md files
    

    @ex(
        help='Manage TODOs using Asana',
        arguments=[
            (['action'],{
                "help" : "One of {add, ls, dn, lsws}",
                "action": "store"
            }),
            (['-t'],{
                "help": "Text of the TODO",
                "action": "store"
            }),
            (['-l'],{
                "help": "Length of time in days this is expected to take",
                "action": "store"
            }),
            (['-p'],{
                "help" : "Project id. If not given, grabs 1203472445329580 (Saker).",
                "action" : 'store'
            }),
            (['-i'],{
                "help" : "Id of the finished task",
                "action": "store"
            }),
            (['-ws'],{
                "help": "Workspace gid (long numeric) otherwiwise grabs the first one",
                "action": "store"
            }),
            (['-f'],{
                "help" : "Filter TODOs for ls",
                "action": "store"
            })
        ]
    )
    def td(self):
        from ..ext.asana import add_todo, asana_list_todos, done_todo,  \
            fix_past_due, asana_list_workspaces
        project = self.app.pargs.p or "1203472445329580"

        if self.app.pargs.action=='add':
            add_todo(self.app.pargs.t, self.app.pargs.l, self.app.pargs.ws, project)
        elif self.app.pargs.action=='ls':
            asana_list_todos(
                self.app.pargs.p,
                self.app.pargs.f,)
        elif self.app.pargs.action=='dn':
            done_todo(self.app.pargs.i)
        elif self.app.pargs.action=='fix':
            fix_past_due(self.app.pargs.p)
        elif self.app.pargs.action=='lsws':
            asana_list_workspaces(self.app.pargs.f)

        else:
            raise NotImplemented("Action must be one of {add, ls, dn, lsws}")

    @ex(
        help='(Deprecated) Manage TODOs using Google Keep',
        arguments=[
            (['action'],{
                "help" : "One of {add, ls, dn}",
                "action": "store"
            }),
            (['-t'],{
                "help": "Text of the TODO",
                "action": "store"
            }),
            (['-l'],{
                "help": "Length of time in hours this is expected to take",
                "action": "store"
            }),
            (['-p'],{
                "help" : "Project name. One of {DA, SL}",
                "action" : 'store'
            }),
            (['-i'],{
                "help" : "Id of the finished task",
                "action": "store"
            }),
            (['-f'],{
                "help" : "Filter TODOs for ls",
                "action": "store"
            })
        ]
    )
    def gkeep(self):
        from ..ext.gkeep import add_todo, list_todos, done_todo
        project = self.app.pargs.p or 'SL'

        if self.app.pargs.action=='add':
            add_todo(self.app.pargs.t, self.app.pargs.l, self.app.pargs.p)
        elif self.app.pargs.action=='ls':
            list_todos(self.app.pargs.f or True,
                       self.app.pargs.p)
        elif self.app.pargs.action=='dn':
            done_todo(self.app.pargs.i)

        else:
            raise NotImplemented("Action must be one of {add, ls, dn}")
        
    @ex(
        help="Manage outlook calendar",
        arguments=[
            (['action'],{
                "help" : "One of {add, ls, del}",
                "action": "store"
            }),
            (['-t'],{
                "help": "Title of the event",
                "action": "store"
            }),
            (['-i','--invite'],{
                "help": "Invitee email(s) separated by commas",
                "action": "store"
            }),
            (['-s','--start'],{
                "help": "Start time of the event",
                "action": "store"
            }),
            (['-d','--duration'],{
                "help": "Duration of the event in minutes",
                "action": "store"
            })
        ]
    )
    def ms(self):
        # extract arguments and pass to the appropriate function
        invitees = self.app.pargs.__dict__.get('invite', None) or self.app.pargs.__dict__.get('i', None)
        start = self.app.pargs.__dict__.get('start', None) or self.app.pargs.__dict__.get('s', None)
        duration = self.app.pargs.__dict__.get('duration', None) or self.app.pargs.__dict__.get('d', None)
        
        from ..ext.ms_outlook import create_meeting, list_events, delete_event
        if self.app.pargs.action=='add':
            create_meeting(self.app.pargs.t, invitees, start, duration)
        elif self.app.pargs.action=='ls':
            list_events()
        elif self.app.pargs.action=='del':
            delete_event(self.app.pargs.i)
        else:
            raise NotImplemented("Action must be one of {add, ls, del}")
    
         
    # TODO: implement this as command
    # likely easiest as just alias dt='python -m dt.main'
    # echo "alias dt='python -m dt.main'" > ~/.bashrc; source ~/.basshrc
    # local / mac version and EC2 / remote version

    @ex(
        help='(WIP/Pre-Alpha) Execute a Python command across all files in current dir.',
        arguments=[
            (['command'],{
                "help": "what python command to run",
                "action": "store"
            }),
            (['-f'],{
                "help" : "filter all files in in this directory and below by this expression.",
                "action" : "store"
            })
        ]
    )
    def py(self):
        from ..ext.python_exec import execute
        execute(self.app.pargs.command, self.app.pargs.f)

    @ex(
        help="YouTube video operations (download, analyze, transcribe)",
        arguments=[
            (['url'],{
                "help": "YouTube URL to process",
                "action": "store"
            }),
            (['-s', '--start'],{
                "help": "Start time in format HH:MM:SS",
                "action": "store"
            }),
            (['-e', '--end'],{
                "help": "End time in format HH:MM:SS",
                "action": "store"
            }),
            (['-o', '--output'],{
                "help": "Output file for analysis/transcript",
                "action": "store"
            }),
            (['-m', '--model'],{
                "help": "Which OpenAI model to use for analysis (defaults to gpt-4o)",
                "action": "store"
            }),
            (['-t', '--transcribe'],{
                "help": "Transcribe the video instead of analyzing frames",
                "action": "store_true"
            }),
            (['-d', '--download-only'],{
                "help": "Only download the video without analysis",
                "action": "store_true"
            })
        ]
    )
    def yt(self):
        from ..ext.youtube import download_youtube_video, analyze_frames, transcribe_video
        import os # Ensure os is imported
        
        # Check for mutually exclusive flags
        if self.app.pargs.download_only and self.app.pargs.transcribe:
            print("Error: Cannot use --download-only (-d) and --transcribe (-t) flags together.")
            return

        url = self.app.pargs.url.replace('\\', '')  # Get URL from positional arg
        output_file = self.app.pargs.output
        start_time = self.app.pargs.start
        end_time = self.app.pargs.end
        model = self.app.pargs.model or 'gpt-4o'
        
        print("\nProcessing YouTube video...")
        print(f"URL: {url}")
        if start_time or end_time: # Adjusted condition slightly
            time_range_str = f"{start_time or 'start'} to {end_time or 'end'}"
            print(f"Time range: {time_range_str}")
        
        if self.app.pargs.download_only:
            try: # Added try/except block for better error handling
                video_path, temp_dir = download_youtube_video(url, start_time, end_time)
                
                # Determine final video path
                final_video_path = None
                if output_file:
                    import shutil
                    # Ensure target directory exists if specified
                    output_dir = os.path.dirname(output_file)
                    if output_dir:
                        os.makedirs(output_dir, exist_ok=True)
                    
                    # Ensure the final path has an .mp4 extension
                    base_name, _ = os.path.splitext(os.path.basename(output_file))
                    final_video_path = os.path.join(output_dir, base_name + '.mp4')
                    
                    shutil.move(video_path, final_video_path)
                    shutil.rmtree(temp_dir)
                    print(f"\nVideo saved to: {final_video_path}")
                else:
                    # If no output file specified, keep temp path (will be deleted on exit)
                    final_video_path = video_path 
                    print(f"\nVideo downloaded to: {final_video_path}")
                    print("Warning: Temporary file will be deleted when the program exits")
            except Exception as e:
                print(f"\nError during download: {e}")
                # Clean up temp dir on error if it exists
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            return
            
        try: # Added try/except block
            if self.app.pargs.transcribe:
                model = self.app.pargs.model or 'whisper-1'
                print(f"Transcribing with model: {model}")
                result = transcribe_video(url, model, start_time, end_time)
            else:
                print(f"Analyzing frames with model: {model}")
                result = analyze_frames(url, start_time, end_time, model)

            if result: # Check if result is not None (e.g., on error)
                if output_file:
                    # Ensure target directory exists if specified
                    output_dir = os.path.dirname(output_file)
                    if output_dir:
                        os.makedirs(output_dir, exist_ok=True)
                    with open(output_file, 'w') as f:
                        f.write(result)
                    print(f"\nOutput saved to: {output_file}")
                else:
                    print("\nResult:")
                    print(result)
        except Exception as e:
            print(f"\nError during processing: {e}")

    @ex(
        help="Convert YouTube video segment to high-quality GIF",
        arguments=[
            (['url'],{
                "help": "YouTube URL to process",
                "action": "store"
            }),
            (['-s', '--start'],{
                "help": "Start time in format HH:MM:SS",
                "action": "store"
            }),
            (['-e', '--end'],{
                "help": "End time in format HH:MM:SS",
                "action": "store"
            }),
            (['-o', '--output'],{
                "help": "Output GIF file path",
                "action": "store"
            }),
            (['-f', '--fps'],{
                "help": "Frames per second for the GIF (default: 10)",
                "action": "store",
                "type": int,
                "default": 10
            }),
            (['-S', '--speed'],{
                "help": "Playback speed multiplier (0.25 to 2.0, default: 1.0)",
                "action": "store",
                "type": float,
                "default": 1.0
            }),
            (['--burn-subs'], {
                "help": "Burn subtitles onto the GIF using OpenAI Whisper (requires OPENAI_API_KEY)",
                "action": "store_true"
            })
        ]
    )
    def yt2gif(self):
        from ..ext.youtube import download_youtube_video, convert_to_gif
        import os, shutil # Ensure os and shutil are imported

        url = self.app.pargs.url.replace('\\\\', '')  # Remove escape characters
        output_file = self.app.pargs.output or 'output.gif'
        start_time = self.app.pargs.start
        end_time = self.app.pargs.end
        fps = self.app.pargs.fps
        speed = self.app.pargs.speed
        burn_subtitles = self.app.pargs.burn_subs # Get the new flag value

        print("\nConverting YouTube video to GIF...")
        print(f"URL: {url}")
        if start_time or end_time: # Use 'or' to print if either is set
            time_range_str = f"{start_time or 'start'} to {end_time or 'end'}"
            print(f"Time range: {time_range_str}")
        print(f"Output: {output_file}")
        print(f"FPS: {fps}")
        print(f"Speed: {speed}x")
        if burn_subtitles:
            print("Subtitle Burning: Enabled (using Whisper)")

        temp_dir = None # Initialize temp_dir
        try:
            # Pass burn_subtitles to download function to ensure audio is included
            video_path, temp_dir = download_youtube_video(url, start_time, end_time, ensure_audio=burn_subtitles)
            
            # Ensure output directory exists for the final GIF
            final_output_dir = os.path.dirname(output_file)
            if final_output_dir:
                os.makedirs(final_output_dir, exist_ok=True)
                
            # Determine output format based on file extension
            output_ext = os.path.splitext(output_file)[1].lower()
            is_video_output = output_ext in ['.mp4', '.mkv', '.mov', '.avi']
            output_type = "Video" if is_video_output else "GIF"
                
            print("\nConverting to {}...".format(output_type))
            
            # Pass burn_subtitles flag AND time arguments to the conversion function
            if convert_to_gif(video_path, output_file, fps, speed, 
                              burn_subtitles=burn_subtitles, 
                              start_time=start_time, 
                              end_time=end_time):
                print(f"\n{output_type} saved successfully to: {output_file}")
            else:
                print("\nError: GIF conversion failed")

        except Exception as e:
            print(f"\nError: {str(e)}")
        finally:
            # Ensure temp_dir is removed, even if there was an error  
            if temp_dir and os.path.exists(temp_dir):
                print(f"Cleaning up temporary directory: {temp_dir}")
                shutil.rmtree(temp_dir)

    @ex(
        help="Generate AI commit message from git diff and commit",
        arguments=[]
    )
    def ci(self):
        from ..ext.openai_helper import client
        import subprocess
        
        # Get git diff
        try:
            diff = subprocess.check_output(['git', 'diff', '--cached'], text=True)
            if not diff.strip():
                diff = subprocess.check_output(['git', 'diff'], text=True)
            if not diff.strip():
                print("No changes to commit")
                return
        except subprocess.CalledProcessError:
            print("Error: Not a git repository or git command failed")
            return
            
        # Get commit message from OpenAI
        try:
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{"role": "user", "content": f"Summarize these git changes in <200 chars for commit message:\n{diff}"}],
                max_tokens=100
            )
            msg = response.choices[0].message.content.strip()
            print(f"Commit message: {msg}")
            
            # Commit with the message
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', msg], check=True)
            print("Committed successfully")
        except Exception as e:
            print(f"Error: {e}")