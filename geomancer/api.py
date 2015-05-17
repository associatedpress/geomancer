from flask import Blueprint, make_response, request, jsonify, \
    session as flask_session
from geomancer.worker import DelayedResult, do_the_work
from geomancer.helpers import import_class, get_geo_types, get_data_sources
from geomancer.app_config import MANCERS, MANCER_KEYS
from geomancer.mancers.geotype import GeoTypeEncoder
import json
from redis import Redis
from collections import OrderedDict

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

    To mance on a combination of columns, separate the column indexes and 
    geotypes with a semicolon like so:

      {
        10;2: {
          'type': 'city;state', 
          'append_columns': ['total_population', 'median_age']
        }
      }

    In this example, column 10 contains the city info and column 2 contains
    the state info.

    Responds with a key that can be used to poll for results
    """

    field_defs = json.loads(request.data)
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

@api.route('/api/data-sources/')
def data_sources():
    """ 
    Return a list of data sources
    """
    mancers = None
    if request.args.get('geo_type'):
        mancers, errors = get_data_sources(request.args.get('geo_type'))
    else:
        mancers, errors = get_data_sources()
    resp = make_response(json.dumps(mancers, cls=GeoTypeEncoder))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@api.route('/api/table-info/')
def table_info():
    """ 
    Return a list of data sources
    """
    columns = OrderedDict()
    for mancer in MANCERS:
        m = import_class(mancer)
        api_key = MANCER_KEYS.get(m.machine_name)
        try:
            m = m(api_key=api_key)
        except ImportError, e:
            continue
        col_info = m.get_metadata()
        for col in col_info:
            columns[col['table_id']] = {
              'table_id': col['table_id'],
              'human_name': col['human_name'],
              'mancer': m.name, 
              'columns': col['columns'],
              'source_url': col['source_url'],
            }
    response = []
    if request.args.get('table_id'):
        table_id = request.args['table_id']
        try:
            response.append(columns[table_id])
        except KeyError:
            response.append({
                'status': 'error',
                'message': 'table_id %s not found' % table_id
            })
    else:
        response.extend(columns.values())
    resp = make_response(json.dumps(response))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@api.route('/api/geo-types/')
def geo_types():
    """ 
    Return a list of tables grouped by geo_type
    """
    ordered_types = None
    if request.args.get('geo_type'):
        ordered_types, errors = get_geo_types(request.args.get('geo_type'))
    else:
        ordered_types, errors = get_geo_types()
    resp = make_response(json.dumps(ordered_types, cls=GeoTypeEncoder))
    resp.headers['Content-Type'] = 'application/json'
    return resp
