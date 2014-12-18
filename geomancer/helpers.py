from geomancer.app_config import MANCERS
from collections import OrderedDict
import operator
import re

from geomancer.mancers.geotype import City, State, County, SchoolDistrict, \
    CongressionalDistrict, Zip5, Zip9, StateFIPS, StateCountyFIPS, CensusTract

GEOTYPES = [
    City, 
    State, 
    County, 
    SchoolDistrict,
    CongressionalDistrict, 
    Zip5, 
    Zip9, 
    StateFIPS, 
    StateCountyFIPS, 
    CensusTract,
]

def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            v.decode('utf8')
        out_dict[k] = v
    return out_dict

def import_class(cl):
    d = cl.rfind('.')
    classname = cl[d+1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [classname])
    return getattr(m, classname)

def get_geo_types(geo_type=None):
    types = {}
    columns = []
    geo_types = []

    for mancer in MANCERS:
        m = import_class(mancer)()
        for col in m.column_info():
            geo_types.extend(col['geo_types'])
        columns.extend(m.column_info())
    for t in geo_types:
        types[t.machine_name] = {}
        types[t.machine_name]['info'] = t

        tables = [{'human_name': c['human_name'], 
                 'table_id': c['table_id'], 
                 'source_name': c['source_name'], 
                 'count': c['count'], 
                 'source_url': c['source_url']} \
                 for c in columns if t.machine_name in \
                 [i.machine_name  for i in c['geo_types']]]

        tables_sorted = sorted(tables, key=lambda x: x['human_name'])
        types[t.machine_name]['tables'] = tables_sorted

    if geo_type:
        types = {geo_type: types[geo_type]}

    types_sorted = sorted(types.values(), key=lambda x: x['info'].human_name)

    results = []
    for v in types_sorted:
        results.append(v)

    return results

GEO_LOOKUP = {
    'state': ['state'],
    'city': ['city'],
    'county': ['county'],
    'zip_5': ['zip', 'zip code', 'zipcode'],
    'congress_district': ['congressional district'],
    'school_district': ['school district'],
    'state_fips': ['state fips', 'state fips code'],
    'state_county_fips': ['county fips'],
    'census_tract': ['census tract', 'us census tract'],
}

def guess_geotype(header, values):
    guess = None
    for geotype, vals in GEO_LOOKUP.items():
        if header in vals:
            return geotype
    for geotype in GEOTYPES:
        g = geotype()
        valid, message = g.validate(values)
        if valid:
            guess = g.machine_name
    return guess

def get_data_sources(geo_type=None):
    mancer_data = []
    for mancer in MANCERS:
        m = import_class(mancer)()
        mancer_obj = {
            "name": m.name, 
            "machine_name": m.machine_name, 
            "base_url": m.base_url, 
            "info_url": m.info_url, 
            "description": m.description, 
            "data_types": {}
        }
        info = m.column_info()
        for col in info:
            if geo_type:
                col_types = [i.machine_name for i in col['geo_types']]
                if geo_type in col_types:
                    mancer_obj["data_types"][col['table_id']] = col
            else:
                mancer_obj["data_types"][col['table_id']] = col
            try:
                mancer_obj["data_types"][col['table_id']]['geo_types'] = \
                    sorted(mancer_obj["data_types"][col['table_id']]['geo_types'], 
                           key=lambda x: x.human_name)
            except KeyError:
                pass

        mancer_obj["data_types"] = sorted(mancer_obj["data_types"].values(), 
                                          key=lambda x: x['human_name'])

        mancer_data.append(mancer_obj)

    return mancer_data

def find_geo_type(geo_type, col_idxs):
    if ';' not in geo_type:
        return geo_type, col_idxs, '{0}'
    else:
        g = None
        fmt = '{0}, {1}'
        if 'city' in geo_type:
            g = 'city'
        elif 'county' in geo_type:
            g = 'county'
            fmt = '{0} County, {1}'
        elif 'school_district' in geo_type:
            g = 'school_district'
        elif 'congress_district' in geo_type:
            g = 'congress_district'
            fmt = 'Congressional District {0}, {1}'
        if geo_type.find(g) > 0:
            col_idxs = list(reversed(col_idxs.split(';')))
        else:
            col_idxs = col_idxs.split(';')
        return g, col_idxs, fmt
