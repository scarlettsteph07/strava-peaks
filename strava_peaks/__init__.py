from flask import Flask, request, render_template
from dotenv import load_dotenv
import yaml
import json
from strava_peaks.constants import config
import datetime
import os

load_dotenv()
app = Flask(__name__)

user_file = open(os.getenv("DATA_FILE"))
user_data = yaml.load(user_file, Loader=yaml.FullLoader)

def peaks_data(request, limit):
    activity_type = request.args.get('type') or 'cycling'
    attribute = request.args.get('attribute') or 'watts'
    duration = request.args.get('duration') or 300

    heartrate_peaks = [act for act in user_data[activity_type]
                       if act['attribute'] == attribute and act['duration'] == int(duration)]
    for peak in heartrate_peaks:
        if 'converted' in peak.keys() and peak['converted'] is True:
            continue
        if peak['attribute'] == 'velocity_smooth':
            peak['value'] = 2.23694 * peak['value']
            peak['converted'] = True

    return sorted(
        heartrate_peaks,
        key=lambda i: i['value'], reverse=True
    )[0:limit]

@app.route('/hello/')
def hello(name=None):
    activity_type = request.args.get('type') or 'cycling'
    attribute = request.args.get('attribute') or 'watts'
    duration = request.args.get('duration') or 300
    limit = request.args.get('limit') or 10

    data = peaks_data(request, int(limit))
    for d in data:
        if isinstance(d['start_date_local'], datetime.datetime):
            continue
        d['start_date_local'] = datetime.datetime.strptime(
            d['start_date_local'], "%Y-%m-%dT%H:%M:%S%z")

    return render_template(
        'hello.html',
        durations=config()['PEAK_DURATIONS'],
        types=config()['TYPE'].keys(),
        attributes=config()['ATTRIBUTES'],
        data=data,
        type=activity_type,
        attribute=attribute,
        duration=int(duration),
        limit=int(limit)
    )


@app.route('/')
def peaks():
    return json.dumps(peaks_data(request, 100))
