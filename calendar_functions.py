import json
import os
from datetime import datetime, timedelta

# JSON 파일 경로
JSON_FILE = './data/events.json'


def load_events():
    """이벤트 데이터를 JSON 파일에서 로드."""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_events(events):
    """이벤트 데이터를 JSON 파일에 저장."""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=4, ensure_ascii=False)


def create_event(summary, start, end):
    """새로운 이벤트 생성."""
    events = load_events()
    event_id = str(len(events) + 1)  # 간단한 ID 생성
    new_event = {
        "id": event_id,
        "summary": summary,
        "start": start,
        "end": end,
        "created_at": datetime.now().isoformat(),
    }
    events.append(new_event)
    save_events(events)
    print(f"Event created: {new_event}")
    return new_event


def generate_schedule(book_title, days, time, weeks, contents):
    """학습 계획 생성 및 캘린더 이벤트 등록."""
    events = []
    total_sessions = weeks * len(days)
    per_session = len(contents) // total_sessions
    extra = len(contents) % total_sessions
    
    # 학습 시작 날짜 계산
    start_date = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))  # 다음 주 월요일
    session_contents = []
    
    for week in range(weeks):
        for day in days:
            day_offset = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}[day]
            session_date = start_date + timedelta(days=(day_offset - start_date.weekday()) % 7)
            start_time = session_date.strftime(f"%Y-%m-%dT{time}:00+09:00")
            end_time = session_date.strftime(f"%Y-%m-%dT{time}:30+09:00")

            # 이번 세션에 할당된 목차
            to_study = contents[:per_session]
            contents = contents[per_session:]
            if extra > 0:
                to_study.append(contents.pop(0))
                extra -= 1

            # 목차가 비어있는 경우를 방지
            if not to_study:
                continue

            summary = f"{book_title} 학습 ({', '.join(to_study)})"
            event = create_event(summary, start_time, end_time)
            events.append(event)
    
    return {
        "message": f"{book_title} 학습 일정이 성공적으로 생성되었습니다.",
        "events": events
    }
