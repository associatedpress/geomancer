import scrapelib
import us
from urllib import urlencode
import json
import os
from geomancer.mancers.mancer import Mancer
from geomancer.helpers import encoded_dict
from lxml import etree
import re
from collections import OrderedDict

TABLE_PARAMS = {
    'fpds': {
        'state': 'stateCode', 
        'zip_5': 'placeOfPerformanceZIPCode', 
        'congress_district': 'pop_cd'
    },
    'faads': {
        'state': 'principal_place_state_code', 
        'city': 'principal_place_cc', 
        'county': 'principal_place_cc',
    },
    'fsrs': {
        'state': 'subawardee_pop_state', 
        'zip_5': 'subawardee_pop_zip', 
        'congress_district': 'subawardee_pop_cd',
    },
}

class USASpendingError(Exception):
    def __init__(self, message, body=None):
        Exception.__init__(self, message)
        self.message = message
        self.body = body

class USASpending(Mancer):
    """ 
    Subclassing Mancer
    """

    base_url = "http://www.usaspending.gov"
    description = """ """

    @staticmethod
    def column_info():
        return [
            {
              'table_id': 'fpds', 
              'human_name': 'Federal Contracts',
              'description': '',
              'source_url': 'http://www.usaspending.gov/data',
              'geo_types': ['state','zip_5', 'congress_district'],
              'count': 1 # probably a lot more
            },
            {
              'table_id': 'faads', 
              'human_name': 'Federal Assistance',
              'description': '',
              'source_url': 'http://www.usaspending.gov/data',
              'geo_types': ['state','city','county'],
              'count': 1 # probably a lot more
            },
            {
              'table_id': 'fsrs', 
              'human_name': 'Federal sub-awards',
              'description': '',
              'source_url': 'http://www.usaspending.gov/data',
              'geo_types': ['state','zip_5', 'congress_district'],
              'count': 1 # probably a lot more
            },
        ]

    def lookup_state(self, term):
        st = us.states.lookup(term)
        if not st:
            st = [s for s in us.STATES if getattr(s, 'ap_abbr') == search_term]
        if st:
            return st.abbr
        else:
            return term

    def geo_lookup(self, search_term, geo_type=None):
        if geo_type == 'state':
            return {'term': search_term, 'geoid': self.lookup_state(search_term)}
        elif geo_type == 'congress_district':
            parts = search_term.split(' ')
            district = search_term
            if len(parts) > 1:
                st_abbr = self.lookup_state(part[0])
                dist_code = parts[1].zfill(2)
                district = st_abbr + dist_code 
            return {'term': search_term, 'geoid': district}
        else:
            return {'term': search_term, 'geoid': search_term.zfill(5)}

    def search(self, geo_ids=None, columns=None):
        """
        Yay!

        {
            'header': [
                '<data source name 1>',
                '<data source name 2>',
                '...etc...'
            ],
            '<geographic id 1>': [
                <value 1>,
                <value 2>,
                <value 3>,
                <value 4>,
                ...etc...,
            ],
            '<geographic id 2>': [
                <value 1>,
                <value 2>,
                <value 3>,
                <value 4>,
                ...etc...,
            ],
        }
        """
        result = {'header': []}
        for geo_type, geo_id in geo_ids:
            result[geo_id] = []
            for col in columns:
                table = OrderedDict()
                url = '%s/%s/%s.php' % (self.base_url, col, col)
                param = TABLE_PARAMS[col][geo_type]
                query = {param: geo_id, 'detail': 's'}
                params = urlencode(query)
                response = self.urlopen('%s?%s' % (url, params))
                tree = etree.fromstring(str(response))
                xml_schema = tree.nsmap[None]
                tables = tree\
                    .find('{%s}data' % xml_schema)\
                    .find('{%s}record' % xml_schema)\
                    .getchildren()
                for t in tables:
                    table_name = t.tag.replace('{%s}' % xml_schema, '')
                    for column in t.iterchildren():
                        key = column.tag.replace('{%s}' % xml_schema, '')
                        value = column.text
                        if column.attrib:
                            for k,v in column.attrib.items():
                                if k in ['rank', 'year']:
                                    table['%s_%s_%s' % (table_name,k,v.zfill(2))] = value
                                if k in ['total_obligatedAmount', 'id', 'name']: 
                                    rank = column.attrib['rank']
                                    table['%s_rank_%s_%s' % (table_name,rank.zfill(2),k)] = v
                        else:
                            table['%s_%s' % (table_name,key)] = value
                if not result['header']:
                    header = [' '.join(c.split('_')).title() for c in table.keys()]
                    result['header'].extend(header)
                result[geo_id].extend(table.values())

        return result
    
