#/bin/python
'''
TODO: fix

botocore.exceptions.ClientError: An error occurred (InvalidPermission.Duplicate) 
when calling the AuthorizeSecurityGroupIngress operation: the specified rule "peer: 86.16.93.195/32, TCP, from port: 8501, 
to port: 8501, ALLOW" already exists

  File "/Users/jlangr/code/data-toolkit/dt/controllers/base.py", line 101, in sg
    update_sg_to_ip(sg_name=sg_name, profile=profile,
  File "/Users/jlangr/code/data-toolkit/dt/ext/aws_sg.py", line 111, in update_sg_to_ip
    data = ec2.authorize_security_group_ingress(
'''

import boto3
import pandas as pd
import os 
import pprint

try:
    term_wdith = os.get_terminal_size().columns
except OSError:
    term_wdith = 70

# pd.set_option('display.max_colwidth',term_wdith - 40)
pd.set_option('display.max_colwidth',30)

def get_public_ip():
    from urllib.request import urlopen
    import re
    data = str(urlopen('http://checkip.dyndns.com/').read())
    # data = '<html><head><title>Current IP Check</title></head><body>Current IP Address: 65.96.168.198</body></html>\r\n'
    return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)

def get_sg(profile: str, sg_id: str = None, sg_name: str = None, region='eu-west-1'):
    ec2 = boto3.session.Session(profile_name=profile, region_name=region).client('ec2')
    
    if sg_id:
        response = ec2.describe_security_groups(GroupIds=[sg_id])
    elif sg_name:
        response = ec2.describe_security_groups(GroupNames=[sg_name])
    else:
        raise ValueError("Either sg_id or sg_name must be provided")
    
    if not response['SecurityGroups']:
        raise ValueError(f"No security group found with the given {'ID' if sg_id else 'name'}")
    
    sg_info = response['SecurityGroups'][0]
    
    # Format the security group information
    formatted_sg = {
        'GroupName': sg_info['GroupName'],
        'GroupId': sg_info['GroupId'],
        'Description': sg_info['Description'],
        'VpcId': sg_info['VpcId'],
        'InboundRules': [],
        'OutboundRules': []
    }

    # Format inbound rules
    for rule in sg_info['IpPermissions']:
        formatted_rule = {
            'IpProtocol': rule.get('IpProtocol', 'All'),
            'FromPort': rule.get('FromPort', 'All'),
            'ToPort': rule.get('ToPort', 'All'),
            'IpRanges': [ip_range.get('CidrIp', 'Any') for ip_range in rule.get('IpRanges', [])],
            'UserIdGroupPairs': [group.get('GroupId', 'Unknown') for group in rule.get('UserIdGroupPairs', [])]
        }
        formatted_sg['InboundRules'].append(formatted_rule)

    # Format outbound rules
    for rule in sg_info['IpPermissionsEgress']:
        formatted_rule = {
            'IpProtocol': rule.get('IpProtocol', 'All'),
            'FromPort': rule.get('FromPort', 'All'),
            'ToPort': rule.get('ToPort', 'All'),
            'IpRanges': [ip_range.get('CidrIp', 'Any') for ip_range in rule.get('IpRanges', [])],
            'UserIdGroupPairs': [group.get('GroupId', 'Unknown') for group in rule.get('UserIdGroupPairs', [])]
        }
        formatted_sg['OutboundRules'].append(formatted_rule)

    # Use pprint to display the formatted security group information
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(formatted_sg)

    return formatted_sg

def check_if_exists(ip_range: dict, descriptions: list):
    try:
        return ip_range.get('Description') in descriptions
    except KeyError:
        return False

