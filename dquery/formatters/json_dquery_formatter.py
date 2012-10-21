import json
from dquery.application import dQueryFormatter
@dQueryFormatter('json')
def dquery_json_formatter(output):
    print json.dumps(output, indent=2)
