from flask import Blueprint, make_response, request, jsonify, \
    session as flask_session
from geomancer.worker import DelayedResult, do_the_work
from geomancer.helpers import import_class, get_geo_types
from geomancer.app_config import MANCERS
from geomancer.mancers.geotype import GeoTypeEncoder
import json
from redis import Redis

redis = Redis()

api = Blueprint('api', __name__)

@api.route('/api/geomance/', methods=['POST', 'GET'])
def geomance_api():
    """ 
    Needs to get the file as well which fields have 
    geography and what kind of geography they contain.
    Should be a multipart POST with the file in the file part
    and the field definitions in the form part.

    Field definitions should be in string encoded JSON blob like so:

      {
        10: {
          'type': 'city_state', 
          'append_columns': ['total_population', 'median_age']
        }
      }
    The key is the zero-indexed position of the columns within the spreadsheet.
    The value is a dict containing the geographic type and the columns to 
    append. The values in that list should be fetched from one of the other
    endpoints.

    Responds with a key that can be used to poll for results
    """
    defs = json.loads(request.data)
    field_defs = {}
    for k,v in defs.items():
        field_defs[int(k)] = v
    if request.files:
        file_contents = request.files['input_file'].read()
        filename = request.files['input_file'].filename
    else:
        file_contents = flask_session['file']
        filename = flask_session['filename']
    session = do_the_work.delay(file_contents, field_defs, filename)
    resp = make_response(json.dumps({'session_key': session.key}))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@api.route('/api/geomance-results/<session_key>/')
def geomance_results(session_key):
    """ 
    Looks in the Redis queue to see if the worker has finished yet.
    """
    rv = DelayedResult(session_key)
    if rv.return_value is None:
        return jsonify(ready=False)
    redis.delete(session_key)
    result = rv.return_value
    return jsonify(ready=True, result=result['result'], status=result['status'])

@api.route('/api/geo-types/')
def geo_types():
    """ 
    Return a list of tables grouped by geo_type
    """
    ordered_types = None
    if request.args.get('geo_type'):
        ordered_types = get_geo_types(request.args.get('geo_type'))
    else:
        ordered_types = get_geo_types()
    resp = make_response(json.dumps(ordered_types, cls=GeoTypeEncoder))
    resp.headers['Content-Type'] = 'application/json'
    return resp
    

@api.route('/api/data-info/')
def data_attrs():
    """ 
    For a given geographic type, return a list of available data attributes
    for that geography.
    """
    geo_type = request.args.get('geo_type')
    attributes = []
    for mancer in MANCERS:
        m = import_class(mancer)()
        info = m.column_info()
        d = {'source': m.name, 'tables': [], 'description': m.description}
        if geo_type:
            d['tables'].extend([c for c in info if geo_type in c['geo_types']])
        else:
            d['tables'].extend(info)
        attributes.append(d)
    resp = make_response(json.dumps(attributes))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@api.route('/api/data-map/')
def data_map():
    """ 
    For a list of geographic identifiers, a geographic type and data attributes, 
    return a set of data attributes for each geographic identifier
    """
    resp = make_response(json.dumps({}))
    resp.headers['Content-Type'] = 'application/json'
    return resp
