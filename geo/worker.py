from flask import current_app
from pickle import loads, dumps
from redis import Redis
from uuid import uuid4
import sys
import os
from cStringIO import StringIO
from csvkit.unicsv import UnicodeCSVReader
from geo.utils.lookups import ACS_DATA_TYPES, GEO_TYPES
from geo.utils.census_reporter import CensusReporter, CensusReporterError

redis = Redis()

class DelayedResult(object):
    def __init__(self, key):
        self.key = key
        self._rv = None

    @property
    def return_value(self):
        if self._rv is None:
            rv = redis.get(self.key)
            if rv is not None:
                self._rv = loads(rv)
        return self._rv
    
def queuefunc(f):
    def delay(*args, **kwargs):
        qkey = current_app.config['REDIS_QUEUE_KEY']
        key = '%s:result:%s' % (qkey, str(uuid4()))
        s = dumps((f, key, args, kwargs))
        redis.rpush(current_app.config['REDIS_QUEUE_KEY'], s)
        return DelayedResult(key)
    f.delay = delay
    return f

@queuefunc
def do_the_work(file_contents, field_defs):
    """
      {
        10: {
          'type': 'city_state', 
          'append_columns': ['total_population', 'median_age']
        }
      }
    """
    contents = StringIO(file_contents)
    reader = UnicodeCSVReader(contents)
    header = reader.next()
    c = CensusReporter()
    result = None
    geo_ids = set()
    table_ids = set()
    geoid_mapper = {}
    for row_idx, row in enumerate(reader):
        col_idxs = [int(k) for k in field_defs.keys()]
        for idx in col_idxs:
            val = row[idx]
            geo_type = field_defs[idx]['type']
            for column in field_defs[idx]['append_columns']:
                table_ids.add(ACS_DATA_TYPES[column]['table_id'])
            sumlevs = [g['acs_sumlev'] for g in GEO_TYPES if g['name'] == geo_type]
            try:
                geoid_search = c.geo_search(val, sumlevs=sumlevs)
            except CensusReporterError, e:
                return e.message
            row_geoid = geoid_search['results'][0]['full_geoid']
            geo_ids.add(row_geoid)
            try:
                geoid_mapper[row_geoid].append(row_idx)
            except KeyError:
                geoid_mapper[row_geoid] = [row_idx]
    print geo_ids
    print table_ids
    print geoid_mapper
    return 'boo'
    #try:
    #    data = c.data_show(geo_ids=list(geo_ids), table_ids=list(table_ids))
    #except CensusReporterError, e:
    #    return e.message
    #return data

def queue_daemon(app, rv_ttl=500):
    while 1:
        msg = redis.blpop(app.config['REDIS_QUEUE_KEY'])
        func, key, args, kwargs = loads(msg[1])
        try:
            rv = func(*args, **kwargs)
        except Exception, e:
            rv = e.message
        if rv is not None:
            redis.set(key, dumps(rv))
            redis.expire(key, rv_ttl)
