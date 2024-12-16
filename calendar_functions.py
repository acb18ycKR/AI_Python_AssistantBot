
import json
import os
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_bolt import App
from openai import OpenAI
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# 파일 경로 설정
CALENDAR_FILE = './data/calendar.json'
CHAT_LOG_FILE = './data/chat_log.json'
CONTENTS_FILE = './data/contents.md'

# 환경 변수 로드
load_dotenv()
app = App(token=os.environ['SLACK_BOT_TOKEN'])
slack_client = WebClient(os.environ['SLACK_BOT_TOKEN'])

# OpenAI 초기화
api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key
client = OpenAI()

# JSON 파일 저장 함수
def save_schedule_to_json(schedule, output_path=CALENDAR_FILE):
    """일정을 JSON 파일에 저장합니다."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=4)


# 목차 파일 로드 함수
def load_contents(file_path):
    """목차 파일(contents.md)을 읽어옵니다."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    raise FileNotFoundError(f"{file_path} 파일을 찾을 수 없습니다.")


# 일정 포매팅
def format_schedule(schedule):
    """일정 데이터를 요약하여 반환."""
    formatted = []
    for event in schedule:
        # 요약된 일정 데이터 생성
        summary = event['summary'].split(", ")[:3]  # 최대 3개의 목차만 포함
        formatted.append(f"📅 {event['date']} - {', '.join(summary)}")
    return "\n".join(formatted)


# 일정 로드 함수 조회
def load_schedule_from_json():
    """JSON 파일에서 일정을 불러옵니다."""
    print("load_schedule_from_json: 일정 로드 시작.")
    with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            print(f"load_schedule_from_json: {len(data)}개의 일정 로드 완료.")
            return data
        except json.JSONDecodeError:
            print("load_schedule_from_json: 파일이 비어 있습니다.")
            return []

#일정 수정, 일정 삭제, 일정 리마인더 (슬랙 알람), 진행률 보기

# TODO : 수정 기능 TEST - 완료 
# 일정 수정 기능 : 새로운 작업 추가 기능, 일정 이동 기능
# @test-assistant 일정 수정 2024-12-10 01-6 파이썬과 에디터
# @test-assistant 일정 수정 2024-12-10 01-6 파이썬과 에디터 2024-12-11
# 일정 수정 함수
def update_schedule(date, updated_task, new_date=None, new_time=None):
    """
    특정 날짜의 일정을 수정하거나 새 일정으로 추가합니다.
    Args:
        date (str): 기존 일정이 있는 날짜 (예: '2024-12-10').
        updated_task (str): 수정할 작업 이름 (예: '01-6 파이썬과 에디터').
        new_date (str, optional): 이동할 새 날짜 (예: '2024-12-11'). 없으면 같은 날짜에 추가.
        new_time (str, optional): 새로운 시작 시간 (예: '10:00').
    """
    schedule = load_schedule_from_json()
    task_found = False  # 기존 날짜에서 작업 존재 여부

    # 기존 날짜에서 작업 검색 및 삭제
    for event in schedule:
        if event["date"] == date:
            tasks = event["summary"].replace("학습 계획: ", "").split(", ")
            if updated_task in tasks:
                # 기존 작업 삭제
                tasks.remove(updated_task)
                task_found = True
                if tasks:
                    event["summary"] = "학습 계획: " + ", ".join(tasks)
                else:
                    # 모든 작업이 삭제되면 해당 날짜의 일정을 삭제
                    schedule.remove(event)
                break

    # 작업이 기존 날짜에 없으면 오류 메시지를 출력하지 않고 새 작업으로 추가
    if not task_found:
        print(f"{date}에 '{updated_task}' 작업이 존재하지 않아 새로 추가합니다.")

    # 새 날짜로 이동하거나 추가
    target_date = new_date if new_date else date
    for event in schedule:
        if event["date"] == target_date:
            tasks = event["summary"].replace("학습 계획: ", "").split(", ")
            tasks.append(updated_task)
            event["summary"] = "학습 계획: " + ", ".join(tasks)
            if new_time:
                event["start_time"] = new_time
            save_schedule_to_json(schedule)
            return f"'{updated_task}' 작업이 {date}에서 {target_date}로 이동/추가되었습니다."

    # 새 날짜에 새 일정 추가
    schedule.append({
        "date": target_date,
        "start_time": new_time if new_time else "09:00",  # 기본 시작 시간
        "summary": f"학습 계획: {updated_task}",
        "progress": 0.0
    })
    save_schedule_to_json(schedule)
    return f"'{updated_task}' 작업이 {target_date}에 새로 추가되었습니다."



