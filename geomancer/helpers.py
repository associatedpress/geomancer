from geomancer.app_config import MANCERS
from collections import OrderedDict
import operator

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
    type_details = {}

    for mancer in MANCERS:
        m = import_class(mancer)()
        for col in m.column_info():
            geo_types.extend(col['geo_types'])
        columns.extend(m.column_info())
    for t in geo_types:
        types[t.machine_name] = {}
        types[t.machine_name]['info'] = t
        types[t.machine_name]['tables'] = [{'human_name': c['human_name'], 
                     'table_id': c['table_id'], 
                     'source_name': c['source_name'], 
                     'count': c['count'], 
                     'source_url': c['source_url']} \
                     for c in columns if t.machine_name in \
                     [i.machine_name  for i in c['geo_types']]]

    if geo_type:
        types = types[geo_type]

    return OrderedDict(sorted(types.items()))

def get_data_sources(geo_type=None):
    mancer_data = []
    for mancer in MANCERS:
        m = import_class(mancer)()
        mancer_obj = {
            "name": m.name, 
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

        mancer_data.append(mancer_obj)

    return mancer_data