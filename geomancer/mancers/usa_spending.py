import scrapelib
import us
from urllib import urlencode
import json
import os
from geomancer.mancers.base import BaseMancer
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

class USASpending(BaseMancer):
    """ 
    Subclassing BaseMancer
    """

    base_url = "http://www.usaspending.gov"
    info_url = 'http://www.usaspending.gov'
    description = """ 
        Data from the U.S. Office of Management and Budget on federal contracts awarded.
    """

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
        """
        result = {'header': []}
        header_keys = set()
        table_ds = {}
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
                    real_rank_keys = []
                    real_obl_keys = []
                    fake_rank_keys = []
                    fake_obl_keys = []
                    if t.attrib.get('ranked_by'):
                        fake_rank_keys = ['%s_rank_%s' % (table_name, str(i).zfill(2)) \
                            for i in range(1,11)]
                        fake_obl_keys = ['%s_rank_%s_total_obligatedAmount' % \
                            (table_name, str(i).zfill(2)) for i in range(1,11)]
                    child_nodes = t.getchildren()
                    for column in child_nodes:
                        key = column.tag.replace('{%s}' % xml_schema, '')
                        value = column.text
                        if column.attrib:
                            for k,v in column.attrib.items():
                                if k in ['rank', 'year']:
                                    header_val = '%s_%s_%s' % (table_name,k,v.zfill(2))
                                    table[header_val] = value
                                    if k == 'rank':
                                        real_rank_keys.append(header_val)
                                if k in ['total_obligatedAmount', 'id', 'name']: 
                                    rank = column.attrib['rank']
                                    header_val = '%s_rank_%s_%s' % (table_name,rank.zfill(2),k)
                                    table[header_val] = v
                                    if k == 'total_obligatedAmount':
                                        real_obl_keys.append(header_val)
                        else:
                            table['%s_%s' % (table_name,key)] = value
                    if not set(fake_rank_keys).issubset(real_rank_keys):
                        diff = set(fake_rank_keys).difference(real_rank_keys)
                        for col_name in diff:
                            table[col_name] = None
                    if not set(fake_obl_keys).issubset(real_obl_keys):
                        diff = set(fake_obl_keys).difference(real_obl_keys)
                        for col_name in diff:
                            table[col_name] = None
                table = OrderedDict(sorted(table.items()))
                if len(result['header']) != len(table.keys()):
                    positions = [(i, c) for i,c in enumerate(table.keys()) if c not in header_keys]
                    for idx, col in positions:
                        header_keys.add(col)
                        result['header'].insert(i, ' '.join(col.split('_')).title())
                        table[col] = table.get(col)
                table_ds[geo_id] = table
        for key in header_keys:
            for geo_type, geo_id in geo_ids:
                table_ds[geo_id][key] = table_ds[geo_id].get(key)
                result[geo_id] = table_ds[geo_id].values()
        return result
    
