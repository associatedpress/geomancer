import scrapelib
import us
from urllib import urlencode
import json
import os
from geomancer.utils.mancer import Mancer
from geomancer.utils.helpers import encoded_dict
from lxml import etree
import re

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
    xml_schema = 'http://www.usaspending.gov/schemas/'

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
        for geo_type, geo_id in geo_ids:
            for column in columns:
                url = '%s/%s/%s.php' % (self.base_url, column, column)
                param = TABLE_PARAMS[column][geo_type]
                query = {param: geo_id, 'detail': 's'}
                params = urlencode(query)
                response = self.urlopen('%s?%s' % (url, params))
                result = getattr(self,'parse_%s' % column)(response)
                print json.dumps(result, indent=4)

    def parse_fpds(self, raw):
        """
        Parse Contracts response
        """
        tree = etree.fromstring(str(raw))
        tables = tree\
            .find('{%s}data' % self.xml_schema)\
            .find('{%s}record' % self.xml_schema)\
            .getchildren()
        parsed = {}
        for table in tables:
            table_name = table.tag.replace('{%s}' % self.xml_schema, '')
            parsed[table_name] = {}
            for column in table.iterchildren():
                key = column.tag.replace('{%s}' % self.xml_schema, '')
                value = column.text
                parsed[table_name][key] = {k:v for k,v in column.attrib.items()}
                parsed[table_name][key]['value'] = value
        return parsed
    
    def parse_faads(self, raw):
        """
        Parse Assistance response
        """
        return raw
    
    def parse_fsrs(self, raw):
        """
        Parse Sub-Awards response
        """
        return raw
