# ML & data helper code!
Jakub Langr (c) 2021

This is a CLI utility for speeding up basic Data Engineering/Data Science tasks

```
usage: dt [-h] [-d] [-q] [-v]
          {cai,config,ec2,gcp,gh,hist,load,monitor,nf,py,run,s3,sftp,sg,ssh,td,viz}
          ...

ML & data helper code!

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           full application debug mode
  -q, --quiet           suppress all console output
  -v, --version         show program's version number and exit

sub-commands:
  {cai,config,ec2,gcp,gh,hist,load,monitor,nf,py,run,s3,sftp,sg,ssh,td,viz}
    cai                 Ops with Codex AI from OpenAI.
    config              Operations with config.
    ec2                 AWS EC2 helper commands.
    gcp                 GCP VM Instances helper commands.These are currently
                        in alpha and some may not work
    gh                  All Github related operations
    hist                Operations on CLI hist
    load                Appends defaults: from zshrc.txt to ~/.bashrc or
                        ~/.zshrc or tmux conf
    monitor             Monitor lack of GPU activity. When there is none, runs
                        -job
    nf                  Displays the number of files
    py                  (WIP/Pre-Alpha) Execute a Python command across all
                        files in current dir.
    run                 Operations with snippets
    s3                  Operations with s3 buckets
    sftp                Operations to easily work with remote servers /
                        devices
    sg                  AWS Security Groups helper functions
    ssh                 Operations on the SSH config
    td                  Manage TODOs using Google Keep
    viz                 Basic viz using streamlit for image comparisons

Usage: dt command [args] [kwargs]
```
The screen above can be called using:
```
dt -h
``` 

For example, to run to list the running ec2 isntances run 

```
dt ec2 ls --profile <profile>
```

## Installation

```
$ pip install data-toolkit
```

## Tips and examples

Personally I find most helpful the following commands:
```
dt ec2 ls
```
Shows running EC2 instances with a range of parameters depending on the width of your terminal.
```
dt sg ls
```
Shows an overview of all security groups in the current region.
```
dt sg show
```
Shows detail of either all or one security group in the current region.
```
dt ssh update
```
Updates the SSH config with with the IP addresses of the running EC2 instances (matches them by name/tag).

When I'm travelling I like to use the following commands:
```
dt sg update -n <sg_name>  -m "22:jakub 4g"
```
Which updates the `<sg_name>` security group to allow SSH from the current IP address and port 22 and sets the description to "jakub 4g".

**Hope this helps!**
## Development

This project includes a number of helpers in the `Makefile` to streamline common development tasks.

### Environment Setup

The following demonstrates setting up and working with a development environment:

```
### create a virtualenv for development

$ make virtualenv

$ source env/bin/activate


### run dt cli application

$ dt --help


### run pytest / coverage

$ make test
```
