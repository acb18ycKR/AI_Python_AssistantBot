import os
import datetime
from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
from dotenv import load_dotenv
from chat_functions import load_contents, initialize_files, save_chat_log, add_previous_data_to_messages
from calendar_functions import delete_schedule, update_schedule,  view_progress, update_task_progress, schedule_all_reminders, save_schedule_to_json
from calendar_functions import  format_schedule, schedule_specific_reminder, load_schedule_from_json
from create_calender import generate_schedule, parse_input
# from rag_functions import initialize_rag_system
from raptor_rag_functions import generate_raptor_rag_answer, initialize_raptor_rag_system
# 환경 변수 로드
load_dotenv()

# 목차 로드
try:
    CONTENTS = load_contents()
    CONTENTS_TEXT = "\n".join(CONTENTS)
except FileNotFoundError:
    CONTENTS = []
    CONTENTS_TEXT = "목차 파일(contents.md)을 찾을 수 없습니다. 파일을 추가하고 다시 시도해주세요."
MAX_MESSAGE_HISTORY = 10  # 메시지 히스토리를 10개로 제한
# Slack 및 GPT 설정
MESSAGES = [
    {
        "role": "system",
        "content": (
            "너는 학습 플래너로서 사용자가 제공한 학습 목차에 기반하여 학습 일정을 생성, 조회, 수정, 리마인더 설정, 진행률 입력 및 조회를 그리고 용어 사전과 퀴즈를 지원하는 역할이야.  \n\n"
            "첫 대화가 시작되면 아래처럼 안내를 해줘:\n"
            "안녕하세요. 저는 학습 플래너 챗봇이에요🤖 \n\n"
            "아래의 기능을 사용할 수 있어요:\n"
            "- 일정 생성: '일정 생성'을 입력해주세요.\n"
            "- 일정 조회: '일정 조회'를 입력해주세요.\n"
            "- 일정 수정: '일정 수정'을 입력해주세요.\n"
            "- 리마인더 설정: '리마인더 예약' 또는 '리마인더 예약 전체'를 입력해주세요.\n"
            "- 진행률 입력: '진행률 입력'을 입력해주세요.\n"
            "- 진행률 보기: '진행률 보기'를 입력해주세요.\n\n"
            "- 용어 사전\n"
            "- 퀴즈\n"
            "반드시 아래 목차만 활용해서 답변해야 해:\n\n"
            f"{CONTENTS_TEXT}\n\n"
            "질문에 친절하고 명확하게 답변하고, 필요시 추가 정보를 요청하도록 해."
        )
    }
]

def manage_message_history(messages):
    """메시지 히스토리를 제한하여 토큰 초과를 방지."""
    if len(messages) > MAX_MESSAGE_HISTORY:
        messages = messages[-MAX_MESSAGE_HISTORY:]  # 최근 MAX_MESSAGE_HISTORY 개 메시지만 유지
    return messages

def summarize_messages(messages):
    """기존 메시지 내용을 요약하여 시스템 메시지로 추가."""
    if len(messages) > MAX_MESSAGE_HISTORY:
        summary = "사용자와의 이전 대화 요약: "
        summary += " ".join([m["content"] for m in messages[:-MAX_MESSAGE_HISTORY]])
        messages = messages[-MAX_MESSAGE_HISTORY:]
        messages.insert(0, {"role": "system", "content": summary})
    return messages

app = App(token=os.environ['SLACK_BOT_TOKEN'])
slack_client = WebClient(os.environ['SLACK_BOT_TOKEN'])

# OpenAI 초기화
api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key
client = OpenAI()


# 
# 유저 입력 저장용 변수# RAG 시스템 초기화
RAG_PDF_PATH = r"C:\Users\RMARKET\workspace\projects\AI_Python_AssistantBot\data\converted_data_with_metadata.pdf"

# try:
#     print("🔧 RAG 시스템 초기화 중...")
#     rag_chain = initialize_raptor_rag_system(RAG_PDF_PATH)
#     print("✅ RAG 시스템 초기화 완료!")
# except Exception as e:
#     rag_chain = None
#     print(f"❌ RAG 시스템 초기화 실패: {str(e)}")

