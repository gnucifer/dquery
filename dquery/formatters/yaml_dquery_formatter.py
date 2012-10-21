import yaml
from dquery.application import dQueryFormatter
@dQueryFormatter('yaml')
def dquery_yaml_formatter(output):
    print yaml.dump(output, default_flow_style=False)
