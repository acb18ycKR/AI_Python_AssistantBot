import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
        
# 파일 경로 설정
CALENDAR_FILE = './data/calendar.json'
CHAT_LOG_FILE = './data/chat_log.json'
CONTENTS_FILE = './data/contents.md'


# 목차 로드 함수
def load_contents():
    """contents.md 파일에서 목차를 읽어옵니다."""
    print("load_contents: 목차 파일 로드 시작.")
    if os.path.exists(CONTENTS_FILE):
        with open(CONTENTS_FILE, 'r', encoding='utf-8') as f:
            contents = [line.strip() for line in f if line.strip()]
            print(f"load_contents: {len(contents)}개의 항목 로드 완료.")
            return contents
    raise FileNotFoundError(f"{CONTENTS_FILE} 파일을 찾을 수 없습니다.")


# JSON 파일 초기화 함수
def initialize_files():
    """필요한 JSON 파일을 초기화합니다."""
    print("initialize_files: 초기화 시작.")
    os.makedirs('./data', exist_ok=True)
    if not os.path.exists('./data/calendar.json'):
        with open('./data/calendar.json', 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        print("initialize_files: calendar.json 파일 생성 완료.")
    if not os.path.exists('./data/chat_log.json'):
        with open('./data/chat_log.json', 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        print("initialize_files: chat_log.json 파일 생성 완료.")


# ⭐ 항상 이전 대화와 일정을 MESSAGES에 추가하는 함수 ⭐
# 대화 내용 저장
def save_chat_log(user_id, message, role="user"):
    """대화 내용을 JSON 파일에 저장합니다."""
    print("save_chat_log: 대화 저장 시작.")
    with open(CHAT_LOG_FILE, 'r+', encoding='utf-8') as f:
        try:
            data = json.load(f)
            print(f"save_chat_log: 기존 대화 {len(data)}개 로드.")
        except json.JSONDecodeError:
            data = []
            print("save_chat_log: 기존 파일이 비어 있습니다.")
        
        data.append({
            "user_id": user_id,
            "role": role,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        print(f"save_chat_log: 대화 저장 완료. 총 {len(data)}개의 대화.")
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_previous_data_to_messages(messages):
    """
    이전 대화와 일정을 MESSAGES에 추가합니다.
    max_logs: 최근 대화 최대 개수
    """
    # 최근 대화 기록 추가
    try:
        with open(CHAT_LOG_FILE, 'r', encoding='utf-8') as f:
            chat_logs = json.load(f)
            recent_logs = chat_logs  # 최근 max_logs 개 대화만 유지
            previous_chats = "\n".join(
                f"{log['role']}: {log['message']} ({log['timestamp']})"
                for log in recent_logs
            )
            messages.append({
                "role": "system",
                "content": f"🗨️ 최근 대화 기록:\n{previous_chats}"
            })

            print(f'recent_logs : {recent_logs}')
    except (FileNotFoundError, json.JSONDecodeError):
        print("add_previous_data_to_messages: 이전 대화 기록이 없거나 파일이 비어 있습니다.")

    # 일정 정보 추가
    try:
        with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
            schedule = json.load(f)
            if schedule:
                formatted_schedule = "\n".join(
                    f"📅 {event['date']} {event['summary']}" for event in schedule
                )
                messages.append({
                    "role": "system",
                    "content": f"📅 저장된 일정:\n{formatted_schedule}"
                })
    except (FileNotFoundError, json.JSONDecodeError):
        print("add_previous_data_to_messages: 저장된 일정이 없거나 파일이 비어 있습니다.")