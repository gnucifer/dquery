from dquery.lib import *
from dquery.xml import *

from cli.profiler import Profiler

import lxml.etree

#profiler = Profiler(stdout=sys.stdout)
#@profiler.deterministic
#TODO: lazy building
def dquery_multisite_xml_xpath(drupal_root, xpath_expression, cache=True):
    xml_etree = dquery_build_multisite_xml_etree(drupal_root, cache=cache)
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cache_filename = os.path.join(
        script_dir,
        'cache',
        ''.join([str(drupal_root.__hash__()), '.dquery_build_multisite_xml_etree.xml']))

    #TODO: error handling
    if cache and os.path.isfile(cache_filename):
        with open(cache_filename, 'r') as cache_file:
            etree_from_file = lxml.etree.parse(cache_file)
            xml_etree = etree_from_file.getroot()
    """


    return xml_etree.xpath(xpath_expression)

def dquery_multisite_xpath_query(drupal_root, xpath_expression, cache=True):
    result = dquery_multisite_xml_xpath(drupal_root, xpath_expression, cache=cache)
    return dquery_xpath_result_to_python(result)

#to_python, to_data, deobjectify, strip_object? ....
def dquery_xpath_result_to_python(xpath_result):
    if type(xpath_result) is bool or type(xpath_result) is int or type(xpath_result) is float:
        return xpath_result
    elif type(xpath_result) is list:
        result = []
        for element in xpath_result:
            result.append(dquery_xpath_result_to_python(element))
        return result;
    elif isinstance(xpath_result, lxml.etree._Element):
        return dquery_lxml_to_dictlist(xpath_result)
    else:
        return str(xpath_result)

"""
<root attr='attrval'>
    <element1 attr='attrval'></element1>
    <element2 attr='attrval'></element2>
    <element2 attr='attrval'></element2>
    <element1 attr='attrval'></element1>
    <element1 attr='attrval'></element1>
    <element2 attr='attrval'></element2>
</root>
 => 
{
    '@attr' : 'attrval',
    'element1' : [{'@attr' : 'attrval'}, {'@attr' : 'attrval'}, {'@attr' : 'attrval'}],
    'element2' : [{'@attr' : 'attrval'}, {'@attr' : 'attrval'}, {'@attr' : 'attrval'}]
}
"""

#TODO: check out values() method
def dquery_lxml_to_dictlist(xml_etree):
    dictlist = {}
    for attr, value in xml_etree.attrib.items():
        dictlist['@' + attr] = value

    #children/elements?
    #TODO: remove len is possible
    # Our xml has either children or content, not both
    if len(xml_etree):
        #_children = []
        #TODO: use values instead?
        for child in xml_etree:
            if not child.tag in dictlist:
                dictlist[child.tag] = []
            dictlist[child.tag].append(dquery_lxml_to_dictlist(child))
    else:
        #how handle this case? handle at all?
        if not xml_etree.text is None:
            dictlist['value'] = xml_etree.text
    return dictlist


