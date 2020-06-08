import requests
import yaml
from stravaio import StravaIO
from datetime import datetime
import time
from dotenv import load_dotenv
import os
load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
PEAK_DURATIONS = [5, 60, 300, 600, 1200, 3600, 5400]
TYPE = {'rowing': ['Rowing'], 'cycling': ['VirtualRide', 'Ride']}


def calc_peak(num_seconds, data_stream, activity_id):
    if len(data_stream) == 0:
        return 0
    if num_seconds > len(data_stream):
        return None
    sums = []
    for w in range(len(data_stream)):
        if w + num_seconds > len(data_stream):
            break

        try:
            sums.append(sum(data_stream[w:w + num_seconds]))
        except:
            print('unable to sum datastream for {}'.format(activity_id))
            return 0
    peak_total = sorted(sums)[-1]
    return peak_total // num_seconds


def fill_values(time_stream, data_stream):
    new_data_stream = []
    if len(time_stream) != len(data_stream):
        return None
    if len(time_stream) == len(data_stream):
        return data_stream
    for i in range(0, len(time_stream) - 1):
        if i == len(time_stream):
            continue
        new_data_stream.append(data_stream[i])
        time_diff = time_stream[i + 1] - time_stream[i]
        if time_diff > 1:
            data_diff = data_stream[i + 1] - data_stream[i]
            for j in range(1, time_diff):
                new_data_stream.append(
                    data_stream[i] + ((data_diff / time_diff) * j))
    return new_data_stream


def main():
    user_file = open(os.getenv("DATA_FILE"))
    user_data = yaml.load(user_file, Loader=yaml.FullLoader)
    user_file.close()

    if datetime.now().timestamp() > user_data['strava_token_expiration']:
        print('refreshing token')
        data = {
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': user_data['strava_refresh_token']
        }

        r = requests.post(
            'https://www.strava.com/api/v3/oauth/token', data=data)
        print(r.json())
        user_data['strava_token_expiration'] = r.json()['refresh_token']
        user_data['strava_access_token'] = r.json()['access_token']
        user_data['strava_token_expiration'] = r.json()['expires_at']

    client = StravaIO(
        access_token=user_data['strava_access_token'])
    activities = client.get_logged_in_athlete_activities(after='06/01/2020')
    for activity in activities:
        if user_data['processed_activities'] is None:
            user_data['processed_activities'] = []
        streams = None
        if activity.id in user_data['processed_activities']:
            print('skipped activity {} since it has been processed'.format(activity.id))
            continue
        try:
            time.sleep(5)
            streams = client.get_activity_streams(
                activity.id, user_data['athlete_id'])
        except:
            print('error getting streams for activity {}'.format(
                activity.id))
            user_data['processed_activities'].append(activity.id)
            continue
        if streams is None:
            print('Streams is null')
            continue
        time_stream = streams.time
        activity_types = [
            k for k, item in TYPE.items() if activity.type in item]
        print(activity_types)

        if len(activity_types) == 0:
            continue
        activity_key = activity_types[0]

        for statistic in ['heartrate', 'watts', 'velocity_smooth']:
            for duration in PEAK_DURATIONS:
                data_stream = streams._get_stream_by_name(statistic)
                if data_stream is None:
                    continue
                normalized_stream = fill_values(time_stream, data_stream)
                # print(normalized_stream)
                peak_value = calc_peak(
                    duration, normalized_stream, activity.id)
                if peak_value is None:
                    continue

                if user_data[activity_key] is None:
                    user_data[activity_key] = []

                user_data[activity_key].append({
                    'activity_id': activity.id,
                    'name': activity.name,
                    'duration': duration,
                    'value': peak_value,
                    'attribute': statistic,
                    'start_date_local': activity.start_date_local.isoformat()
                })

        user_data['processed_activities'].append(activity.id)
        user_file = open(os.getenv("DATA_FILE"), 'w')
        user_file.write(yaml.dump(user_data, sort_keys=True))
        user_file.close()

main()
