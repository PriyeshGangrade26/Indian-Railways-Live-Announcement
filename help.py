from __future__ import absolute_import
from pip._internal.basecommand import SUCCESS, Command
from pip._internal.exceptions import CommandError
class HelpCommand(Command):
    name = 'help'
    usage = """
      %prog <command>"""
    summary = 'Show help for commands.'
    ignore_require_venv = True
    def run(self, options, args):
        from pip._internal.commands import commands_dict, get_similar_commands
        try:
            cmd_name = args[0]
        except IndexError:
            return SUCCESS
        if cmd_name not in commands_dict:
            guess = get_similar_commands(cmd_name)
            msg = ['unknown command "%s"' % cmd_name]
            if guess:
                msg.append('maybe you meant "%s"' % guess)
            raise CommandError(' - '.join(msg))
        command = commands_dict[cmd_name]()
        command.parser.print_help()
        return SUCCESS