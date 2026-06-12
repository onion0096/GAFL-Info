from flask import Flask, request, jsonify
import requests
from datetime import date, datetime
import os

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# =============================================
# 2026 GAFL 학사일정 (구글 캘린더 기준)
# =============================================
SCHEDULE = [
    {"date": "2026-03-03", "event": "개학식 / 환영식"},
    {"date": "2026-03-11", "event": "IB 고급 영어 어휘 대회"},
    {"date": "2026-03-17", "end": "2026-03-17", "event": "ASG Spring SA 시작"},
    {"date": "2026-03-18", "end": "2026-03-19", "event": "학교교육설명회"},
    {"date": "2026-03-24", "event": "전국연합학력평가 (서울)"},
    {"date": "2026-04-03", "event": "DP1 학부모 Subject Conference"},
    {"date": "2026-04-10", "event": "PreDP 학부모 Subject Conference"},
    {"date": "2026-04-15", "event": "IB 영어 에세이 쓰기 대회"},
    {"date": "2026-04-22", "end": "2026-04-24", "event": "국내반 1차 정기시험"},
    {"date": "2026-04-27", "end": "2026-05-01", "event": "DP1 GVT / IB Retake 시험"},
    {"date": "2026-05-04", "end": "2026-05-15", "event": "학교 휴일 / AP 시험 시작"},
    {"date": "2026-05-08", "event": "PreDP & DP1 체육대회"},
    {"date": "2026-05-13", "end": "2026-05-15", "event": "학부모 공개수업"},
    {"date": "2026-05-20", "event": "IB 역사 대회"},
    {"date": "2026-06-03", "event": "지방선거일"},
    {"date": "2026-06-08", "end": "2026-06-12", "event": "DP1 학부모 해외대학 상담"},
    {"date": "2026-06-14", "end": "2026-06-16", "event": "DP2 Subject Conference"},
    {"date": "2026-06-24", "end": "2026-07-03", "event": "IB Sem.1 시험 / 국내반 2차 정기시험"},
    {"date": "2026-07-08", "end": "2026-07-10", "event": "DP1 학부모 Subject Conference"},
    {"date": "2026-07-22", "event": "여름방학 시작"},
    {"date": "2026-07-27", "end": "2026-08-05", "event": "GAFL IB English Summer Camp"},
    {"date": "2026-08-10", "event": "2학기 개학"},
    {"date": "2026-08-24", "end": "2026-08-25", "event": "IB Evaluation Visit"},
    {"date": "2026-09-01", "event": "전국연합학력평가"},
    {"date": "2026-09-09", "event": "IB 경제 에세이 쓰기 대회"},
    {"date": "2026-09-15", "end": "2026-09-23", "event": "DP1 1차 정기시험"},
    {"date": "2026-09-24", "end": "2026-09-27", "event": "추석 연휴"},
    {"date": "2026-10-06", "end": "2026-10-08", "event": "국내반 1차 정기시험"},
    {"date": "2026-10-07", "event": "IB 영어 독서 감상문 쓰기 대회"},
    {"date": "2026-10-20", "event": "전국연합학력평가 (서울)"},
    {"date": "2026-10-29", "end": "2026-10-30", "event": "학부모 공개수업 (PreDP & DP1)"},
    {"date": "2026-11-03", "end": "2026-11-11", "event": "IB Sem.2 시험 (PreDP & DP1) / 국내반 2차 정기시험"},
    {"date": "2026-11-18", "event": "PreDP 학부모 해외대학 상담"},
    {"date": "2026-11-19", "end": "2026-11-20", "event": "수능 (학교 휴일)"},
    {"date": "2026-11-21", "end": "2026-11-23", "event": "DP1 Subject Conference"},
    {"date": "2026-11-25", "end": "2026-11-27", "event": "PreDP Subject Conference"},
    {"date": "2026-12-01", "end": "2026-12-11", "event": "IB Sem.2 시험 (PreDP & DP1) / 국내반 2차 정기시험"},
    {"date": "2026-12-21", "end": "2026-12-23", "event": "DP1 학부모 Subject Conference"},
    {"date": "2026-12-30", "event": "2027 PreDP 면접"},
    {"date": "2026-12-31", "event": "겨울방학 시작"},
    {"date": "2027-01-11", "end": "2027-01-22", "event": "PreGAFL"},
    {"date": "2027-01-18", "end": "2027-01-27", "event": "GAFL IB English Winter Camp"},
    {"date": "2027-02-03", "end": "2027-02-04", "event": "교사 출근 / 졸업식"},
    {"date": "2027-02-06", "end": "2027-02-09", "event": "설날 연휴"},
    {"date": "2027-02-22", "end": "2027-02-26", "event": "교사 신학기 준비 / DP1 학부모 해외대학 상담 (2/23~25)"},
]


