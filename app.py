from flask import Flask, request, jsonify
from datetime import date, datetime, timedelta
import requests
import csv
import io

app = Flask(__name__)

# =============================================
# 구글 스프레드시트 설정
# 시트를 "링크 있는 누구나 볼 수 있음"으로 공유 설정 필요
# =============================================
SHEET_ID = "12HTfYapiFumAjqVCK-_P-gxrcX7yPqw6sn-9ZtXx8FI"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

DAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]


def load_schedule():
    """구글 시트에서 일정 불러오기"""
    try:
        res = requests.get(SHEET_URL, timeout=10)
        res.encoding = "utf-8"
        reader = csv.DictReader(io.StringIO(res.text))
        schedule = []
        for row in reader:
            start = row.get("시작일", "").strip()
            end = row.get("종료일", "").strip()
            event = row.get("일정명", "").strip()
            if start and event:
                item = {"date": start, "event": event}
                if end:
                    item["end"] = end
                schedule.append(item)
        return schedule
    except Exception as e:
        return []


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


MAIN_BUTTONS = ["오늘 일정", "이번 주 일정", "다음 주 일정", "이번 달 일정", "방학 일정", "다음 시험"]


# =============================================
# 엔드포인트
# =============================================

@app.route("/", methods=["GET"])
def health():
    return "GAFL 알리미 서버 정상 작동 중 🏫"


@app.route("/today", methods=["POST"])
def today_schedule():
    today = date.today()
    schedule = load_schedule()
    events = [s for s in schedule if is_in_range(s, today, today)]
    if events:
        lines = [f"📅 오늘({fmt_date(today)}) 일정\n"]
        lines += [format_event(s) for s in events]
        text = "\n\n".join(lines)
    else:
        text = f"📅 오늘({fmt_date(today)})은 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/weekly", methods=["POST"])
def weekly_schedule():
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    schedule = load_schedule()
    events = [s for s in schedule if is_in_range(s, start, end)]
    if events:
        lines = [f"📅 이번 주 일정\n({fmt_date(start)} ~ {fmt_date(end)})\n"]
        lines += [format_event(s) for s in events]
        text = "\n\n".join(lines)
    else:
        text = f"📅 이번 주({fmt_date(start)} ~ {fmt_date(end)})는 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/next_week", methods=["POST"])
def next_week_schedule():
    today = date.today()
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
    end = start + timedelta(days=6)
    schedule = load_schedule()
    events = [s for s in schedule if is_in_range(s, start, end)]
    if events:
        lines = [f"📅 다음 주 일정\n({fmt_date(start)} ~ {fmt_date(end)})\n"]
        lines += [format_event(s) for s in events]
        text = "\n\n".join(lines)
    else:
        text = f"📅 다음 주({fmt_date(start)} ~ {fmt_date(end)})는 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/monthly", methods=["POST"])
def monthly_schedule():
    today = date.today()
    start = today.replace(day=1)
    if today.month == 12:
        end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    schedule = load_schedule()
    events = [s for s in schedule if is_in_range(s, start, end)]
    if events:
        lines = [f"📅 {today.month}월 일정\n"]
        lines += [format_event(s) for s in events]
        text = "\n\n".join(lines)
    else:
        text = f"📅 {today.month}월은 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/vacation", methods=["POST"])
def vacation():
    keywords = ["방학", "Summer Camp", "Winter Camp", "PreGAFL"]
    today = date.today()
    schedule = load_schedule()
    events = [
        s for s in schedule
        if any(k in s["event"] for k in keywords) and parse_date(s["date"]) >= today
    ]
    if events:
        lines = ["🏖️ 방학 관련 일정\n"]
        lines += [format_event(s) for s in events[:5]]
        text = "\n\n".join(lines)
    else:
        text = "🏖️ 남은 방학 일정이 없어요."
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/exam", methods=["POST"])
def next_exam():
    keywords = ["시험", "정기시험", "Retake", "Sem.", "수능", "Final Exams"]
    today = date.today()
    schedule = load_schedule()
    events = [
        s for s in schedule
        if any(k in s["event"] for k in keywords) and parse_date(s["date"]) >= today
    ]
    if events:
        next_e = events[0]
        lines = ["📝 다음 시험 일정\n", format_event(next_e)]
        if len(events) > 1:
            lines.append("\n그 다음 시험:")
            lines += [format_event(s) for s in events[1:3]]
        text = "\n\n".join(lines)
    else:
        text = "📝 남은 시험 일정이 없어요."
    return kakao_response(text, MAIN_BUTTONS)



@app.route("/next_month", methods=["POST"])
def next_month_schedule():
    today = date.today()
    if today.month == 12:
        first = today.replace(year=today.year + 1, month=1, day=1)
    else:
        first = today.replace(month=today.month + 1, day=1)
    if first.month == 12:
        last = first.replace(year=first.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last = first.replace(month=first.month + 1, day=1) - timedelta(days=1)
    schedule = load_schedule()
    events = [s for s in schedule if is_in_range(s, first, last)]
    if events:
        lines = [f"📅 {first.month}월 일정\n"]
        lines += [format_event(s) for s in events]
        text = "\n\n".join(lines)
    else:
        text = f"📅 {first.month}월은 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/month", methods=["POST"])
