from datetime import datetime, timedelta

# 목차 파일 경로
file_path = r"C:\Users\RMARKET\workspace\projects\AI_Python_AssistantBot\data\contents.md"
calendar_file = "./test_calendar.json"  # 테스트용 일정 파일 경로



# 시간 형식 변환 함수
def convert_time_format(time_str):
    """오전/오후 시간을 %H:%M 형식으로 변환."""
    time_str = time_str.strip()
    if "오전" in time_str:
        hour = int(time_str.replace("오전", "").replace("시", "").strip())
        if hour == 12:
            hour = 0
        return f"{hour:02d}:00"
    elif "오후" in time_str:
        hour = int(time_str.replace("오후", "").replace("시", "").strip())
        if hour != 12:
            hour += 12
        return f"{hour:02d}:00"
    elif ":" in time_str:
        return time_str
    raise ValueError(f"유효하지 않은 시간 형식입니다: {time_str}")

# 입력 파싱 함수
def parse_input(prompt):
    """입력 문자열을 파싱하여 days, time, weeks를 추출합니다."""
    days = [day for day in ["월", "화", "수", "목", "금", "토", "일"] if day in prompt]
    time = None
    weeks = None

    for word in prompt.split():
        if ":" in word or ("오전" in word or "오후" in word):
            time = convert_time_format(word.strip())

    for word in prompt.split():
        if "주" in word:
            weeks = int(word.replace("주", "").strip())
    
    if not days or not time or not weeks:
        raise ValueError(f"올바르지 않은 입력 형식입니다: {prompt}")
    
    return days, time, weeks


# 일정 생성 함수
def generate_schedule(days, time, weeks, contents):
    """학습 계획을 생성하고 저장합니다."""
    schedule = []
    total_sessions = weeks * len(days)
    per_session = len(contents) // total_sessions
    extra = len(contents) % total_sessions

    content_index = 0
    study_time = datetime.strptime(time, "%H:%M").time()
    today = datetime.now()
    start_date = today + timedelta(days=(7 - today.weekday()))  # 다음 주 월요일 기준 시작 날짜

    for week in range(weeks):
        for day in days:
            if content_index >= len(contents):
                break
            day_offset = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}[day]
            session_date = start_date + timedelta(days=(week * 7) + (day_offset - start_date.weekday()) % 7)
            start_datetime = datetime.combine(session_date, study_time)
            session_contents = contents[content_index:content_index + per_session]
            content_index += per_session

            if extra > 0:
                session_contents.append(contents[content_index])
                content_index += 1
                extra -= 1

            schedule.append({
                "date": session_date.strftime("%Y-%m-%d"),
                "start_time": start_datetime.strftime("%H:%M"),
                "summary": f"학습 계획: {', '.join(session_contents)}"
            })

    if content_index < len(contents):
        remaining_contents = contents[content_index:]
        last_date = start_date + timedelta(days=(weeks * 7))
        start_datetime = datetime.combine(last_date, study_time)
        schedule.append({
            "date": last_date.strftime("%Y-%m-%d"),
            "start_time": start_datetime.strftime("%H:%M"),
            "summary": f"학습 계획: {', '.join(remaining_contents)}"
        })
    return schedule