def get_schedule_text():
    lines = []
    for s in SCHEDULE:
        end_part = f" ~ {s['end']}" if s.get("end") else ""
        lines.append(f"{s['date']}{end_part}: {s['event']}")
    return "\n".join(lines)


def ask_claude(user_message):
    today = date.today().isoformat()
    schedule_text = get_schedule_text()

    system_prompt = f"""당신은 GAFL(경기외국어고등학교 국제반) 학사일정 안내 챗봇입니다.
오늘 날짜: {today}

아래는 2026 GAFL 학사일정입니다:
{schedule_text}

답변 규칙:
- 친근하고 간결하게 답변 (3~4줄 이내)
- 날짜 형식: "○월 ○일(요일)" 형식 사용
- 기간이 있는 일정은 시작~종료 날짜 모두 안내
- 오늘로부터 며칠 남았는지 D-day도 함께 알려주기
- 일일/주간/월간 조회 시 해당 기간의 모든 일정 나열
- 해당 일정 없으면 "해당 기간에 일정이 없어요"라고 답변
- 이모지 적절히 사용"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        },
        timeout=10,
    )
    data = response.json()
    return data["content"][0]["text"]


def kakao_response(text, buttons=None):
    outputs = [{"simpleText": {"text": text}}]
    result = {"version": "2.0", "template": {"outputs": outputs}}
    if buttons:
        result["template"]["quickReplies"] = [
            {"messageText": b, "action": "message", "label": b} for b in buttons
        ]
    return jsonify(result)


# =============================================
# 엔드포인트
# =============================================

@app.route("/", methods=["GET"])
def health():
    return "GAFL 알리미 서버 정상 작동 중 🏫"


@app.route("/chat", methods=["POST"])
def chat():
    """자유 대화 - Claude AI가 답변"""
    try:
        body = request.json
        user_msg = body.get("userRequest", {}).get("utterance", "")
        if not user_msg:
            return kakao_response("메시지를 입력해주세요.")

        reply = ask_claude(user_msg)
        return kakao_response(reply, buttons=["오늘 일정", "이번 주 일정", "이번 달 일정", "방학 일정", "다음 시험"])
    except Exception as e:
        return kakao_response(f"오류가 발생했어요. 잠시 후 다시 시도해주세요.\n({str(e)})")


@app.route("/today", methods=["POST"])
def today_schedule():
    """오늘 일정"""
    try:
        reply = ask_claude("오늘 학교 일정이 있어?")
        return kakao_response(reply, buttons=["이번 주 일정", "이번 달 일정", "다음 시험", "방학 일정"])
    except Exception as e:
        return kakao_response("오류가 발생했어요. 잠시 후 다시 시도해주세요.")


@app.route("/weekly", methods=["POST"])
def weekly_schedule():
    """이번 주 일정"""
    try:
        reply = ask_claude("이번 주 학교 일정을 모두 알려줘")
        return kakao_response(reply, buttons=["오늘 일정", "이번 달 일정", "다음 시험", "방학 일정"])
    except Exception as e:
        return kakao_response("오류가 발생했어요. 잠시 후 다시 시도해주세요.")


@app.route("/monthly", methods=["POST"])
def monthly_schedule():
    """이번 달 일정"""
    try:
        reply = ask_claude("이번 달 학교 일정을 모두 알려줘")
        return kakao_response(reply, buttons=["오늘 일정", "이번 주 일정", "다음 시험", "방학 일정"])
    except Exception as e:
        return kakao_response("오류가 발생했어요. 잠시 후 다시 시도해주세요.")


@app.route("/vacation", methods=["POST"])
def vacation():
    """방학 일정"""
    try:
        reply = ask_claude("여름방학과 겨울방학이 언제야? D-day도 알려줘")
        return kakao_response(reply, buttons=["오늘 일정", "이번 달 일정", "다음 시험"])
    except Exception as e:
        return kakao_response("오류가 발생했어요. 잠시 후 다시 시도해주세요.")


@app.route("/exam", methods=["POST"])
def next_exam():
    """다음 시험 일정"""
    try:
        reply = ask_claude("다음 시험 일정이 언제야? D-day도 알려줘")
        return kakao_response(reply, buttons=["오늘 일정", "이번 달 일정", "방학 일정"])
    except Exception as e:
        return kakao_response("오류가 발생했어요. 잠시 후 다시 시도해주세요.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