# 일정 삭제 기능
# TODO : 날짜의 전체 일정 삭제 - 완료
# TODO : 날짜의 특정 학습 계획 삭제 - 완료
# 일정 삭제 기능
# 일정 삭제 기능
def delete_schedule(date=None, task=None, delete_all=False):
    """
    특정 날짜의 일정을 삭제하거나 특정 작업만 삭제하거나 전체 일정을 삭제합니다.
    Args:
        date (str, optional): 삭제할 날짜 (예: '2024-12-10').
        task (str, optional): 삭제할 특정 작업 이름 (예: '01-6 파이썬과 에디터').
        delete_all (bool, optional): True이면 전체 일정을 삭제.
    Returns:
        str: 삭제 결과 메시지.
    """
    schedule = load_schedule_from_json()

    if delete_all:
        # 전체 일정 삭제
        save_schedule_to_json([])  # 빈 리스트 저장
        return "모든 일정이 삭제되었습니다."

    if not date:
        return "삭제할 날짜를 입력해 주세요."

    updated_schedule = []
    task_found = False

    for event in schedule:
        if event["date"] == date:
            tasks = event["summary"].replace("학습 계획: ", "").split(", ")
            if task:  # 특정 작업 삭제
                if task in tasks:
                    tasks.remove(task)
                    task_found = True
                    if tasks:  # 다른 작업이 남아 있으면 업데이트
                        event["summary"] = "학습 계획: " + ", ".join(tasks)
                        updated_schedule.append(event)
                else:
                    updated_schedule.append(event)  # 작업이 없을 경우 일정 그대로 유지
            else:  # 날짜 전체 삭제
                task_found = True  # 전체 일정 삭제
        else:
            updated_schedule.append(event)  # 해당 날짜가 아닌 일정은 그대로 유지

    # 결과 저장
    save_schedule_to_json(updated_schedule)

    # 결과 메시지 생성
    if task:
        if task_found:
            return f"'{task}' 작업이 {date}에서 삭제되었습니다."
        else:
            return f"⚠️ {date}에 '{task}' 작업이 없습니다."
    else:
        if task_found:
            return f"✅ {date}의 모든 일정이 삭제되었습니다."
        else:
            return f"⚠️ {date}에 해당하는 일정이 없습니다."


# TODO : 일정별 리마인더 기능 구현 
# TODO : 리마인더 설정시 "start_time": "21:18" start time에 알람 설정 시간이 저장이되는 문제 해결
# TODO : 초기에 일정 생성시, 알림을 설정하시겠습니까? 라는 안내 문구가 나오고 예, 아니오로 답하여 알림 기능 설정
# TODO : 알림 끄기 기능 설정
# 일정 리마인더 기능
def send_reminder_to_slack(channel, date):
    """특정 날짜의 일정을 슬랙으로 알림 보냅니다."""
    schedule = load_schedule_from_json()
    for event in schedule:
        if event["date"] == date:
            message = f"📅 리마인더: {event['date']} - {event['summary']}"
            slack_client.chat_postMessage(channel=channel, text=message)
            print(f"리마인더 전송 완료: {message}")
            return f"{date}의 일정 리마인더가 슬랙으로 전송되었습니다."
    return f"{date}에 해당하는 일정이 없습니다."

