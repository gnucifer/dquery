#!/usr/bin/env python

#if sys.stdout.isatty(): + turn off pipe detection
# + colors
import sys
import cli.app #TODO
import fnmatch
import yaml
#from cli.profiler import Profiler
from lib import *

#import inspect
#TODO: rename module-usage to usage, or perhaps present tense, using?
from colorama import init
init()
from dquery import settings as dquery_settings

__all__ = ["dquery_application", "dquery_command", "dQueryCommand"]

class DqueryCommandLineMixin(cli.app.CommandLineMixin):

    ## Customization/plugin methods, allows for mixins to provide extra
    ## functionallity by compasing a DqueryCommandLine app

    def process_args(self):
        pass

    def setup_args(self):
        pass

    def parse_args(self):
        pass


    def _load_subcommand_modules(self):
        #TODO: helper function, get command-plugin directories, error handling
        import imp
        modules = []
        script_dir = os.path.dirname(os.path.realpath(__file__))
        subcommand_directories = [os.path.join(script_dir, 'commands')]
        subcommand_files = [
            os.path.join(path, basename)
                for path in subcommand_directories
                    for basename in os.listdir(path)
                        if fnmatch.fnmatch(basename,'*_dquery_command.py')]
        for filename in subcommand_files:
            name = os.path.splitext(os.path.basename(filename))[0]
            try:
                f, pathname, description = imp.find_module(
                        name,
                        [os.path.dirname(filename)])
                module = imp.load_module(name, f, pathname, description)
                modules.append(module)
            except Exception as e:
                print e
                exit()
        return modules
    """
    def _extract_subcommands(module):
        # check if is instance?
        subcommands = []
        if hasattr(module, '__dquery_commands__'):
            for name in module.__dquery_commands__:
                try:
                    subcommands.append(getattr(module, name))
                except AttributeError:
                    print 'Class ' + name + \
                            ' not found in module ' + module.__name__
                    exit()
        #TODO: not implemented yet
        #magic_suffix = 'QueryCommand'
        #if(hasattr(module, magic_classname)):
         #   return [getattr(
        #TODO: warning if no commands found?

    def _load_subcommands():
        subcommands = []
        for module in self._load_subcommand_modules():
            for subcommand in self._extract_subcommands():
                subcommands.append(subcommand)
        return subcommands
    """

    def setup(self):
        super(DqueryCommandLineMixin, self).setup()

        self.argparser.add_argument('-r', '--root',
                dest='drupal_root',
                type=str,
                default=os.getcwd(),
                help='Drupal root directory to use'
                )

        self.argparser.add_argument('--relative',
                dest='relative_paths',
                action='store_true',
                help='Output paths relative to drupal root directory'
                )

        self.argparser.add_argument('-v',
                dest='verbose',
                action='store_true'
                )

        """
        self.argparser.add_argument('-p', '--pipe',
                dest='pipe',
                action='store_true'
                ) # this can be auto-detected? Yes, but that is a bad idea
        """
        #TODO: mutually exlusive with sub-commands?
        self.argparser.add_argument('--no-cache',
                dest='use_cache',
                action='store_false',
                help='Do not use the internal DQuery cache'
                )

        self.argparser.add_argument(
                '--clear-cache',
                dest='clear_cache',
                action='store_true',
                help='Clear the interal DQuery cache'
            )

        self.setup_args()


    def pre_run(self):
        super(DqueryCommandLineMixin, self).pre_run()

        drupal_root = os.path.abspath(self.params.drupal_root)

        #process args, TODO: nice way of doing this
        try:
            if dquery_valid_drupal_root(drupal_root):
                self.params.drupal_root = drupal_root
            else:
                #TODO: Catch all DDquery errors and use argparser.error instaed
                #TODO: investigate possiblilities to override error methods with
                #pretty printing, colors and other fabulous stuff
                message = '{0!r} does not appear to be a valid Drupal root directory'
                self.argparser.error(message.format(drupal_root))
        except Exception as e:
            self.argparser.error(str(e))

        if  self.params.clear_cache:
           dquery_clear_cache()

class DqueryCommandLineApp(DqueryCommandLineMixin, cli.app.Application):

    def __init__(self, main=None, **kwargs):
        DqueryCommandLineMixin.__init__(self, **kwargs)
        cli.app.Application.__init__(self, main, **kwargs)

    def setup(self):
        cli.app.Application.setup(self)
        DqueryCommandLineMixin.setup(self)


#profiler = Profiler(stdout=sys.stdout)

@DqueryCommandLineApp(
    name="dquery",
    version="0.1.0-alpha",
    description="Drupal query tool")
#@profiler.deterministic
def dquery_application(app):
    #dispatch to function
    output = app.params.func(app.params)
    #dispatch to formatter, should formatter or I print?
    app.params.formatter(output)

subparsers = dquery_application.argparser.add_subparsers(
    title='commands',
    help='sub-command help')#, description='valid subcommands')

class dQueryCommand(object):
    # same arguments as ArgumentParser
    def __init__(self, *args, **kwargs):
        self.argparser = subparsers.add_parser(*args, **kwargs)
        self.actions = {} # Why do I need this?
        #self.parser_args = args
        #self.parser_kwargs = kwargs
    #def before_parse(slef, argsparse):
    #def after_parse(self, args):
    """
    def add_param(self, *args, **kwargs):
        action = self.argparser.add_argument(*args, **kwargs)
        self.actions[action.dest] = action
        return action
    """
    def __call__(self, f):
        self.argparser.set_defaults(func=f)
        #Return self?
        return self.argparser

from dquery.commands import *

formatters_group = dquery_application.argparser.add_mutually_exclusive_group(required=False)

class dQueryFormatter(object):
    def __init__(self, format_name, default=False):
        self.name = format_name
        self.default = default
    def __call__(self, f):
        formatters_group.add_argument(
            '--' + self.name,
            dest='formatter',
            action='store_const',
            const=f)
        if self.default:
            dquery_application.argparser.set_defaults(formatter=f)

from dquery.formatters import *

#TODO: helper function, get command-plugin directories, error handling
"""
import imp
modules = []
script_dir = os.path.dirname(os.path.realpath(__file__))
subcommand_directories = [os.path.join(script_dir, 'commands')]
subcommand_files = [
        os.path.join(path, basename)
        for path in subcommand_directories
        for basename in os.listdir(path)
        if fnmatch.fnmatch(basename,'*_dquery_command.py')]
for filename in subcommand_files:
    name = os.path.splitext(os.path.basename(filename))[0]
    try:
        f, pathname, description = imp.find_module(
                name,
                [os.path.dirname(filename)])
        #module = imp.load_module(name, f, pathname, description)
        #modules.append(module)
    except Exception as e:
        print 'printing exception'
        print e
        exit()
"""

