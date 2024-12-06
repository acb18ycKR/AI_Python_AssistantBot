import json
import os
from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
from dotenv import load_dotenv
from calendar_functions import generate_schedule

# 환경 변수 로드
load_dotenv()

MESSAGES = []

# Slack 이벤트 API와 Web API 설정
app = App(token=os.environ['SLACK_BOT_TOKEN'])
slack_client = WebClient(os.environ['SLACK_BOT_TOKEN'])

# GPT API 초기화
api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key
client = OpenAI()


def process_tool_call(tool_name, tool_input):
    """도구 호출 처리 함수"""
    if tool_name == "generate_schedule":
        return generate_schedule(**tool_input)


@app.event("app_mention")
def handle_message_events(body, logger):
    try:
        # 사용자가 보낸 메시지 추출
        prompt = str(body["event"]["text"]).split(">")[1].strip()
        print(f"\n{'='*50}\nUser Message: {prompt}\n{'='*50}")

        # 사용자 메시지 응답 중 '처리 중' 메시지 전송
        slack_client.chat_postMessage(
            channel=body["event"]["channel"],
            thread_ts=body["event"]["event_ts"],
            text="안녕하세요, 개인 비서 슬랙봇입니다! :robot_face: \n곧 전달 주신 문의사항 처리하겠습니다!"
        )

        # 사용할 도구(tool) 정의
        tools = [
            {
                "name": "generate_schedule",
                "description": "학습 계획 생성 및 일정 등록",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "book_title": {
                            "type": "string",
                            "description": "책 제목 (예: '점프 투 파이썬')"
                        },
                        "days": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "학습 요일 (예: ['화', '목'])"
                        },
                        "time": {
                            "type": "string",
                            "description": "학습 시간 (예: '20:00')"
                        },
                        "weeks": {
                            "type": "integer",
                            "description": "학습 기간 (주 단위)"
                        },
                        "contents": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "책 목차 리스트"
                        }
                    },
                    "required": ["book_title", "days", "time", "weeks", "contents"]
                }
            }
        ]

        # OpenAI API 호출
        MESSAGES.append({"role": "user", "content": prompt})
        response_from_gpt = client.chat.completions.create(
            model="gpt-4",  # 최신 모델 사용
            messages=MESSAGES,
            functions=tools,
            max_tokens=1024
        )

        print(f"\n초기 응답: {response_from_gpt.choices[0].message.content}")

        if response_from_gpt.choices[0].finish_reason == "function_call":
            function_call = response_from_gpt.choices[0].message.function_call
            tool_name = function_call.name
            tool_input = json.loads(function_call.arguments)

            # 도구 실행
            tool_result = process_tool_call(tool_name, tool_input)
            print(f"도구 결과: {tool_result}")

            # 도구 결과를 GPT에 전달하여 최종 응답 생성
            final_response = client.chat.completions.create(
                model="gpt-4",
                messages=MESSAGES + [
                    {"role": "assistant", "function_call": {"name": tool_name, "arguments": json.dumps(tool_input)}},
                    {"role": "function", "name": tool_name, "content": json.dumps(tool_result)}
                ],
                max_tokens=4096
            )
            final_content = final_response.choices[0].message.content  # 최종 응답 내용
        else:
            final_content = response_from_gpt.choices[0].message.content

        # 최종 응답을 Slack 채널에 전송
        slack_client.chat_postMessage(
            channel=body["event"]["channel"],
            thread_ts=body["event"]["event_ts"],
            text=final_content
        )


    except Exception as e:
        logger.error(f"Error handling message: {e}")
        slack_client.chat_postMessage(
            channel=body["event"]["channel"],
            thread_ts=body["event"]["event_ts"],
            text=f"오류가 발생했습니다: {str(e)}"
        )


if __name__ == "__main__":
    SocketModeHandler(app, os.environ['SLACK_APP_TOKEN']).start()
