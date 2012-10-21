#!/usr/bin/env python

#if sys.stdout.isatty(): + turn off pipe detection
# + colors
import sys
import cli.app #TODO
import fnmatch
import yaml
from cli.profiler import Profiler
from lib import *

#import inspect
#TODO: rename module-usage to usage, or perhaps present tense, using?
from colorama import init
init()
#import dquery

__all__ = ["dquery_application", "dquery_command", "dQueryCommand"]

"""
dquery_commands = []

def dquery_command(subcommand):
    print 'registring command'
    print subcommand
    dquery_commands.append(subcommand)
    return subcommand

def dquery_depends(args):
    print 'depends'
    print args

def dquery_belongs(args):
    print 'belongs'
    print args

def dquery_projects(args):
    module_directories = dquery_drupal_module_directories(args.drupal_root, cache=args.use_cache)
    module_map = dquery_modules_list(args.drupal_root, module_directories, cache=args.use_cache)
    projects = args.projects if len(args.projects) else module_map.keys
    for project in projects:
        for projects_dir in module_map[project]:
            version = ''
            project_dir = module_map[project][projects_dir]['directory']
            for module_namespace, module_info in module_map[project][projects_dir]['modules'].iteritems():
                if 'version' in module_info['info']:
                    version = module_info['info']['version']
                    break
            print ', '.join(['project:' + project, 'version:' + version, 'directory:' + project_dir])
"""
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
                help='Do not use the internal dquery cache'
                )

        self.argparser.add_argument(
                '--clear-cache',
                dest='clear_cache',
                action='store_true',
                help='Clear the interal dquery cache'
            )

        #self.argparser.add_argument('module_directories', metavar='MODULE_DIRECTORY',  type=str, nargs='*', help='Module directories')
        
        #for subcommand in self._load_subcommands():



        """
        from dquery.commands import *
        usage_dquery_command.test()
        print sys.modules.keys()
        exit()
        """

        """
        print dquery.commands.__package__

        print dquery.commands.usage_dquery.test()

        for subcommand in dquery.commands.__all__:
            print subcommand
            ##print dir(getattr(dquery.commands, subcommand))
        print dir(dquery.commands)
        exit()
        """

        #print dir(subcommands)
        #print subcommands.modules.keys()
        #exit()
        
        """
        subparsers = self.argparser.add_subparsers(
                title='commands',
                help='sub-command help'
                )#, description='valid subcommands')

        parser_sites = subparsers.add_parser('sites',
                help='list sites'
                )

        parser_sites.add_argument('-f, --format',
                dest='format',
                choices=['uri', 'relpath', 'abspath', 'basename'],
                default='uri',
                help='Site output format'
                )

        #TODO: how make parseargs save as frozenset instead of list
        parser_sites.set_defaults(func=dquery_sites)

        parser_projects = subparsers.add_parser('projects',
                help='list projects'
                )

        parser_projects.add_argument('projects',
                metavar='PROJECT',
                type=str, nargs='*',
                help='Limit results'
                )

        parser_projects.set_defaults(func=dquery_projects)
        
        parser_modules = subparsers.add_parser('modules',
                help='list modules'
                )

        parser_modules.add_argument('module_namespaces',
                metavar='MODULE',
                type=str,
                nargs='*',
                help='Limit results'
                )

        parser_modules.set_defaults(func=dquery_modules)

        parser_module_info = subparsers.add_parser('module-info',
                help='display module info'
                )

        parser_module_info.add_argument('module_path',
                type=str,
                help='Path to module to display info for'
                )

        #TODO: how make parseargs save as frozenset instead of list
        parser_module_info.set_defaults(func=dquery_module_info_action)
        parser_depends = subparsers.add_parser(
                'depends',
                help='depends help'
                )

        parser_depends.add_argument(
                '--baz',
                choices='XYZ',
                help='baz help'
                )

        parser_depends.set_defaults(func=dquery_depends)

        parser_belongs = subparsers.add_parser(
                'belongs',
                help='belongs help'
                )
        parser_belongs.add_argument(
                'bar',
                type=int,
                help='baz help'
                )

        parser_belongs.set_defaults(func=dquery_belongs)
        """
        self.setup_args()


    def pre_run(self):
        super(DqueryCommandLineMixin, self).pre_run()

        drupal_root = os.path.abspath(self.params.drupal_root)

        #process args, TODO: nice way of doing this
        try:
            if dquery_valid_drupal_root(drupal_root):
                self.params.drupal_root = drupal_root
            else:
                #TODO: python string formatting, gah
                self.argparser.error(drupal_root + ' does not appear to be a valid drupal root directory')

        except Exception as e:
            self.argparser.error(str(e))

        if  self.params.clear_cache:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            cache_dir = os.path.join(script_dir, 'cache')
            for basename in os.listdir(cache_dir):
                filename = os.path.join(cache_dir, basename)
                try:
                    if os.path.isfile(filename):
                        os.unlink(filename)
                except Exception as e:
                    print e


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

def dquery_default_formatter(output):
    print yaml.dump(output, default_flow_style=False)

dquery_application.argparser.set_defaults(formatter=dquery_default_formatter)
formatters_group = dquery_application.argparser.add_mutually_exclusive_group(required=False)

#dquery_application.argparser.add_argument('-f', '--format', default=

class dQueryFormatter(object):
    def __init__(self, format_name):
        self.name = format_name
    def __call__(self, f):
        formatters_group.add_argument(
            '--' + self.name,
            dest='formatter',
            action='store_const',
            const=f)

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

