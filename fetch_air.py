import requests
import json
import os
from datetime import datetime

API_KEY = os.environ.get('AIRKOREA_KEY', '602d951dbed28048545dcbf3a9b8a3483185bdff37afa2eae5f516c741faeddd')
BASE = 'https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty'

# 지역별 후보 측정소명 여러 개 시도
STATIONS = [
    {'id': 'namdong',  'name': '남동구',   'area': '인천', 'candidates': ['구월', '남동', '논현', '남동구']},
    {'id': 'seo',      'name': '서구',     'area': '인천', 'candidates': ['서구', '청라', '검단', '오류']},
    {'id': 'jung',     'name': '중구',     'area': '인천', 'candidates': ['중구', '항동', '신흥', '인천중구']},
    {'id': 'yeonsu',   'name': '연수구',   'area': '인천', 'candidates': ['연수', '송도', '옥련', '연수구']},
    {'id': 'bupyeong', 'name': '부평구',   'area': '인천', 'candidates': ['부평', '갈산', '부평구', '산곡']},
    {'id': 'gyeyang',  'name': '계양구',   'area': '인천', 'candidates': ['계양', '계산', '계양구', '효성']},
    {'id': 'ansan',    'name': '단원구',   'area': '안산', 'candidates': ['안산', '단원', '선부', '고잔', '원곡']},
    {'id': 'sihwa',    'name': '시화산단', 'area': '시흥', 'candidates': ['정왕', '시흥', '월곶', '시화', '능곡']},
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
        items = data['response']['body']['items']
        if items and isinstance(items, list) and len(items) > 0:
            item = items[0]
            pm25 = item.get('pm25Value', '-')
            if pm25 and pm25 != '-' and pm25 != '':
                return {
                    'pm25': float(pm25),
                    'pm10': float(item.get('pm10Value') or 0),
                    'no2':  float(item.get('no2Value')  or 0),
                    'so2':  float(item.get('so2Value')  or 0),
                    'o3':   float(item.get('o3Value')   or 0),
                    'co':   float(item.get('coValue')   or 0),
                    'station_matched': station_name
                }
        return None
    except Exception as e:
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

print('=' * 50)
print(f'에어코리아 수집 시작: {result["updated"]}')
print('=' * 50)

for s in STATIONS:
    print(f'\n[{s["area"]} {s["name"]}] 탐색 중...')
    entry = {k: v for k, v in s.items() if k != 'candidates'}
    live_data = None

    for candidate in s['candidates']:
        data = fetch(candidate)
        if data:
            live_data = data
            print(f'  OK: "{candidate}" PM2.5={data["pm25"]}')
            break
        else:
            print(f'  FAIL: "{candidate}"')

    if live_data:
        entry.update(live_data)
        entry['risk'] = risk(live_data['pm25'])
        entry['live'] = True
    else:
        entry['live'] = False
        print(f'  WARNING: 폴백 사용')

    result['stations'].append(entry)

os.makedirs('data', exist_ok=True)
with open('data/airdata.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

live_count = sum(1 for s in result['stations'] if s.get('live'))
print(f'\n완료: {live_count}/{len(STATIONS)}개소 실측')
print(f'[측정소명 매칭 결과]')
for s in result['stations']:
    m = s.get('station_matched', '폴백')
    status = f'OK ({m})' if s.get('live') else 'FALLBACK'
    print(f'  {s["area"]} {s["name"]}: {status}')