def update_sg_to_ip(sg_name=None, sg_id=None, ports=None, profile='default',
                    messages='', region='eu-west-1', ip=None):
    import boto3

    if ip is None:
        ip = f"{get_public_ip()}/32"
    elif ip.lower() == 'anywhere':
        ip = '0.0.0.0/0'

    ec2 = boto3.session.Session(profile_name=profile, region_name=region).client('ec2')

    if sg_id:
        target_sg_dict = get_sg(profile=profile, sg_id=sg_id, region=region)
    elif sg_name:
        target_sg_dict = get_sg(profile=profile, sg_name=sg_name, region=region)
    else:
        raise ValueError("Either sg_name or sg_id must be provided")

    ec2_res = boto3.session.Session(profile_name=profile, region_name=region).resource('ec2')
    sg_res = ec2_res.SecurityGroup(target_sg_dict['GroupId'])

    # determine what the new sg rules should be either default or custom
    if messages == '':
        print('Warning: messages are empty. Using default descriptions.')
        descriptions = {
            22: 'SSH',
            80: 'HTTP',
            443: 'HTTPS',
            8888: 'Jupyter',
            8501: 'Streamlit',
            8889: 'Jupyter2',
            5432: 'Postgres'
        }
        if ports is None:
            ports = list(descriptions.keys())
    else:
        items = [i for i in messages.split(',')]
        descriptions = {int(k.split(':')[0]): k.split(':')[1] for k in items}
        ports = [int(i.split(':')[0]) for i in items]

    # Create a set of ports for efficient lookup
    ports_set = set(ports)

    # Create target_ports list based on existing permissions
    target_ports = [any(p in ports_set for p in range(s.get('FromPort', 0), s.get('ToPort', 0) + 1))
                    for s in sg_res.ip_permissions if 'FromPort' in s and 'ToPort' in s]

    # Ensure target_ports has at least as many elements as ports
    target_ports.extend([False] * (len(ports) - len(target_ports)))

    permissions_to_revoke = []
    for i, permission in enumerate(sg_res.ip_permissions):
        if i < len(target_ports) and target_ports[i]:
            ip_ranges_to_revoke = [s for s in permission.get('IpRanges', []) if check_if_exists(s, list(descriptions.values()))]
            if ip_ranges_to_revoke:
                permissions_to_revoke.append({
                    **permission,
                    'IpRanges': ip_ranges_to_revoke
                })

    # Removes all relevant permissions from this group
    if permissions_to_revoke:
        sg_res.revoke_ingress(IpPermissions=permissions_to_revoke)
        print(f'Removed permissions {permissions_to_revoke}')
    else:
        print('No permissions to revoke. Skipping.')

    # assign new rules   
    ip_perms = [{
        'IpProtocol': 'tcp',
        'FromPort': port,
        'ToPort': port,
        'IpRanges': [{'CidrIp': ip, 'Description': descriptions[port]}]
    } for port in ports]
    
    for perm in ip_perms:
        try:
            ec2.authorize_security_group_ingress(
                GroupId=target_sg_dict['GroupId'],
                IpPermissions=[perm]
            )
            print(f'Ingress Successfully Set {perm} to {sg_name or sg_id}')
        except ec2.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                print(f"Warning: Rule already exists for port {perm['FromPort']}. Skipping.")
            else:
                print(f"Error setting rule for port {perm['FromPort']}: {e}")

    # Refresh the security group to get updated rules
    updated_sg = get_sg(profile=profile, sg_id=target_sg_dict['GroupId'], region=region)
    print("Updated Security Group:")
    pprint.pprint(updated_sg)

