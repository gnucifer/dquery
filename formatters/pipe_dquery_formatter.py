from dquery.application import dQueryFormatter
#TODO: replace with some kind of table printing formatter?
@dQueryFormatter('pipe')
def dquery_pipe_formatter(output):
    if type(output) is list:
        for line in output:
            if type(line) is list:
                print ' '.join(line)
            elif type(line) is dict:
                row = [key + ' ' + value for key, value in line.items() if isinstance(key, str) and key[0] == '@']
                if row:
                    print ' '.join(row)
            else:
                print str(line)
    else:
        print str(output)