# 진행률 보기
def view_progress():
    """전체 일정의 평균 진행률과 오늘 진행률을 계산합니다."""
    schedule = load_schedule_from_json()
    if not schedule:
        return "저장된 일정이 없습니다."

    # 오늘 날짜 계산
    today = datetime.now().strftime("%Y-%m-%d")

    # 전체 진행률 계산 변수
    total_tasks = 0
    completed_tasks = 0
    today_total_tasks = 0
    today_completed_tasks = 0

    for event in schedule:
        # 작업 목록 추출
        tasks = event["summary"].replace("학습 계획: ", "").split(", ")

        for task in tasks:
            total_tasks += 1
            if "(완료)" in task:  # 완료된 작업 확인
                completed_tasks += 1

            # 오늘 날짜의 작업 처리
            if event["date"] == today:
                today_total_tasks += 1
                if "(완료)" in task:
                    today_completed_tasks += 1

    # 전체 평균 진행률 계산
    if total_tasks == 0:
        average_progress = 0
    else:
        average_progress = (completed_tasks / total_tasks) * 100

    # 오늘 진행률 계산
    if today_total_tasks == 0:
        today_progress = 0
    else:
        today_progress = (today_completed_tasks / today_total_tasks) * 100

    # 결과 반환
    print(f"전체 평균 진행률: {average_progress:.2f}%, 오늘 진행률: {today_progress:.2f}%")
    return (
        f"현재 전체 평균 진행률은 {average_progress:.2f}%입니다.\n"
        f"오늘({today})의 진행률은 {today_progress:.2f}%입니다."
    )

def update_task_progress(date, task_name):
    """특정 날짜의 특정 작업에 대해 진행률을 업데이트합니다."""
    schedule = load_schedule_from_json()
    found = False  # 해당 작업이 존재하는지 여부
    completed_tasks = 0
    total_tasks = 0

    for event in schedule:
        if event["date"] == date:
            # '학습 계획: ' 제거 및 작업 단위로 분리
            tasks = event["summary"].replace("학습 계획: ", "").split(", ")
            total_tasks = len(tasks)

            # 특정 작업의 진행률 업데이트
            updated_tasks = []
            for task in tasks:
                # 작업 이름 비교 (공백 제거 및 대소문자 무시)
                if task.strip().lower() == task_name.strip().lower():
                    updated_tasks.append(f"{task} (완료)")
                    completed_tasks += 1
                    found = True
                else:
                    if "(완료)" in task:
                        completed_tasks += 1
                    updated_tasks.append(task)

            # 수정된 summary를 다시 문자열로 저장
            event["summary"] = "학습 계획: " + ", ".join(updated_tasks)

    if not found:
        return f"{date}에 '{task_name}' 작업이 없습니다."

    # 전체 진행률 계산
    overall_progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    event["progress"] = overall_progress

    save_schedule_to_json(schedule)
    print(f"{date}의 '{task_name}' 학습 완료. 전체 학습률: {overall_progress:.2f}%")
    return f"{date}의 '{task_name}' 학습을 완료했습니다..\n현재 전체 학습 진행률은 {overall_progress:.2f}%입니다."

# def update_task_progress(date, task_name):
#     """특정 날짜의 특정 작업에 대해 진행률을 업데이트합니다."""
#     schedule = load_schedule_from_json()
#     found = False  # 해당 작업이 존재하는지 여부
#     completed_tasks = 0
#     total_tasks = 0

#     for event in schedule:
#         if event["date"] == date:
#             # '학습 계획: ' 제거 및 작업 단위로 분리
#             tasks = event["summary"].replace("학습 계획: ", "").split(", ")
#             total_tasks = len(tasks)

#             # 특정 작업의 진행률 업데이트
#             updated_tasks = []
#             for task in tasks:
#                 if task == task_name:
#                     updated_tasks.append(f"{task} (완료)")
#                     completed_tasks += 1
#                     found = True
#                 else:
#                     if "(완료)" in task:
#                         completed_tasks += 1
#                     updated_tasks.append(task)

#             # 수정된 summary를 다시 문자열로 저장
#             event["summary"] = "학습 계획: " + ", ".join(updated_tasks)

