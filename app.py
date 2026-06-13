from flask import Flask, request, jsonify
from datetime import date, datetime, timedelta

app = Flask(__name__)

# =============================================
# 2026 GAFL 학사일정
# =============================================
SCHEDULE = [
    {"date": "2026-03-03", "event": "개학식 / 환영식"},
    {"date": "2026-03-11", "event": "IB 고급 영어 어휘 대회"},
    {"date": "2026-03-17", "event": "ASG Spring SA 시작"},
    {"date": "2026-03-18", "end": "2026-03-19", "event": "학교교육설명회"},
    {"date": "2026-03-24", "event": "전국연합학력평가 (서울)"},
    {"date": "2026-04-03", "event": "DP1 학부모 Subject Conference"},
    {"date": "2026-04-10", "event": "PreDP 학부모 Subject Conference"},
    {"date": "2026-04-15", "event": "IB 영어 에세이 쓰기 대회"},
    {"date": "2026-04-22", "end": "2026-04-24", "event": "국내반 1차 정기시험"},
    {"date": "2026-04-27", "end": "2026-05-01", "event": "DP1 GVT / IB Retake 시험"},
    {"date": "2026-05-04", "end": "2026-05-15", "event": "학교 휴일 / AP 시험"},
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
    {"date": "2027-02-22", "end": "2027-02-26", "event": "교사 신학기 준비 / DP1 학부모 해외대학 상담"},
]

DAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def fmt_date(d):
    return f"{d.month}/{d.day}({DAYS_KR[d.weekday()]})"


def dday(d):
    diff = (d - date.today()).days
    if diff == 0:
        return "오늘"
    elif diff > 0:
        return f"D-{diff}"
    else:
        return f"D+{abs(diff)}"


def is_in_range(s, start, end):
    """일정이 주어진 날짜 범위와 겹치는지 확인"""
    s_start = parse_date(s["date"])
    s_end = parse_date(s.get("end", s["date"]))
    return s_start <= end and s_end >= start


def format_event(s):
    s_start = parse_date(s["date"])
    if s.get("end"):
        s_end = parse_date(s["end"])
        date_str = f"{fmt_date(s_start)}~{fmt_date(s_end)}"
    else:
        date_str = fmt_date(s_start)
    return f"🔹 {s['event']}\n{date_str} | {dday(s_start)}"


def kakao_response(text, buttons=None):
    outputs = [{"simpleText": {"text": text}}]
    result = {"version": "2.0", "template": {"outputs": outputs}}
    if buttons:
        result["template"]["quickReplies"] = [
            {"messageText": b, "action": "message", "label": b} for b in buttons
        ]
    return jsonify(result)


MAIN_BUTTONS = ["오늘 일정", "이번 주 일정", "이번 달 일정", "방학 일정", "다음 시험"]


# =============================================
# 엔드포인트
# =============================================

@app.route("/", methods=["GET"])
def health():
    return "GAFL 알리미 서버 정상 작동 중 🏫"


@app.route("/today", methods=["POST"])
def today_schedule():
    today = date.today()
    events = [s for s in SCHEDULE if is_in_range(s, today, today)]
    if events:
        lines = [f"📅 오늘({fmt_date(today)}) 일정\n"]
        lines += [format_event(s) for s in events]
        text = "\n".join(lines)
    else:
        text = f"📅 오늘({fmt_date(today)})은 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/weekly", methods=["POST"])
def weekly_schedule():
    today = date.today()
    # 이번 주 월요일~일요일
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    events = [s for s in SCHEDULE if is_in_range(s, start, end)]
    if events:
        lines = [f"📅 이번 주 일정 ({fmt_date(start)} ~ {fmt_date(end)})\n"]
        lines += [format_event(s) for s in events]
        text = "\n".join(lines)
    else:
        text = f"📅 이번 주({fmt_date(start)} ~ {fmt_date(end)})는 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/monthly", methods=["POST"])
def monthly_schedule():
    today = date.today()
    start = today.replace(day=1)
    # 이번 달 말일
    if today.month == 12:
        end = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
    else:
        end = today.replace(month=today.month+1, day=1) - timedelta(days=1)
    events = [s for s in SCHEDULE if is_in_range(s, start, end)]
    if events:
        lines = [f"📅 {today.month}월 일정\n"]
        lines += [format_event(s) for s in events]
        text = "\n".join(lines)
    else:
        text = f"📅 {today.month}월은 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/vacation", methods=["POST"])
def vacation():
    keywords = ["방학", "Summer Camp", "Winter Camp", "PreGAFL"]
    today = date.today()
    events = [
        s for s in SCHEDULE
        if any(k in s["event"] for k in keywords) and parse_date(s["date"]) >= today
    ]
    if events:
        lines = ["🏖️ 방학 관련 일정\n"]
        lines += [format_event(s) for s in events[:5]]
        text = "\n".join(lines)
    else:
        text = "🏖️ 남은 방학 일정이 없어요."
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/exam", methods=["POST"])
def next_exam():
    keywords = ["시험", "정기시험", "Retake", "Sem.", "수능"]
    today = date.today()
    events = [
        s for s in SCHEDULE
        if any(k in s["event"] for k in keywords) and parse_date(s["date"]) >= today
    ]
    if events:
        next_e = events[0]
        lines = ["📝 다음 시험 일정\n", format_event(next_e)]
        if len(events) > 1:
            lines.append("\n그 다음 시험:")
            lines += [format_event(s) for s in events[1:3]]
        text = "\n".join(lines)
    else:
        text = "📝 남은 시험 일정이 없어요."
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/chat", methods=["POST"])
def chat():
    """자유 대화 - 버튼 안내로 대체"""
    text = "아래 버튼으로 원하는 일정을 조회해보세요! 😊\n\n원하시는 항목을 선택해주세요."
    return kakao_response(text, MAIN_BUTTONS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
