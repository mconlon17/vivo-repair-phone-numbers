#!/user/bin/env/python
"""
    repair-phone-numbers.py -- Replace poorly formatted phone numbers with
    improved formatted phone numbers

    At UF, phone numbers in VIVO come from a variety of sources.  Some come
    from the UF directory, which itself gathers from various sources, some are
    self-edited, while others are proxy edited.  VIVO supports an open-text
    box for phone numbers leading to a wide variety of inputs.

    This software repairs VIVO phone numbers as needed to comply with ITU
    recommended standards.  Resulting phone numbers
    will have one of the following formats:

    (xxx) xxx-xxxx ext. xxxx where area code and/or extension are optional
    +xx xxx xxxx xx xxx      where spacing between number groups is according
                             to local stadards

    References
    International Telecommunications Union, Notation for national and
    international telephone numbers, e-mail addresses and web addresses
    http://www.itu.int/rec/T-REC-E.123-200102-I/en

    Madey, John Suncom Number Changes, March 21, 2008.
    http://www.admin.ufl.edu/ddd/default.asp?doc=13.9.2206.7

    All vivo:phoneNumber and vivo:phoneNumber values are considered and
    replaced as needed.

    Version 0.95 MC 2013-03-02
    --  Query VIVO, process phone numbers and replace as necessary
    Version 1.0 MC 2014-02-17
    --  repair_phone_number now in vivotools, pass pylint

"""

__author__ = "Michael Conlon"
__copyright__ = "Copyright 2013, University of Florida"
__license__ = "BSD 3-Clause license"
__version__ = "1.0"

import tempita
import vivotools as vt

def make_phone_dictionary(phone_dictionary={}, debug=False):
    """
    Extract all phone numbers in VIVO and organize them into a dictionary
    keyed by uri and each with a dictionary of phone and primary phone
    """
    query = tempita.Template("""
    SELECT ?uri ?phone ?primary
    WHERE {
    {?uri vivo:phoneNumber ?phone .}
    UNION {?uri vivo:primaryPhoneNumber ?primary .}
    }""")
    query = query.substitute()
    result = vt.vivo_sparql_query(query)
    try:
        count = len(result["results"]["bindings"])
    except:
        count = 0
    if debug:
        print query, count,\
        result["results"]["bindings"][0], result["results"]["bindings"][1]
    #
    i = 0
    while i < count:
        b = result["results"]["bindings"][i]
        uri = b['uri']['value']
        dict = {}
        if 'phone' in b:
            dict['phone'] = b['phone']['value']
        if 'primary' in b:
            dict['primary'] = b['primary']['value']
        if dict != {}:
            phone_dictionary[uri] = dict
        i = i + 1
    return phone_dictionary

#  Start here

print "Making phone dictionary"
phone_dictionary = make_phone_dictionary(debug=True)
print "Phone dictionary has ", len(phone_dictionary), " entries."
ardf = vt.rdf_header()
srdf = vt.rdf_header()
i = 0
na = 0
ns = 0

for uri, result in phone_dictionary.items():
    i = i + 1
    if i > 200000:
        break
    if 'phone' in result:
        updated_phone = vt.repair_phone_number(result['phone'], debug=True)
        [add, sub] = vt.update_data_property(uri, 'vivo:phoneNumber',
                                         result['phone'], updated_phone)
        ardf = ardf + add
        srdf = srdf + sub
    if 'primary' in result:
        updated_phone = vt.repair_phone_number(result['primary'], debug=True)
        [add, sub] = vt.update_data_property(uri, 'vivo:primaryPhoneNumber',
                                         result['primary'], updated_phone)
        if add != "":
            na = na + 1
        if sub != "":
            ns = ns + 1
        ardf = ardf + add
        srdf = srdf + sub
srdf = srdf + vt.rdf_footer()
ardf = ardf + vt.rdf_footer()
print "<!-- Addition RDF -->"
print ardf
print "<!-- Subtraction RDF -->"
print srdf
print "Number to add = ", na
print "Number to subtract = ", ns
