import os

_script_dir = os.path.dirname(os.path.realpath(__file__))

cache_dir = '.cache'
cache_dir_abspath = os.path.join(_script_dir, cache_dir)

#TODO: implement?
plugin_directories = [_script_dir]
