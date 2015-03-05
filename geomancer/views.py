from flask import Blueprint, make_response, request, redirect, url_for, \
    session, render_template, current_app, send_from_directory, flash
import json
import sys
import os
import gzip
import requests
from uuid import uuid4
from werkzeug import secure_filename
from csvkit import convert
from csvkit.unicsv import UnicodeCSVReader
from csvkit.cleanup import RowChecker
from cStringIO import StringIO
from geomancer.helpers import import_class, get_geo_types, get_data_sources, \
    guess_geotype, check_combos, SENSICAL_TYPES
from geomancer.app_config import ALLOWED_EXTENSIONS, \
    MAX_CONTENT_LENGTH
from werkzeug.exceptions import RequestEntityTooLarge

views = Blueprint('views', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# primary pages
@views.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@views.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

@views.route('/upload-formats', methods=['GET', 'POST'])
def upload_formats():
    return render_template('upload-formats.html')

@views.route('/contribute-data', methods=['GET', 'POST'])
def contribute_data():
    return render_template('contribute-data.html')

@views.route('/geographies', methods=['GET', 'POST'])
def geographies():
    geographies, errors = get_geo_types()
    for error in errors:
        flash(error)
    return render_template('geographies.html', geographies=geographies)

@views.route('/data-sources', methods=['GET', 'POST'])
def data_sources():
    data_sources, errors = get_data_sources()
    for error in errors:
        flash(error)
    return render_template('data-sources.html', data_sources=data_sources)

# routes for geomancin'
@views.route('/upload/', methods=['GET', 'POST'])
def upload():
    context = {}
    if request.method == 'POST':
        big_file = False
        try:
            files = request.files
        except RequestEntityTooLarge, e:
            files = None
            big_file = True
            current_app.logger.info(e)
        if files:
            f = files['input_file']
            if allowed_file(f.filename):
                inp = StringIO(f.read())
                file_format = convert.guess_format(f.filename)
                try:
                    converted = convert.convert(inp, file_format)
                except UnicodeDecodeError:
                    context['errors'] = ['We had a problem with reading your file. \
                        This could have to do with the file encoding or format']
                    converted = None
                f.seek(0)
                if converted:
                    outp = StringIO(converted)
                    reader = UnicodeCSVReader(outp)
                    session['header_row'] = reader.next()
                    rows = []
                    columns = [[] for c in session['header_row']]
                    column_ids = range(len(session['header_row']))
                    for row in range(100):
                        try:
                            rows.append(reader.next())
                        except StopIteration:
                            break
                    for i, row in enumerate(rows):
                        for j,d in enumerate(row):
                            columns[j].append(row[column_ids[j]])
                    sample_data = []
                    guesses = {}
                    for index, header_val in enumerate(session['header_row']):
                        guesses[index] = guess_geotype(header_val, columns[index])
                        sample_data.append((index, header_val, columns[index]))
                    session['sample_data'] = sample_data
                    session['guesses'] = json.dumps(guesses)
                    outp.seek(0)
                    session['file'] = outp.getvalue()
                    session['filename'] = f.filename
                    return redirect(url_for('views.select_geo'))
            else:
                context['errors'] = ['Only .xls or .xlsx and .csv files are allowed.']
        else:
            context['errors'] = ['You must provide a file to upload.']
            if big_file:
                context['errors'] = ['Uploaded file must be 10mb or less.'] 
    return render_template('upload.html', **context)

@views.route('/select-geography/', methods=['GET', 'POST'])
def select_geo():
    if not session.get('file'):
        return redirect(url_for('views.index'))
    context = {}
    if request.method == 'POST':
        inp = StringIO(session['file'])
        reader = UnicodeCSVReader(inp)
        header = reader.next()
        fields = {}
        valid = True
        geotype_val = None
        if not request.form:
            valid = False
            context['errors'] = ['Select a field that contains a geography type']
        else:
            geotypes = []
            indexes = []
            for k,v in request.form.items():
                if k.startswith("geotype"):
                    geotypes.append(v)
                    indexes.append(k.split('_')[1])
            if len(indexes) > 2:
                valid = False
                context['errors'] = ['We can only merge geographic information from 2 columns']
            else:
                fields_key = ';'.join([header[int(i)] for i in indexes])
                geotype_val = ';'.join([g for g in geotypes])
                if not check_combos(geotype_val):
                    valid = False
                    types = [t.title() for t in geotype_val.split(';')]
                    context['errors'] = ['The geographic combination of {0} and {1} does not work'.format(*types)]
                else:
                    fields[fields_key] = {
                        'geo_type': geotype_val,
                        'column_index': ';'.join(indexes)
                    }

            # found_geo_type = get_geo_types(geo_type)[0]['info']
            # sample_list = session['sample_data'][index][2]
            # valid, message = found_geo_type.validate(sample_list)
            # context['errors'] = [message]
        if valid:
            try:
                geo_type = SENSICAL_TYPES[geotype_val]
            except KeyError:
                geo_type = geotype_val
            mancer_data, errors = get_data_sources(geo_type=geo_type)
            session['fields'] = fields
            session['mancer_data'] = mancer_data
            for error in errors:
                flash(error)
            return redirect(url_for('views.select_tables'))
    return render_template('select_geo.html', **context)

@views.route('/select-tables/', methods=['POST', 'GET'])
def select_tables():
    if not session.get('file'):
        return redirect(url_for('views.index'))
    context = {}
    if request.method == 'POST' and not request.form:
        valid = False
        context['errors'] = ['Select at least on table to join to your spreadsheet']
    return render_template('select_tables.html', **context)

@views.route('/geomance/<session_key>/')
def geomance_view(session_key):
    return render_template('geomance.html', session_key=session_key)

@views.route('/download/<path:filename>')
def download_results(filename):
    return send_from_directory(current_app.config['RESULT_FOLDER'], filename)

@views.route('/413.html')
def file_too_large():
    return make_response(render_template('413.html'), 413)