#     if not found:
#         return f"{date}에 '{task_name}' 작업이 없습니다."

#     # 전체 진행률 계산
#     overall_progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
#     event["progress"] = overall_progress

#     save_schedule_to_json(schedule)

#     return f"{date}의 '{task_name}' 학습을 완료했습니다.\n현재 전체 학습 진행률은 {overall_progress:.2f}%입니다."


# 스케줄러 초기화
scheduler = BackgroundScheduler()
scheduler.start()


# 리마인더 예약 함수
# 전체 일정에 대한 리마인더
def schedule_all_reminders(channel, slack_client, hours_before=1):
    """모든 일정에 대해 리마인더를 예약하고 JSON 데이터에 추가합니다."""
    schedule = load_schedule_from_json()

    for event in schedule:
        # 날짜와 시간 계산
        event_datetime = datetime.strptime(f"{event['date']} {event['start_time']}", "%Y-%m-%d %H:%M")
        reminder_time = event_datetime - timedelta(hours=hours_before)

        # 현재 시간 기준 확인
        if reminder_time < datetime.now():
            print(f"예약 시간 경과: {event['date']} - {event['start_time']} - 알람 설정 생략")
            continue

        # 리마인더 시간 추가
        event['reminder_date'] = reminder_time.strftime("%Y-%m-%d")
        event['reminder_time'] = reminder_time.strftime("%H:%M")

        # 리마인더 전송 함수
        def send_reminder(event=event):
            message = f"📅 리마인더: {event['reminder_date']} {event['reminder_time']} - 학습 계획: {event['summary']}"
            slack_client.chat_postMessage(channel=channel, text=message)
            print(f"리마인더 전송 완료: {message}")

        # 예약 작업 추가
        scheduler.add_job(
            send_reminder,
            'date',
            run_date=reminder_time
        )
        print(f"리마인더 예약 완료: {event['date']} {event['start_time']} - 알람 시간: {reminder_time}")

    # JSON 파일에 업데이트된 데이터 저장
    save_schedule_to_json(schedule)



# 특정 날짜 일정에 대한 리마인더
def schedule_specific_reminder(channel, slack_client, target_date, hours_before=1):
    """특정 날짜의 일정에 대해 리마인더를 예약하고 JSON 데이터에 추가합니다."""
    schedule = load_schedule_from_json()

    # 특정 날짜 일정 필터링
    filtered_events = [event for event in schedule if event["date"] == target_date]

    if not filtered_events:
        # 해당 날짜에 일정이 없는 경우
        slack_client.chat_postMessage(
            channel=channel,
            text=f"⚠️ {target_date}에 일정이 없습니다. 올바른 날짜를 입력하세요."
        )
        return

    for event in filtered_events:
        # 날짜와 시간 계산
        event_datetime = datetime.strptime(f"{event['date']} {event['start_time']}", "%Y-%m-%d %H:%M")
        reminder_time = event_datetime - timedelta(hours=hours_before)

        # 현재 시간 기준 확인
        if reminder_time < datetime.now():
            print(f"예약 시간 경과: {event['date']} - {event['start_time']} - 알람 설정 생략")
            continue

        # 리마인더 시간 추가
        event['reminder_date'] = reminder_time.strftime("%Y-%m-%d")
        event['reminder_time'] = reminder_time.strftime("%H:%M")

        # 리마인더 전송 함수
        def send_reminder(event=event):
            message = f"📅 리마인더: {event['reminder_date']} {event['reminder_time']} - 학습 계획: {event['summary']}"
            slack_client.chat_postMessage(channel=channel, text=message)
            print(f"리마인더 전송 완료: {message}")

        # 예약 작업 추가
        scheduler.add_job(
            send_reminder,
            'date',
            run_date=reminder_time
        )
        print(f"리마인더 예약 완료: {event['date']} {event['start_time']} - 알람 시간: {reminder_time}")

    # JSON 파일에 업데이트된 데이터 저장
    save_schedule_to_json(schedule)
