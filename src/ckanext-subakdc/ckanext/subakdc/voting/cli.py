import click

import ckanext.subakdc.voting.utils as utils


@click.group()
def voting():
    pass


@click.command()
def initdb():
    utils.initdb()
    click.secho("UserDatasetVotes table is setup", fg="green")


voting.add_command(initdb)


def get_commands():
    return [voting]
