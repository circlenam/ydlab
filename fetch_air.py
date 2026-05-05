import requests
import json
import os
from datetime import datetime

API_KEY = os.environ.get('AIRKOREA_KEY', '602d951dbed28048545dcbf3a9b8a3483185bdff37afa2eae5f516c741faeddd')
BASE = 'https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty'

STATIONS = [
    {'id': 'namdong',  'name': '남동구',   'area': '인천', 'station': '남동'},
    {'id': 'seo',      'name': '서구',     'area': '인천', 'station': '서구'},
    {'id': 'jung',     'name': '중구',     'area': '인천', 'station': '중구'},
    {'id': 'yeonsu',   'name': '연수구',   'area': '인천', 'station': '연수'},
    {'id': 'bupyeong', 'name': '부평구',   'area': '인천', 'station': '부평'},
    {'id': 'gyeyang',  'name': '계양구',   'area': '인천', 'station': '계양'},
    {'id': 'ansan',    'name': '단원구',   'area': '안산', 'station': '안산'},
    {'id': 'sihwa',    'name': '시화산단', 'area': '시흥', 'station': '시흥'},
]

def fetch(station_name):
    params = {
        'stationName': station_name,
        'dataTerm': 'DAILY',
        'pageNo': 1,
        'numOfRows': 1,
        'returnType': 'json',
        'serviceKey': API_KEY,
        'ver': '1.3'
    }
    try:
        r = requests.get(BASE, params=params, timeout=10)
        data = r.json()
        item = data['response']['body']['items'][0]
        return {
            'pm25': float(item.get('pm25Value') or 0),
            'pm10': float(item.get('pm10Value') or 0),
            'no2':  float(item.get('no2Value')  or 0),
            'so2':  float(item.get('so2Value')  or 0),
            'o3':   float(item.get('o3Value')   or 0),
            'co':   float(item.get('coValue')   or 0),
        }
    except Exception as e:
        print(f'  ERROR {station_name}: {e}')
        return None

def risk(pm25):
    if pm25 >= 50: return 'vhigh'
    if pm25 >= 35: return 'high'
    if pm25 >= 15: return 'mid'
    return 'low'

result = {
    'updated': datetime.now().strftime('%Y-%m-%d %H:%M KST'),
    'source': '한국환경공단 에어코리아',
    'stations': []
}

for s in STATIONS:
    print(f'Fetching {s["station"]}...')
    live = fetch(s['station'])
    entry = {**s}
    if live and live['pm25'] > 0:
        entry.update(live)
        entry['risk'] = risk(live['pm25'])
        entry['live'] = True
        print(f'  OK: PM2.5={live["pm25"]}')
    else:
        entry['live'] = False
        print(f'  FALLBACK')
    result['stations'].append(entry)

os.makedirs('data', exist_ok=True)
with open('data/airdata.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

live_count = sum(1 for s in result['stations'] if s.get('live'))
print(f'\n완료: {live_count}/{len(STATIONS)}개소 실측 데이터 수집')
print(f'업데이트: {result["updated"]}')
