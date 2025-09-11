import click

from . import backup
from . import develop
from . import status
from . import inspect
from . import reset
from . import update


@click.group()
def main():
    pass


main.add_command(backup.encrypted_instance_backup)
main.add_command(develop.develop)
main.add_command(inspect.inspect)
main.add_command(status.status)
main.add_command(reset.reset)
main.add_command(update.update)
