from ast import Raise
import click

from ckanext.qa import tasks
from ckanext.qa.qa import QaTaskRunner

@click.group()
def qa():
    pass

@click.command()
@click.argument('task', required=False)
def run(task):
    """
    Runs all given tasks (or all tasks if none given) over all packages
    
    Run using `ckan qa run {task_name}` in the CKAN container
    """
    if not task:
        runner = QaTaskRunner(tasks.values())
    else:
        runner = QaTaskRunner([tasks[task]])
        
    runner.run()

qa.add_command(run)

def get_commands():
    return [qa]