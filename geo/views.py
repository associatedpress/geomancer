from flask import Blueprint, make_response, request, session, \
    render_template, current_app
import json
import os
import gzip
from uuid import uuid4
from werkzeug import secure_filename
from csvkit import convert
from csvkit.unicsv import UnicodeCSVReader
from cStringIO import StringIO

views = Blueprint('views', __name__)

ALLOWED_EXTENSIONS = set(['csv', 'xls', 'xlsx'])

@views.route('/', methods=['GET', 'POST'])
def index():
    context = {}
    if request.method == 'POST':
        f = request.files['input_file']
        inp = StringIO(f.read())
        file_format = convert.guess_format(f.filename)
        try:
            converted = convert.convert(inp, file_format)
        except UnicodeDecodeError:
            context['errors'] = ['We had a problem with reading your file. \
                This could have to do with the file encoding or format']
            converted = None
        if converted:
            outp = StringIO(converted)
            reader = UnicodeCSVReader(outp)
            context['header_row'] = reader.next()
            rows = []
            columns = [[] for c in context['header_row']]
            column_ids = range(len(context['header_row']))
            for row in range(10):
                rows.append(reader.next())
            for i, row in enumerate(rows):
                for j,d in enumerate(row):
                    columns[j].append(row[column_ids[j]])
            columns = [', '.join(c) for c in columns]
            sample_data = []
            for index,_ in enumerate(context['header_row']):
                sample_data.append((index, context['header_row'][index], columns[index]))
            context['sample_data'] = sample_data
            outp.seek(0)
            session['file'] = outp.getvalue()
    return render_template('index.html', **context)

@views.route('/geomance/', methods=['POST'])
def geomance():
    if not session.get('file'):
        redirect(url_for('views.index'))
    print request.form
    inp = StringIO(session['file'])
    reader = UnicodeCSVReader(inp)
    header = reader.next()
    field_names = []
    for k,v in request.form.items():
        index = int(k.split('_')[1])
        field_names.append(header[index])
    context = {'field_names': field_names}
    return render_template('geomance.html', **context)