user_inputs = {}


@app.event("app_mention")
def handle_message_events(body, logger):

    global user_inputs, MESSAGES
    channel = None  # channel 변수를 초기화

    try:
        # Slack 이벤트 데이터 추출
        prompt = str(body["event"]["text"]).split(">")[1].strip()
        channel = body["event"]["channel"]
        thread_ts = body["event"]["event_ts"]
        user_id = body["event"]["user"]

        # # 항상 이전 대화와 일정 정보를 추가
        # add_previous_data_to_messages(MESSAGES)  # 최근 대화 추가

        # 항상 이전 대화와 일정 정보를 추가
        MESSAGES = manage_message_history(MESSAGES)

        ##### 특정 명령어 처리
        # Slack Bot 일정 생성 기능
                ##### 일정 생성 요청 감지 #####
   
        # TODO : 일정 생성 찾아서 구현해두기
        # 일정 생성 요청 감지
        if "일정 생성" in prompt:
            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=(
                    "📅 학습 일정을 생성하려면 아래 정보를 모두 입력해주세요:\n"
                    "- 학습 요일 (예: 월, 수)\n"
                    "- 학습 시간 (예: 9:00 또는 오전 9시)\n"
                    "- 학습 기간 (주 단위, 예: 10)\n\n"
                    "입력 예시: 월, 수 10:00 10주"
                )
            )
            # 유저 입력 저장소 초기화
            user_inputs[channel] = {"days": None, "time": None, "weeks": None}
            return

        # 추가 입력을 받아 일정 생성
        if channel in user_inputs:
            user_data = user_inputs[channel]
            try:
                # 사용자 입력을 업데이트
                days, time, weeks = parse_input(prompt)
                user_data["days"] = days
                user_data["time"] = time
                user_data["weeks"] = weeks
            except ValueError as e:
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"⚠️ 입력 오류: {e}\n\n"
                        "아래 형식을 확인하고 다시 입력해주세요:\n"
                        "- 학습 요일 (예: 월, 수)\n"
                        "- 학습 시간 (예: 9:00 또는 오전 9시)\n"
                        "- 학습 기간 (주 단위, 예: 10)\n\n"
                        "입력 예시: 월, 수 10:00 10주"
                )
                return

            # 입력 데이터가 모두 수집되었는지 확인
            if None in user_data.values():
                missing = [key for key, value in user_data.items() if value is None]
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"⚠️ 부족한 입력 데이터: {', '.join(missing)}\n"
                        "필요한 정보를 모두 입력해주세요."
                )
                return

            # 일정 생성 및 저장
            try:
                schedule = generate_schedule(
                    user_data["days"], 
                    user_data["time"], 
                    user_data["weeks"], 
                    CONTENTS
                )
                save_schedule_to_json(schedule)

                # 포매팅된 일정 응답
                formatted_schedule = format_schedule(schedule)
                formatted_response = (
                    "📅 생성된 학습 일정입니다:\n"
                    f"{formatted_schedule}\n\n"
                    "다른 질문이나 요청이 있다면 말씀해주세요!"
                )
                MESSAGES.append({"role": "assistant", "content": formatted_response})

                # Slack 응답
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=formatted_response
                )

                # 일정 생성 후 데이터 삭제
                del user_inputs[channel]
            except Exception as e:
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"⚠️ 일정 생성 중 오류가 발생했습니다: {e}"
                )
        # 일정 조회 요청 감지
        elif "일정 조회" in prompt or "주차 일정" in prompt:
            schedule = load_schedule_from_json()  # 스케줄 데이터를 파일에서 읽어옴
            if schedule:
                formatted_schedule = format_schedule(schedule)  # 포매팅된 스케줄 데이터
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"📅 저장된 학습 일정:\n{formatted_schedule}"
                )
            else:
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text="저장된 일정이 없습니다. 먼저 일정을 생성해주세요."
                )
            return


        # 일정 수정 로직 구현
        elif "일정 수정" in prompt:
            try:
                # 사용자 입력 파싱
                parts = prompt.replace("일정 수정", "").strip().split(" ")

                # 입력이 부족한 경우 안내 메시지 제공
                if len(parts) < 4:
                    gpt_response = (
                        "일정을 수정하려면 아래 형식을 사용해 주세요:\n"
                        "- **형식:** 일정 수정 [기존 날짜] [수정할 작업] [새 날짜] [새 시간]\n"
                        "- **예:** 일정 수정 2024-12-09 01-5 파이썬 둘러보기 2024-12-11 10:00\n\n"
                        "추가적인 질문이 있다면 언제든지 말씀해 주세요! 😊"
                    )
                    MESSAGES.append({"role": "assistant", "content": gpt_response})
                    slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_response)
                    return

                # 0번째: 기존 날짜
                date = parts[0]

                # 1부터 마지막 두 번째까지: 학습 목차
                updated_task = " ".join(parts[1:-2])

                # 마지막 두 부분: 새 날짜와 새 시간
                new_date = parts[-2]
                new_time = parts[-1]

                # 일정 수정 함수 호출
                response = update_schedule(date.strip(), updated_task.strip(), new_date.strip(), new_time.strip())

                # 수정 성공 여부에 따른 응답
                if "이동되었습니다" in response or "추가되었습니다" in response:
                    gpt_response = (
                        f"✅ 일정이 성공적으로 수정되었습니다!\n"
                        f"- **기존 날짜:** {date}\n"
                        f"- **수정된 작업:** {updated_task}\n"
                        f"- **새로운 날짜:** {new_date}\n"
                        f"- **새로운 시간:** {new_time}\n\n"
                        f"결과: {response}"
                    )
                else:
                    gpt_response = (
                        f"⚠️ 일정 수정 중 문제가 발생했습니다: {response}\n"
                        f"입력 형식이 올바른지 확인하고 다시 시도해 주세요.\n"
                        "- **형식:** 일정 수정 [기존 날짜] [수정할 작업] [새 날짜] [새 시간]"
                    )

                # GPT 응답 생성 및 Slack 메시지 전송
                MESSAGES.append({"role": "assistant", "content": gpt_response})
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_response)

            except ValueError as e:
                # 입력 오류가 발생했을 때 일정 수정 안내 메시지 제공
                gpt_response = (
                    f"⚠️ 입력 오류가 발생했습니다: {str(e)}\n\n"
                    "일정을 수정하려면 아래 형식을 사용해 주세요:\n"
                    "- **형식:** 일정 수정 [기존 날짜] [수정할 작업] [새 날짜] [새 시간]\n"
                    "- **예:** 일정 수정 2024-12-09 01-5 파이썬 둘러보기 2024-12-11 10:00\n\n"
                    "추가적인 질문이 있다면 언제든지 말씀해 주세요! 😊"
                )
                MESSAGES.append({"role": "assistant", "content": gpt_response})
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_response)
            return


        # Slack 명령어 처리
        # 일정 삭제 Slack 명령어 처리
        elif "일정 삭제" in prompt:
            try:
                # 사용자 입력 파싱
                parts = prompt.replace("일정 삭제", "").strip().split(" ")

                if not parts or (len(parts) == 1 and parts[0] == ""):
                    gpt_response = (
                        "삭제할 일정을 입력해 주세요:\n"
                        "- **형식 1:** 일정 삭제 [날짜] (해당 날짜 전체 삭제)\n"
                        "- **형식 2:** 일정 삭제 [날짜] [삭제할 작업] (특정 작업만 삭제)\n"
                        "- **형식 3:** 일정 전체 삭제\n\n"
                        "예:\n"
                        "- 일정 삭제 2024-12-10\n"
                        "- 일정 삭제 2024-12-10 01-6 파이썬 둘러보기\n"
                        "- 일정 전체 삭제"
                    )
                    MESSAGES.append({"role": "assistant", "content": gpt_response})
                    slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_response)
                    return

                # "전체 삭제" 처리
                if "전체 삭제" in parts:
                    gpt_response = (
                        "⚠️ 모든 일정을 삭제하시겠습니까?\n"
                        "이 작업은 되돌릴 수 없습니다.\n"
                        "삭제를 원하시면 '예' 또는 '아니오'로 응답해 주세요."
                    )
                    MESSAGES.append({"role": "assistant", "content": gpt_response})
                    slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_response)

                    # 실제 삭제 확인 로직
                    confirmation = "예"  # 예제에서는 자동으로 '예' 처리. 실제 Slack에서는 사용자 응답을 받아 처리.
                    if confirmation.lower() == "예":
                        response = delete_schedule(delete_all=True)
                    else:
                        response = "❌ 전체 일정 삭제가 취소되었습니다."

                    slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=response)
                    return

                # 특정 날짜와 작업 삭제 처리
                date = parts[0]
                task = " ".join(parts[1:]) if len(parts) > 1 else None

                if not date:
                    gpt_response = (
                        "⚠️ 삭제할 날짜를 입력해 주세요.\n"
                        "- **예:** 일정 삭제 2024-12-10"
                    )
                    MESSAGES.append({"role": "assistant", "content": gpt_response})
                    slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_response)
                    return

                # 일정 삭제 호출
                response = delete_schedule(date.strip(), task.strip() if task else None)

                # 결과 메시지 처리
                gpt_response = f"✅ {response}" if "삭제되었습니다" in response else f"⚠️ {response}"
                MESSAGES.append({"role": "assistant", "content": gpt_response})
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_response)

            except ValueError:
                # 잘못된 입력 처리
                gpt_error_response = (
                    "⚠️ 입력 형식 오류가 발생했습니다:\n"
                    "- **형식 1:** 일정 삭제 [날짜] (해당 날짜 전체 삭제)\n"
                    "- **형식 2:** 일정 삭제 [날짜] [삭제할 작업] (특정 작업만 삭제)\n\n"
                    "예:\n"
                    "- 일정 삭제 2024-12-10\n"
                    "- 일정 삭제 2024-12-10 01-6 파이썬 둘러보기\n"
                )
                MESSAGES.append({"role": "assistant", "content": gpt_error_response})
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_error_response)
            return

        elif "일정 전체 삭제" in prompt:
            try:
                # 전체 삭제 확인 메시지와 버튼 전송
                gpt_response = {
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "⚠️ 모든 일정을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다."
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "예"},
                                    "style": "danger",
                                    "action_id": "confirm_delete_all"  # 여기에서 action_id 설정
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "아니오"},
                                    "style": "primary",
                                    "action_id": "cancel_delete_all"  # 여기에서 action_id 설정
                                }
                            ]
                        }
                    ]
                }

                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, blocks=gpt_response["blocks"], text="전체 일정 삭제 확인")
            except Exception as e:
                gpt_error_response = f"⚠️ 오류가 발생했습니다: {str(e)}"
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=gpt_error_response)
            return

        elif "리마인더" in prompt:
            if "리마인더 예약 전체" in prompt:
                try:
                    parts = prompt.replace("리마인더 예약 전체", "").strip()
                    hours_before = int(parts) if parts else 1  # 기본값 1시간
                    schedule_all_reminders(channel, slack_client, hours_before)
                    slack_client.chat_postMessage(
                        channel=channel,
                        thread_ts=thread_ts,
                        text=f"모든 일정에 대해 {hours_before}시간 전에 리마인더가 예약되었습니다."
                    )
                except ValueError:
                    slack_client.chat_postMessage(
                        channel=channel,
                        thread_ts=thread_ts,
                        text="⚠️ 올바른 시간을 입력하세요. 예: `리마인더 예약 전체 3`"
                    )
            elif "리마인더 예약" in prompt:
                try:
                    parts = prompt.replace("리마인더 예약", "").strip().split()
                    target_date = parts[0]
                    hours_before = int(parts[1]) if len(parts) > 1 else 1  # 기본값 1시간
                    schedule_specific_reminder(channel, slack_client, target_date, hours_before)
                    slack_client.chat_postMessage(
                        channel=channel,
                        thread_ts=thread_ts,
                        text=f"{target_date} 일정에 대해 {hours_before}시간 전에 리마인더가 예약되었습니다."
                    )
                except (IndexError, ValueError):
                    slack_client.chat_postMessage(
                        channel=channel,
                        thread_ts=thread_ts,
                        text="⚠️ 올바른 형식을 입력하세요. 예: `리마인더 예약 2024-12-18 3`"
                    )
            else:
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=(
                        "리마인더 기능을 사용할 수 있습니다:\n"
                        "- 특정 날짜 리마인더 예약: `리마인더 예약 [날짜] [시간 전]`\n"
                        "  예: `리마인더 예약 2024-12-18 3`\n"
                        "- 전체 일정 리마인더 예약: `리마인더 예약 전체 [시간 전]`\n"
                        "  예: `리마인더 예약 전체 3`"
                    )
                )


        elif "진행률 입력" in prompt:
            # 사용자가 올바른 입력을 제공했는지 확인
            try:
                parts = prompt.replace("진행률 입력", "").strip().split(" ", 2)
                if len(parts) < 3:
                    raise ValueError("올바른 입력 형식을 제공해야 합니다.")
                date, task_name, progress = parts[0], parts[1], int(parts[2])

                # 진행률 업데이트 처리
                response = update_task_progress(date, task_name, progress)
                MESSAGES.append({"role": "assistant", "content": response})

                # GPT가 응답하도록 설정
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=response)

            except (ValueError, IndexError):
                # 올바른 형식이 아닌 경우 안내 메시지 생성
                MESSAGES.append({"role": "user", "content": prompt})
                assistant_response = (
                    "📝 진행률을 입력하려면 아래 형식을 사용하세요:\n"
                    "- **형식:** 진행률 입력 [날짜] [학습 목차] [진행률(0~100)]\n"
                    "- **예:** 진행률 입력 2024-12-18 01-5 파이썬 둘러보기 50\n\n"
                    "정확한 정보를 입력해 주시면 기록하겠습니다!"
                )
                MESSAGES.append({"role": "assistant", "content": assistant_response})
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=assistant_response)

            return
        

        elif "진행률 보기" in prompt:
            # 진행률 보기 요청
            try:
                if "진행률 보기" == prompt.strip():  # 단순히 '진행률 보기'만 입력된 경우
                    progress = view_progress()
                    MESSAGES.append({"role": "assistant", "content": progress})
                    slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=progress)
                else:
                    raise ValueError("진행률 보기 명령 형식이 올바르지 않습니다.")
            except ValueError:
                # 올바른 형식 안내
                MESSAGES.append({"role": "user", "content": prompt})
                assistant_response = (
                    "📊 진행률을 보시려면 아래 명령어를 사용하세요:\n"
                    "- **형식:** 진행률 보기\n"
                    "이 명령어로 전체 평균 진행률과 오늘 날짜의 진행률을 확인할 수 있습니다!"
                )
                MESSAGES.append({"role": "assistant", "content": assistant_response})
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=assistant_response)

            return
        
        # raptor 버전
        if "용어 사전" in prompt:
            search_query = prompt.replace("용어 사전", "").strip()

            if not search_query:
                MESSAGES.append({"role": "user", "content": prompt})
                assistant_response = (
                    "📚 용어 사전에 대해 안내드립니다:\n"
                    "- **용어 사전**은 학습 중 나온 주요 개념이나 키워드에 대한 설명을 제공합니다.\n"
                    "- 특정 용어를 검색하려면 '용어 사전 [검색어]' 형식으로 입력하세요.\n"
                    "- 예시: '용어 사전 RAG'\n\n"
                    "검색어 없이 '용어 사전'만 입력하면 이렇게 안내를 드립니다!"
                )
                MESSAGES.append({"role": "assistant", "content": assistant_response})
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=assistant_response)
                return

            try:
                # RAG 시스템 초기화
                RAG_PDF_PATH = r"C:\Users\RMARKET\workspace\assistntbot\AI_Python_AssistantBot\data\converted_data_with_metadata.pdf"
                rag_chain = initialize_raptor_rag_system(RAG_PDF_PATH)
            except Exception as e:
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"❌ RAG 시스템 초기화 중 오류가 발생했습니다: {str(e)}"
                )
                return

            today = datetime.date.today().strftime("%Y-%m-%d")
            system_prompt = f"{today} 학습 진도에 맞는 용어를 20개 선정하고 정의해줘."
            user_question = search_query

            try:
                # 사용자 질문 처리 및 RAG 답변 생성
                input_data = f"{system_prompt}\\n\\n{user_question}"
                answer = generate_raptor_rag_answer(input_data, rag_chain)
            except Exception as e:
                answer = f"❌ 답변 생성 중 오류가 발생했습니다: {str(e)}"

            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=answer
            )

        ### 기존 rag
        # if "용어 사전" in prompt:
        #     search_query = prompt.replace("용어 사전", "").strip()

        #     if not search_query:
        #         MESSAGES.append({"role": "user", "content": prompt})
        #         assistant_response = (
        #             "📚 용어 사전에 대해 안내드립니다:\n"
        #             "- **용어 사전**은 학습 중 나온 주요 개념이나 키워드에 대한 설명을 제공합니다.\n"
        #             "- 특정 용어를 검색하려면 '용어 사전 [검색어]' 형식으로 입력하세요.\n"
        #             "- 예시: '용어 사전 RAG'\n\n"
        #             "검색어 없이 '용어 사전'만 입력하면 이렇게 안내를 드립니다!"
        #         )
        #         MESSAGES.append({"role": "assistant", "content": assistant_response})
        #         slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=assistant_response)
        #         return

        #     try:
        #         # RAG 시스템 초기화
        #         RAG_PDF_PATH = r"C:\Users\RMARKET\workspace\assistntbot\AI_Python_AssistantBot\data\converted_data_with_metadata.pdf"
        #         rag_chain = initialize_rag_system(RAG_PDF_PATH)
        #     except Exception as e:
        #         slack_client.chat_postMessage(
        #             channel=channel,
        #             thread_ts=thread_ts,
        #             text=f"❌ RAG 시스템 초기화 중 오류가 발생했습니다: {str(e)}"
        #         )
        #         return

        #     today = datetime.date.today().strftime("%Y-%m-%d")
        #     system_prompt = f"{today} 학습 진도에 맞는 용어를 20개 선정하고 정의해줘."
        #     user_question = search_query

        #     try:
        #         # 프롬프트와 사용자 질문을 RAG 시스템에 전달하여 답변 생성
        #         input_data = f"{system_prompt}\n\n{user_question}"
        #         answer = generate_rag_answer(input_data, rag_chain)
        #     except Exception as e:
        #         answer = f"❌ 답변 생성 중 오류가 발생했습니다: {str(e)}"

        #     slack_client.chat_postMessage(
        #         channel=channel,
        #         thread_ts=thread_ts,
        #         text=answer
        #     )

 

        if "요약 정리" in prompt:
            search_query = prompt.replace("요약 정리", "").strip()

            # 날짜가 없을 경우 최근 날짜 사용
            if not search_query:
                today = datetime.date.today().strftime("%Y-%m-%d")
                search_query = today  # 최근 날짜로 설정

            try:
                # RAG 시스템 초기화
                RAG_PDF_PATH = r"C:\Users\RMARKET\workspace\assistntbot\AI_Python_AssistantBot\data\converted_data_with_metadata.pdf"
                rag_chain = initialize_raptor_rag_system(RAG_PDF_PATH)
            except Exception as e:
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"❌ RAG 시스템 초기화 중 오류가 발생했습니다: {str(e)}"
                )
                return

            system_prompt = f"{search_query} 학습 진도에 맞는 내용을 20개 요약 정리해줘."

            try:
                # 요약 생성
                answer = generate_raptor_rag_answer({'prompt': system_prompt, 'question': user_question}, rag_chain)
            except Exception as e:
                answer = f"❌ 요약 생성 중 오류가 발생했습니다: {str(e)}"

            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=answer
            )



        # raptor 버전
        if "퀴즈 풀기" in prompt:
            search_query = prompt.replace("퀴즈 풀기", "").strip()

            if not search_query:
                MESSAGES.append({"role": "user", "content": prompt})
                assistant_response = (
                    "📚 퀴즈 풀기에 대해 안내드립니다:\n"
                    "- **퀴즈 풀기**는 학습 중 나온 주요 개념이나 키워드에 퀴즈와 정답을 제공합니다.\n"
                    "- 특정 용어를 검색하려면 '퀴즈 풀기 [검색어]' 형식으로 입력하세요.\n"
                    "- 예시: '퀴즈 풀기 while문'\n\n"
                    "검색어 없이 '퀴즈 풀기'만 입력하면 이렇게 안내를 드립니다!"
                )
                MESSAGES.append({"role": "assistant", "content": assistant_response})
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=assistant_response)
                return

            try:
                # RAG 시스템 초기화
                RAG_PDF_PATH = r"C:\\Users\\RMARKET\\workspace\\assistntbot\\AI_Python_AssistantBot\\data\\converted_data_with_metadata.pdf"
                rag_chain = initialize_raptor_rag_system(RAG_PDF_PATH)
            except Exception as e:
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"❌ RAG 시스템 초기화 중 오류가 발생했습니다: {str(e)}"
                )
                return

            today = datetime.date.today().strftime("%Y-%m-%d")
            system_prompt = f"{today} 학습 진도에 맞는 용어를 20개 선정하고 정의해줘."
            user_question = search_query

            try:
                # 사용자 질문 처리 및 RAG 답변 생성
                input_data = f"{system_prompt}\\n\\n{user_question}"
                answer = generate_raptor_rag_answer(input_data, rag_chain)
            except Exception as e:
                answer = f"❌ 답변 생성 중 오류가 발생했습니다: {str(e)}"

            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=answer
            )


        # 기본 메시지 처리 (GPT 활용)
        save_chat_log(user_id, prompt, role="user")
        MESSAGES.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model='gpt-4o',
            messages=MESSAGES
        )

        assistant_reply = response.choices[0].message.content
        MESSAGES.append({"role": "assistant", "content": assistant_reply})

        save_chat_log("GPT", assistant_reply, role="assistant")

        slack_client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=assistant_reply
        )

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        if channel:
            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f"오류가 발생했습니다: {str(e)}"
            )



