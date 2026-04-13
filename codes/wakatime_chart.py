import os
import datetime
import requests
import asciichartpy as ac
import sys
import base64

NDAYS = 30
HEIGHT = 15

def get_summaries(start_date, end_date, headers):
    url = f"https://wakatime.com/api/v1/users/current/summaries?start={start_date}&end={end_date}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching summaries: {response.status_code}", file=sys.stderr)
        if response.status_code == 401:
            print("WAKATIME_API_KEY is invalid or expired.", file=sys.stderr)
        sys.exit(1)
    return response.json()

def get_durations(date_str, headers):
    url = f"https://wakatime.com/api/v1/users/current/durations?date={date_str}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get('data', [])

def classify_productivity(durations_list):
    early_bird_seconds = 0
    night_owl_seconds = 0

    for date_str, durations in durations_list.items():
        for chunk in durations:
            start_time = datetime.datetime.fromtimestamp(chunk['time'])
            duration_secs = chunk['duration']
            hour = start_time.hour

            if 6 <= hour < 18:
                early_bird_seconds += duration_secs
            else:
                night_owl_seconds += duration_secs

    if early_bird_seconds >= night_owl_seconds:
        return "Early Bird 🌅"
    else:
        return "Night Owl 🦉"

def main():
    api_key = os.getenv("WAKATIME_API_KEY")

    if not api_key:
        print("Error: WAKATIME_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    auth_header = "Basic " + base64.b64encode(api_key.encode("utf-8")).decode("utf-8")
    headers = {"Authorization": auth_header}

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=NDAYS - 1)

    summaries_data = get_summaries(start_date.isoformat(), end_date.isoformat(), headers)

    daily_hours = []
    for day_summary in summaries_data.get('data', []):
        total_seconds = day_summary['grand_total']['total_seconds']
        hours = total_seconds / 3600.0
        daily_hours.append(hours)

    durations_dict = {}
    duration_start_date = end_date - datetime.timedelta(days=6)
    for i in range(7):
        ds = duration_start_date + datetime.timedelta(days=i)
        d_str = ds.isoformat()
        durations_dict[d_str] = get_durations(d_str, headers)

    classifier = classify_productivity(durations_dict)

    chart_config = {
        'height': HEIGHT,
        'format': '{:8.2f}'
    }

    if len(daily_hours) == 0:
        daily_hours = [0] * NDAYS

    chart = ac.plot(daily_hours, chart_config)

    print(f"# ⏱️ WakaTime Coding Hours (Last {NDAYS} Days) #\n")
    print(f"**Activity Profile:** {classifier}\n")
    print("Hours Coded")
    print(chart)

if __name__ == "__main__":
    main()
