import requests
from datetime import  datetime, date, time

r = requests.get("http://localhost:6800/listspiders.json?project=default")

data = r.json()

# Create a cycleid for each run using date and time of run
date_list = str(date.today()).split("-")
now = datetime.now()
current_time = now.strftime("%H%M")

cycleid = f"{date_list[0]}{date_list[1]}{date_list[2]}{current_time}"

for s in data.get('spiders'):
    if s in ['azrieli']:
        payload = {'project': 'coupons', 'spider': f'{s}', 'cycleid': f'{cycleid}'}
        r = requests.post("http://localhost:6800/schedule.json",data=payload)