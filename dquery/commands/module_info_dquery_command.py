from dquery.application import dQueryCommand
from dquery.lib import *

@dQueryCommand('module-info', help='display module info')
def dquery_module_info_command(args):
    #TODO: more path mangling
    module_abspath = None
    if os.path.isabs(args.module_path):
        module_abspath = os.path.realpath(args.module_path) 
    else:
        module_abspath = os.path.join(args.drupal_root, args.module_path)
    info = dquery_module_info(module_abspath)
    print yaml.dump(info, default_flow_style=False)

dquery_module_info_command.add_argument('module_path', type=str, help='Path to module to display info for')
