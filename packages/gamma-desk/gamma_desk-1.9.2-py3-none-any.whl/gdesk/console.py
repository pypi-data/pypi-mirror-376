"""
Gamma Desk interface to the DOS console
"""
import sys
import os
import logging
import argparse
from pathlib import Path

from . import __release__, refer_shell_instance
from . import configure, config, DOC_HTML, PROGNAME
from .core import conf

logger = logging.getLogger(__name__)

boot_handler = logging.StreamHandler(sys.stdout)
boot_handler.set_name('boot')
logging.root.addHandler(boot_handler)

MODNAME = '.'.join(globals()['__name__'].split('.')[:-1])
PATH_SEPERATOR = ';' if sys.platform == 'win32' else ':'

HEADER = f"{PROGNAME} {__release__}"
HEADER += '\n' + len(HEADER) * '=' + '\n'

HEADER += DOC_HTML + '\n'

EPILOG = f"""\
Examples
--------

{MODNAME} -i init_file.py
{MODNAME} -c config_file.???
"""

def argparser():
    """
    Make the ArgumentParser instance
    """
    parser = argparse.ArgumentParser(description=HEADER, prog=f'python -m {MODNAME}',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EPILOG)

    parser.add_argument("-c", "--config_file", help="Use this configuration file")
    parser.add_argument("-i", "--init_file", help="Run this init file in console 1")
    parser.add_argument("-d", "--debug", action='store_true', help="Set logging level to debug")
    parser.add_argument("pictures", nargs='*', help="Image file to load")

    return parser


def argexec(argv=None, **config_kwargs):
    """
    Configure and start the eventloop
    """
    bootpath = Path('.').resolve()
    print(f'Bootpath: {bootpath}')
    parser = argparser()
    args = parser.parse_args(argv)

    if args.debug:
        config_kwargs['logging_level'] = 'DEBUG'
        logging.root.setLevel(config_kwargs['logging_level'])

    config_kwargs['qapp'] = True

    if args.config_file:
        config_kwargs['path_config_files'] = [args.config_file]

    if args.init_file:
        config_kwargs['init_file'] = args.init_file

    configure(**config_kwargs)

    # Configure has to be done before import other modules
    from .core.shellmod import Shell
    shell = Shell()
    refer_shell_instance(shell)
    
    watcher_ports =  shell.get_watcher_ports()
    
    pics = [bootpath / p for p in args.pictures]
    
    if len(watcher_ports) > 0:
        if args.pictures:
            from gdesk.core.watcher import CommandClient
            cmd = {'cmd': 'open_images', 'args': pics}
            cmdclient = CommandClient(watcher_ports[0], 'localhost')
            cmdclient.send(cmd)
            return

    from .gcore.guiapp import eventloop    
    eventloop(shell, init_file=config['init_file'], pictures=pics)

    return shell


def run_as_child(console_args, config_kwargs, config_objects):
    """
    Top level function to start as child process
    """
    #Note that auto unpickling of received arguments can have caused a configarion to be execed
    #The configuration was triggered by the Process code on decode this function pointer
    conf.config_objects.update(config_objects)

    #Allow reconfiguring
    conf.config.clear()
    conf.configured = False

    print(config_kwargs)
    argexec(console_args, **config_kwargs)


def is_imported_by_child_process():
    """
    Detect whenever this module is imported by multiprocessing.spawn
    """
    frame = sys._getframe()

    while not frame is None:
        module_name = frame.f_globals['__name__']
        if module_name == 'multiprocessing.spawn':
            return True
        frame = frame.f_back

    return False
    
def restart():
    # in case of started with -m gdesk and extra arguments
    # sys.argv:  # ['c:\\users\\thomas.cools\\projects\\gamma-desk\\git\\gdesk\\__main__.py', '-c', '..\\setup\\gdconf.json']
    # in case of started with \scripts\gdesk.exe and extra arguments
    # ['C:\\Users\\thomas.cools\\AppData\\Local\\Programs\\Python\\venv\\os10a10\\Scripts\\gdesk', '-c', '../setup/gdconf.json']
    #    
    from . import shell
    extra_arguments = sys.argv[1:]
    shell.logdir.release_lock_file()
    os.execlp(sys.executable, 'python', '-m', 'gdesk', *extra_arguments)        


if is_imported_by_child_process():
    configure(qapp=True)