@app.action("confirm_delete_all")
def handle_confirm_delete_all(ack, body, client, logger):
    """
    '예' 버튼 클릭 이벤트를 처리하여 모든 일정을 삭제합니다.
    """
    ack()  # Slack에 응답
    try:
        response = delete_schedule(delete_all=True)  # 모든 일정 삭제
        client.chat_postMessage(
            channel=body["channel"]["id"],
            text=f"✅ 모든 일정이 삭제되었습니다."
        )
    except Exception as e:
        logger.error(f"전체 삭제 처리 중 오류: {e}")
        client.chat_postMessage(
            channel=body["channel"]["id"],
            text=f"⚠️ 오류가 발생했습니다: {str(e)}"
        )


@app.action("cancel_delete_all")
def handle_cancel_delete_all(ack, body, client):
    """
    '아니오' 버튼 클릭 이벤트를 처리하여 삭제 작업을 취소합니다.
    """
    ack()  # Slack에 응답
    client.chat_postMessage(
        channel=body["channel"]["id"],
        text="❌ 전체 일정 삭제가 취소되었습니다."
    )

@app.action("confirm_delete_all")
def handle_confirm_delete_all(ack, body, client, logger):
    ack()  # Slack에 응답
    logger.info(f"버튼 클릭 이벤트 데이터: {body}")  # 로그 출력



if __name__ == "__main__":
    initialize_files()
    SocketModeHandler(app, os.environ['SLACK_APP_TOKEN']).start()
