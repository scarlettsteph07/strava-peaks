
def config():
    return {
        'PEAK_DURATIONS': [5, 60, 300, 600, 1200, 3600, 5400],
        'TYPE': {'rowing': ['Rowing'], 'cycling': ['VirtualRide', 'Ride']},
        'ATTRIBUTES': ['heartrate', 'watts', 'velocity_smooth']
    }