def month_schedule():
    """N월 일정 - 사용자 발화에서 월 추출"""
    import re
    body = request.json
    utterance = body.get("userRequest", {}).get("utterance", "")
    match = re.search(r"(\d{1,2})월", utterance)
    if not match:
        return kakao_response("몇 월 일정을 알고 싶으신가요?\n예) '7월' 또는 '7월 일정'", MAIN_BUTTONS)
    m = int(match.group(1))
    if m < 1 or m > 12:
        return kakao_response("1월~12월 사이로 입력해주세요.", MAIN_BUTTONS)
    today = date.today()
    year = today.year
    # 1~2월은 다음 해로 처리 (학사일정 기준)
    if m <= 2:
        year = today.year + 1 if today.month >= 3 else today.year
    first = date(year, m, 1)
    if m == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, m + 1, 1) - timedelta(days=1)
    schedule = load_schedule()
    events = [s for s in schedule if is_in_range(s, first, last)]
    if events:
        lines = [f"📅 {m}월 일정\n"]
        lines += [format_event(s) for s in events]
        text = "\n\n".join(lines)
    else:
        text = f"📅 {m}월은 일정이 없어요 😊"
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/parents", methods=["POST"])
def parents_schedule():
    """학부모 일정"""
    keywords = ["학부모", "공개수업", "설명회", "상담"]
    today = date.today()
    schedule = load_schedule()
    events = [
        s for s in schedule
        if any(k in s["event"] for k in keywords) and parse_date(s["date"]) >= today
    ]
    if events:
        lines = ["👨‍👩‍👧 학부모 일정\n"]
        lines += [format_event(s) for s in events[:7]]
        text = "\n\n".join(lines)
    else:
        text = "👨‍👩‍👧 남은 학부모 일정이 없어요."
    return kakao_response(text, MAIN_BUTTONS)


@app.route("/all", methods=["POST"])
def all_schedule():
    """전체 일정 - 오늘 이후 일정을 월별로 묶어서"""
    today = date.today()
    schedule = load_schedule()
    events = [s for s in schedule if parse_date(s["date"]) >= today]
    if not events:
        return kakao_response("📋 남은 일정이 없어요.", MAIN_BUTTONS)
    # 월별 그룹화
    from collections import defaultdict
    grouped = defaultdict(list)
    for s in events:
        d = parse_date(s["date"])
        grouped[f"{d.year}-{d.month:02d}"].append(s)
    lines = ["📋 전체 일정\n"]
    for ym, items in sorted(grouped.items()):
        y, m = ym.split("-")
        lines.append(f"── {int(m)}월 ──")
        for s in items:
            s_start = parse_date(s["date"])
            if s.get("end"):
                s_end = parse_date(s["end"])
                date_str = f"{fmt_date(s_start)}~{fmt_date(s_end)}"
            else:
                date_str = fmt_date(s_start)
            lines.append(f"• {s['event']}\n  {date_str}")
    text = "\n".join(lines)
    # 카카오 메시지 최대 1000자 제한
    if len(text) > 950:
        text = text[:950] + "\n\n(이후 일정은 월별로 조회해주세요)"
    return kakao_response(text, MAIN_BUTTONS)

@app.route("/chat", methods=["POST"])
def chat():
    text = "아래 버튼으로 원하는 일정을 조회해보세요! 😊"
    return kakao_response(text, MAIN_BUTTONS)

# =============================================
# 내정초 알리미 엔드포인트
# =============================================
NEIS_KEY = "d9492c1dac924cea87798bb22de4a376"
NAEJEONG_OFFICE = "J10"
NAEJEONG_SCHOOL = "7551054"

def get_kst_today():
    import pytz
    KST = pytz.timezone('Asia/Seoul')
    return datetime.now(KST).strftime("%Y%m%d")

def get_kst_month():
    import pytz
    KST = pytz.timezone('Asia/Seoul')
    return datetime.now(KST).strftime("%Y%m")

def clean_menu(text):
    import re
    return re.sub(r'\([^)]*\)', '', text).strip()

@app.route("/naejeong/meal", methods=["POST"])
def naejeong_meal():
    today = get_kst_today()
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": NEIS_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": NAEJEONG_OFFICE,
        "SD_SCHUL_CODE": NAEJEONG_SCHOOL,
        "MLSV_YMD": today
    }
    try:
        res = requests.get(url, params=params).json()
        dishes = res["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]
        cleaned = [clean_menu(d) for d in dishes.split("<br/>")]
        menu = "\n".join(cleaned)
        text = f"🍱 오늘의 급식\n\n{menu}"
    except:
        text = "오늘은 급식 정보가 없어요 🍽️"
    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": text}}]}
    })

@app.route("/naejeong/schedule", methods=["POST"])
def naejeong_schedule():
    year_month = get_kst_month()
    url = "https://open.neis.go.kr/hub/SchoolSchedule"
    params = {
        "KEY": NEIS_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": NAEJEONG_OFFICE,
        "SD_SCHUL_CODE": NAEJEONG_SCHOOL,
        "AA_YMD": year_month
    }
    try:
        res = requests.get(url, params=params).json()
        rows = res["SchoolSchedule"][1]["row"]
        result = []
        for row in rows:
            d = row["AA_YMD"]
            name = row["EVENT_NM"]
            result.append(f"{d[4:6]}/{d[6:8]} {name}")
        text = f"📅 이번 달 학사일정\n\n" + "\n".join(result)
    except:
        text = "이번 달 학사일정이 없어요 📅"
    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": text}}]}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