# lists all security groups
def list_security_groups(region: str = 'eu-west-1', profile: str = 'default'):
    # define a boto3 client with a region eu-est
    boto3.setup_default_session(profile_name=profile)
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_security_groups()
    security_group_df = pd.DataFrame(response['SecurityGroups'])

    # extract keys from Tags column
    # [ x for x in df.Tags if not np.all(pd.isna(x)) ] 

    # generate a mask for terms that have FILTER_TERMS in them
    FILTER_TERMS = ['LIW']
    mask = security_group_df.Description.apply(lambda x: any(term in x for term in FILTER_TERMS))
    security_group_df = security_group_df[~mask]

    # display all columns except FILTER_COLS
    FILTER_COLS = ['VpcId', 'Tags','OwnerId']
    security_group_df = security_group_df[security_group_df.columns.difference(FILTER_COLS)]

    # create an Ingress dataframe by filtering on IpPermissions not empty
    df_ingress = security_group_df[security_group_df.IpPermissions.notnull()]
    ip_permissions_df = pd.DataFrame.from_dict([x[0] for x in df_ingress.IpPermissions.values])
    
    df_ingress = df_ingress.reset_index().drop('index',axis=1)
    
    viewable_df = pd.concat([ip_permissions_df,df_ingress],axis=1).drop(['Ipv6Ranges','IpPermissions'],axis=1)
    # viewable_df.Description = viewable_df.Description.str[:30]

    # reorders columns 
    order = "GroupName FromPort IpProtocol ToPort UserIdGroupPairs PrefixListIds Description IpRanges IpPermissionsEgress GroupId".split()
    viewable_df = viewable_df[order]

    return viewable_df

def sg_ls(region, profile, show_all=False):
    from tabulate import tabulate
    
    boto3.setup_default_session(profile_name=profile)
    ec2 = boto3.client('ec2', region_name=region)
    
    if show_all:
        response = ec2.describe_security_groups()
    else:
        instances = ec2.describe_instances()
        sg_ids = set()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                for sg in instance['SecurityGroups']:
                    sg_ids.add(sg['GroupId'])
        response = ec2.describe_security_groups(GroupIds=list(sg_ids))

    security_groups = response['SecurityGroups']

    # Filter out unwanted security groups
    FILTER_TERMS = ['LIW']
    security_groups = [sg for sg in security_groups if not any(term in sg['Description'] for term in FILTER_TERMS)]

    # Create table data
    table_data = []
    headers = ['Group Name', 'Group ID', 'Description', 'Inbound Rules', 'Outbound Rules']

    for sg in security_groups:
        # Format inbound rules organized by IP/CIDR
        inbound_rules = []
        for rule in sg['IpPermissions']:
            protocol = rule.get('IpProtocol', 'All')
            from_port = rule.get('FromPort', 'All')
            to_port = rule.get('ToPort', 'All')
            
            for ip_range in rule.get('IpRanges', []):
                inbound_rules.append(f"{ip_range.get('CidrIp', 'Any')} ({protocol}) {from_port}-{to_port}")
            
            for group_pair in rule.get('UserIdGroupPairs', []):
                inbound_rules.append(f"Group: {group_pair.get('GroupId', 'Unknown')} ({protocol}) {from_port}-{to_port}")

        # Format outbound rules organized by IP/CIDR
        outbound_rules = []
        for rule in sg['IpPermissionsEgress']:
            protocol = rule.get('IpProtocol', 'All')
            if protocol == '-1':
                outbound_rules.append("All traffic")
            else:
                from_port = rule.get('FromPort', 'All')
                to_port = rule.get('ToPort', 'All')
                for ip_range in rule.get('IpRanges', []):
                    outbound_rules.append(f"{ip_range.get('CidrIp', 'Any')} ({protocol}) {from_port}-{to_port}")

        # Sort rules by IP/CIDR for better organization
        inbound_rules.sort(key=lambda x: x.split()[0] if x.split() else '')
        outbound_rules.sort(key=lambda x: x.split()[0] if x.split() else '')
        
        # Show all rules without truncation
        inbound_display = '\n'.join(inbound_rules) if inbound_rules else 'None'
        outbound_display = '\n'.join(outbound_rules) if outbound_rules else 'None'

        # Add row to table data
        table_data.append([
            sg['GroupName'],
            sg['GroupId'],
            sg['Description'][:35] + ('...' if len(sg['Description']) > 35 else ''),
            inbound_display if inbound_rules else 'None',
            outbound_display if outbound_rules else 'None'
        ])

    # Print formatted table with better formatting
    print(tabulate(table_data, headers=headers, tablefmt='fancy_grid', stralign='left', maxcolwidths=[20, 20, 40, 50, 30]))
    return table_data

