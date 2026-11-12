"""data/jobs.json -> dist/ (index.html, data.json, j/<id>.html, sitemap.xml, robots.txt, ads.txt)"""
import json, os, re, html, shutil, datetime, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import region_of
try:
    from PIL import Image, ImageDraw, ImageFont
    _FONT_DIR = "/usr/share/fonts/opentype/noto"
    FONT_B = f"{_FONT_DIR}/NotoSansCJK-Bold.ttc" if os.path.exists(f"{_FONT_DIR}/NotoSansCJK-Bold.ttc") else None
    FONT_R = f"{_FONT_DIR}/NotoSansCJK-Regular.ttc" if os.path.exists(f"{_FONT_DIR}/NotoSansCJK-Regular.ttc") else None
    HAS_PIL = bool(FONT_B and FONT_R)
except Exception:
    HAS_PIL = False
    FONT_B = FONT_R = None
def make_card(path, org, main, sub):
    """링크 미리보기(OG)용 카드 이미지 1200x630 생성. 실패하면 False (빌드는 계속)."""
    if not HAS_PIL: return False
    try:
        W, H = 1200, 630
        NAVY, BLACK, GRAY = (27, 58, 107), (17, 17, 17), (110, 110, 110)
        img = Image.new("RGB", (W, H), (255, 255, 255))
        d = ImageDraw.Draw(img)
        def fit(text, fp, size, min_size=30):
            while size > min_size:
                f = ImageFont.truetype(fp, size)
                if d.textbbox((0, 0), text, font=f)[2] <= 1080: return f
                size -= 4
            return ImageFont.truetype(fp, min_size)
        def center(text, y, f, fill):
            b = d.textbbox((0, 0), text, font=f)
            d.text(((W - (b[2] - b[0])) / 2 - b[0], y), text, font=f, fill=fill)
        d.rectangle([0, 0, W, 84], fill=NAVY)
        center("공공채용 나침반", 22, ImageFont.truetype(FONT_B, 38), (255, 255, 255))
        center(org, 150, fit(org, FONT_B, 76), NAVY)
        center(main, 262, fit(main, FONT_B, 108), BLACK)
        d.line([300, 440, 900, 440], fill=(200, 208, 220), width=3)
        center(sub, 472, fit(sub, FONT_R, 44, 26), GRAY)
        d.rectangle([0, H - 26, W, H], fill=NAVY)
        img.save(path, optimize=True)
        return True
    except Exception:
        return False
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITE = os.environ.get("SITE_URL", "https://example.com").rstrip("/")
ADS = os.environ.get("ADSENSE_CLIENT", "")
D = json.load(open(f"{ROOT}/data/jobs.json", encoding="utf-8"))
TODAY = datetime.date.today()
e = lambda v: html.escape(str(v or "")).strip()
SIDO = ["서울","부산","대구","인천","광주","대전","울산","세종","경기","강원","충북","충남","전북","전남","경북","경남","제주"]
def regions(s):
    s = (s or "").replace("전남광주", "전남,광주").replace("충청북도","충북").replace("충청남도","충남").replace("경상북도","경북").replace("경상남도","경남").replace("전라북도","전북").replace("전라남도","전남")
    r = [x for x in SIDO if x in s]
    return r or ["전국"]
def emp(t):
    t = t or ""
    if "인턴" in t: return "인턴"
    if "공무직" in t: return "무기계약직"
    if "정규" in t: return "정규직"
    if "무기" in t: return "무기계약직"
    if "비정규" in t or "기간제" in t or "계약" in t: return "계약직"
    return "기타"
def edu(s):
    s = s or ""
    if "무관" in s or not s: return "학력무관"
    for k in ("고졸","대졸(2~3년)","대졸(4년)","석사","박사"):
        if k in s: return k
    return "기타"
def car(s):
    s = s or ""
    return "신입·경력" if ("신입" in s and "경력" in s) else ("경력" if "경력" in s else "신입")
def ymd(s):
    try: return datetime.datetime.strptime(str(s)[:8], "%Y%m%d").date()
    except Exception: return None
def rich(s):
    out, lvl = [], 0
    for L in re.split(r"\r?\n", s or ""):
        L = L.strip()
        if not L: continue
        m1 = re.match(r"^(?:[○●□■ㅇ]|\d+\.(?!\d)|[①-⑳])\s*(.*)", L); m2 = re.match(r"^(?:[-·ㆍ]|\d+\))\s*(.*)", L); mn = re.match(r"^(?:※|\*)\s*(.*)", L)
        if mn:
            out += ["</ul>"] * lvl; lvl = 0; out.append(f'<p class="note">※ {e(mn.group(1))}</p>')
        elif m1 or m2:
            want = 1 if m1 else 2
            while lvl < want: out.append('<ul class="l%d">' % (lvl + 1)); lvl += 1
            while lvl > want: out.append("</ul>"); lvl -= 1
            out.append(f"<li>{e((m1 or m2).group(1))}</li>")
        else:
            out += ["</ul>"] * lvl; lvl = 0; out.append(f"<p>{e(L)}</p>")
    out += ["</ul>"] * lvl
    return "".join(out)
def job_regions(r):
    if r.get("region"): return regions(r["region"])
    ac = str(r.get("areacode", "")).strip()
    if ac[:2] in SIDO_CODE: return SIDO_CODE[ac[:2]]
    g = region_of(r.get("org") or "")
    if g != "전국": return ["전남", "광주"] if g == "전남·광주" else [g]
    return regions(r.get("org", "") + " " + r.get("title", ""))
# 행정구역 시도코드(앞 2자리). 12는 전남광주통합특별시로 추정
SIDO_CODE = {"11":["서울"],"26":["부산"],"27":["대구"],"28":["인천"],"29":["광주"],"30":["대전"],"31":["울산"],"36":["세종"],"41":["경기"],"42":["강원"],"51":["강원"],"43":["충북"],"44":["충남"],"45":["전북"],"52":["전북"],"46":["전남"],"12":["전남","광주"],"47":["경북"],"48":["경남"],"50":["제주"]}
items = []
for r in D["data"]:
    end = ymd(r.get("end"))
    if end and end < TODAY: continue
    dd = (end - TODAY).days if end else None
    items.append({**r, "id": re.sub(r"[^A-Za-z0-9_-]", "", str(r["id"])), "regions": job_regions(r), "emp": emp((r.get("type") or "") + " " + (r.get("title") or "")), "eduL": edu(r.get("edu")),
        "car": car(r.get("career")), "fields": ([x.strip() for x in re.split(r"[,|]", r.get("field") or "") if x.strip()] or ([r["orgType"]] if r.get("orgType") else ["공무직·공공" if r.get("src")=="나라일터" else "기타"]))[:3], "dd": dd, "endS": end.isoformat() if end else "채용 시 마감"})
items.sort(key=lambda x: (x["dd"] is None, x["dd"] if x["dd"] is not None else 0))
ADHEAD = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>' if ADS else ""
GA = os.environ.get("GA_ID", "GT-NSSSWH8S")
GAHEAD = f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{GA}");</script>' if GA else ""
# ===== 상세 페이지 고정 광고 슬롯 (2026-11-11, RPM 개선 테스트) =====
# 자동광고만으로는 상세 페이지에 광고가 거의 붙지 않아 수동 슬롯을 켠다.
# 사용자 결정(2026-11-11): 광고 단위는 1개만 만들고 노출이 가장 많은 히어로 아래(상단)에만 적용한다.
# 슬롯 ID는 AdSense 콘솔의 디스플레이 광고 단위. 값이 없으면 빈 문자열을 반환해 기존 동작과 같아진다.
AD_SLOTS = {"detail-top": "6273657390", "detail-mid": "6273657390", "detail-bottom": "6273657390", "list-top": "6273657390"}
def ad(slot):
    sid = AD_SLOTS.get(slot)
    if not ADS or not sid or sid.startswith("SLOT"): return ""
    return (f'<div class="adbox" style="margin:18px 0;min-height:100px;text-align:center">'
            f'<ins class="adsbygoogle" style="display:block" data-ad-client="{ADS}" data-ad-slot="{sid}" '
            f'data-ad-format="auto" data-full-width-responsive="true"></ins>'
            f'<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></div>')
SAMPLE = '<div class="sample">⚠ 예시 데이터입니다. 실제 채용공고가 아니며, API 연결 후 실제 공고로 바뀝니다.</div>' if D.get("sample") else ""
CSS = open(f"{ROOT}/templates/style.css", encoding="utf-8").read()
CPA = [("NCS·필기 인강 할인", "CPA 자리: 공기업 NCS 강의"), ("이력서·자소서 첨삭", "CPA 자리: 이력서 서비스"), ("컴활·한국사 자격증 단기 합격", "CPA 자리: 자격증 강의"), ("공무원 시험 무료 체험강의", "CPA 자리: 공무원 인강")]
def cpa(i): return ""
# ===== 수익 스택 '준비하기' 섹션 (2026-11-09, 표본 단계) =====
# 2026-11-09 표본 확인 후 전체 확대: classify() 자동 판정으로 교체. 쿠팡 링크가 없는 카테고리는 섹션을 붙이지 않는다.
# 제휴 링크는 공고별이 아니라 카테고리별 기본값(PREP_LINKS)으로 관리한다 — 같은 카테고리 공고는 같은 링크 재사용.
# PREP_LINKS 값이 비어 있으면 버튼에 '링크 자리' 배지가 붙는다. 실제 링크는 사용자 계정에서 생성해 채울 것.
# 상담(consult) 층: 텐핑 자격증 카테고리에서 본류 연결 가능한 건 손해평가사 캠페인뿐 (2026-11-09 사용자 확인 — 간호사·사회복지사 캠페인 없음. 베이비시터·약용식물자원관리사는 민간 자격이라 본류 제외). 손해평가사 관련 공고가 표본에 들어올 때 카테고리를 추가하고 consult를 켤 것.
ALERT_FORM_ENDPOINT = ""  # 마감 알림 신청 폼 전송 주소 슬롯. 비어 있으면 폼은 '준비 중' 상태로 동작한다.
PREP_CATS = {
    "ncs": {"books": ["NCS 직업기초능력평가 필기 교재"], "course": None, "consult": None},
    "it_security": {"books": ["정보보안기사 필기 교재"], "course": "정보보안 실무 강의 (Udemy)", "consult": None},
    "nurse": {"books": ["간호사 국가시험 핵심 교재"], "course": None, "consult": None},
    "electric": {"books": ["전기기사 필기 기출문제집"], "course": None, "consult": None},
    "social_worker": {"books": ["사회복지사 1급 종합 교재"], "course": None, "consult": None},
    "med_lab": {"books": ["임상병리사 국가시험 핵심 교재"], "course": None, "consult": None},
    "med_ot": {"books": ["작업치료사 국가시험 핵심 교재"], "course": None, "consult": None},
    "med_assistant": {"books": ["간호조무사 시험 핵심 교재"], "course": None, "consult": None},
    "history": {"books": ["한국사능력검정시험 심화 교재"], "course": None, "consult": None},
    "office_it": {"books": ["컴퓨터활용능력 필기·실기 교재"], "course": None, "consult": None},
    "caregiver": {"books": ["요양보호사 자격시험 표준 교재"], "course": None, "consult": None},
}
PREP_LINKS = {
    "ncs": {"coupang": "https://link.coupang.com/a/iwIXsxAQWy", "yes24": None, "udemy": ""},
    "it_security": {"coupang": "https://link.coupang.com/a/iwJg70YdcO", "yes24": None, "udemy": "https://lase.kr/click.php?m=udemy&a=A100709736&l=0000"},
    "nurse": {"coupang": "https://link.coupang.com/a/iwJmUbb2bI", "yes24": None, "udemy": ""},
    "electric": {"coupang": "https://link.coupang.com/a/iwJoRoUv0e", "yes24": None, "udemy": ""},
    "social_worker": {"coupang": "https://link.coupang.com/a/iwJqjs4WZM", "yes24": None, "udemy": ""},
    "med_lab": {"coupang": "https://link.coupang.com/a/iwTfeQGoXk", "yes24": None, "udemy": ""},
    "med_ot": {"coupang": "https://link.coupang.com/a/iwTgEVNhme", "yes24": None, "udemy": ""},
    "med_assistant": {"coupang": "https://link.coupang.com/a/iwThUclNiS", "yes24": None, "udemy": ""},
    "history": {"coupang": "https://link.coupang.com/a/iwVV12UCHc", "yes24": None, "udemy": ""},
    "office_it": {"coupang": "https://link.coupang.com/a/iwVXrfjcjI", "yes24": None, "udemy": ""},
    "caregiver": {"coupang": "https://link.coupang.com/a/iB3tnITag0", "yes24": None, "udemy": ""},
}
def classify(x):
    """공고 → 준비하기 카테고리 자동 판정 (2026-11-09 설계안). 자격(제목·응시자격·우대사항) 우선, 그다음 NCS 전형. 없으면 None."""
    det = x.get("detail") or {}
    title = x.get("title") or ""
    hay = title + " " + (det.get("응시자격") or "") + " " + (det.get("우대사항") or "")
    proc = det.get("전형절차") or ""
    if any(k in hay for k in ("정보보안기사", "정보보안산업기사", "정보처리기사", "정보처리산업기사", "정보처리기능사")): return "it_security"
    if "간호조무사" in hay and "간호사" not in title.replace("간호조무사", ""): return "med_assistant"
    if "간호사" in title or "간호사 면허" in hay or "간호사면허" in hay: return "nurse"
    if "임상병리사" in hay: return "med_lab"
    if "작업치료사" in hay: return "med_ot"
    if any(k in hay for k in ("전기기사", "전기산업기사", "전기기능사", "전기공사기사", "전기공사산업기사")): return "electric"
    if "사회복지사" in hay: return "social_worker"
    if any(k in title for k in ("의사", "전문의", "변호사", "회계사", "세무사", "약사")): return None  # 전문직은 전공 필기라 NCS 교재와 무관
    if any(k in proc for k in ("필기", "시험")) and any(k in proc for k in ("NCS", "직업기초", "직무수행능력", "직무능력", "인적성")): return "ncs"
    if "요양보호사" in hay: return "caregiver"
    if "한국사능력검정" in hay: return "history"
    if "컴퓨터활용능력" in hay: return "office_it"
    # 제목 폴백 (2026-11-12 보강): detail이 없어 전형절차를 못 보는 공고용.
    # 신입·공개채용 공채 패턴이면 NCS로 본다. 비정규·대체·의료연수 신호가 있으면 제외.
    if not any(k in title for k in ("기간제", "계약직", "촉탁", "일용", "단기", "특정업무직", "시간제", "무기계약직", "공무직", "인턴", "전공의", "레지던트", "대체", "휴직", "파견", "용역", "위촉", "아르바이트", "의료진", "교수", "약무", "약사", "원무", "취사", "조리", "미화", "간호", "치료사", "방사선", "임상", "치과", "수의", "진료", "영양", "경비", "운전", "노무", "위생", "시설관리", "업무지원직", "기술직", "기능직", "연구직", "전문직", "별정직", "교원", "예술감독", "연구지원")):
        if any(k in title for k in ("신입", "공개채용", "공채")):
            return "ncs"
    return None
def _plink(url, label, cls):
    if url is None: return ""  # None이면 버튼 자체를 숨긴다 (예: 그 카테고리는 쿠팡만 운영). ""는 '링크 자리' 표시.
    if url: return f'<a class="{cls}" href="{e(url)}" target="_blank" rel="nofollow sponsored noopener">{label}</a>'
    return f'<a class="{cls} slot" href="#" onclick="return false">{label} <span class="slotb">링크 자리</span></a>'
def prep(x):
    cat = classify(x)
    if not cat: return ""
    cfg, L = PREP_CATS[cat], PREP_LINKS[cat]
    if not L.get("coupang"): return ""  # 쿠팡 링크가 준비된 카테고리만 섹션을 붙인다
    p = ['<section class="card2 prep"><h2>📚 이 공고 준비하기</h2>']
    for b in cfg["books"]:
        p.append(f'<div class="pi"><p class="pt">교재 · {e(b)}</p><div class="pbtns">{_plink(L["coupang"], "쿠팡에서 보기", "pb main")}{_plink(L["yes24"], "예스24에서 보기", "pb sub")}</div></div>')
    if cfg["course"]:
        p.append(f'<div class="pi"><p class="pt">강의 · {e(cfg["course"])}</p><div class="pbtns">{_plink(L["udemy"], "Udemy에서 강의 보기", "pb main")}</div></div>')
    if cfg["consult"]:
        p.append(f'<div class="pi"><p class="pt">상담 · {e(cfg["consult"])} 준비 상담</p><div class="cslot">상담 신청 폼 자리 (텐핑 입력폼 연결 예정)</div></div>')
    p.append('<p class="pnote">이 섹션의 일부 링크는 제휴 링크입니다. 링크를 통해 구매·신청하시면 사이트 운영에 도움이 되는 수수료가 지급될 수 있습니다.</p>')
    org_f = f'{x["org"]} · {", ".join(x["fields"])}'
    if ALERT_FORM_ENDPOINT:
        form_open = f'<form class="aform" method="post" action="{e(ALERT_FORM_ENDPOINT)}">'
    else:
        form_open = '<form class="aform" onsubmit="event.preventDefault();this.querySelector(\'.amsg\').textContent=\'알림 신청은 준비 중입니다. 곧 열릴게요.\';">'
    p.append(f'''<div class="aform-wrap">{form_open}<h3>🔔 마감 알림 신청</h3><p class="atarget">{e(org_f)} 새 공고와 마감을 이메일로 알려드립니다.</p>
<input type="hidden" name="org" value="{e(x["org"])}"><input type="hidden" name="field" value="{e(", ".join(x["fields"]))}">
<input type="email" name="email" required placeholder="이메일 주소" autocomplete="email">
<label><input type="checkbox" required> 마감 알림 발송을 위한 이메일 수집·이용에 동의합니다</label>
<button type="submit">알림 신청하기</button><p class="amsg"></p></form></div></section>''')
    return "".join(p)
def dlab(x): return "상시" if x["dd"] is None else ("오늘 마감" if x["dd"] == 0 else f"D-{x['dd']}")
def page(title, desc, body, canonical, extra="", ogimg=""):
    OGIMG = f'<meta property="og:image" content="{ogimg}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">' if ogimg else ""
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">{OGIMG}{ADHEAD}{GAHEAD}{extra}<style>{CSS}</style></head><body>{SAMPLE}{body}
<footer>출처: 공공기관 채용정보(알리오)·나라일터·고용24 공개 데이터. 지원 전 반드시 원문 공고를 확인하세요.<br>업데이트: {e(D.get("generated_at"))}</footer></body></html>'''
out = f"{ROOT}/dist"; shutil.rmtree(out, ignore_errors=True); os.makedirs(f"{out}/j"); os.makedirs(f"{out}/cards")
OGMAP = {}
for i, x in enumerate(items):
    det = x.get("detail") or {}
    qual = summ = ""
    q = det.get("응시자격") or det.get("aplyQlfcCn") or ""
    qual = f'{x["eduL"]} · {x["car"]}'
    rel_all = [y for y in items if y["id"] != x["id"] and (y["org"] == x["org"] or set(y["regions"]) & set(x["regions"]) or set(y["fields"]) & set(x["fields"]))]
    rel_all.sort(key=lambda y: (y["org"] != x["org"], y["dd"] is None, y["dd"] if y["dd"] is not None else 0))
    rel = rel_all[:6]
    urgent = [y for y in items if y["id"] != x["id"] and y["dd"] is not None and y["dd"] <= 3][:5]
    folds = "".join(f'<details class="fold"><summary>{e(k)}</summary><div class="fb">{rich(v)}</div></details>' for k, v in det.items() if v)
    body = f'''<header class="top"><a href="../">← 공공채용 나침반</a></header><main class="detail">
<p class="crumb">{e(x["src"])} · {e(", ".join(x["fields"]))}</p><h1>{e(x["title"])}</h1>
<section class="hero">
<div class="h"><small>어디</small><strong>{e(x["org"])}</strong></div>
<div class="h"><small>무슨 일</small><strong>{e(", ".join(x["fields"]) or "공고문 참조")} · {e(x["emp"])}{f" · {x['count']}명" if x.get("count") else ""}</strong></div>
<div class="h"><small>마감</small><strong class="money">{dlab(x)} <span class="sm">({x["endS"]})</span></strong></div>
{f'<div class="h"><small>급여</small><strong>{e(x["salary"])}</strong></div>' if x.get("salary") else ""}
<div class="mini"><span>🎓 {e(qual)}</span><span>📍 {e(", ".join(x["regions"]))}</span></div></section>
{ad("detail-top")}
{folds}
<details class="fold"><summary>공고 기본정보</summary><div class="fb"><ul class="l1"><li>고용형태: {e(x.get("type"))}</li><li>근무지: {e(x.get("region"))}</li><li>학력: {e(x.get("edu"))}</li><li>채용구분: {e(x.get("career"))}</li><li>접수: {e(x.get("start"))} ~ {e(x.get("end"))}</li></ul></div></details>
{ad("detail-mid")}
{cpa(i)}{prep(x)}
{f'<section class="card2 rel"><h2>비슷한 채용공고</h2>' + "".join(f'<a href="{y["id"]}.html"><strong>{e(y["org"])}</strong><span>{e(y["title"])} · {dlab(y)}</span></a>' for y in rel) + '</section>' if rel else ""}
{f'<section class="card2 rel"><h2>⏰ 마감 임박 공고</h2>' + "".join(f'<a href="{y["id"]}.html"><strong>{e(y["org"])}</strong><span>{e(y["title"])} · {dlab(y)}</span></a>' for y in urgent) + '</section>' if urgent else ""}
{ad("detail-bottom")}</main>
{f'<div class="sticky"><a href="{e(x["url"])}" rel="nofollow noopener" target="_blank">원문 공고 보고 지원하기</a></div>' if x.get("url") else ""}'''
    title = f'{x["org"]} {x["emp"]} 채용 {dlab(x)} | {", ".join(x["regions"])} {x["eduL"]} | 공공채용 나침반'
    desc = f'{x["org"]} {x["title"]}. {x["emp"]}, {", ".join(x["regions"])}, {x["eduL"]}·{x["car"]}, 마감 {x["endS"]}.{(" 급여 "+x["salary"]+".") if x.get("salary") else ""}'[:155]
    ld = json.dumps({"@context": "https://schema.org", "@type": "JobPosting", "title": x["title"], "datePosted": str(x.get("start")), "validThrough": x["endS"] if x["dd"] is not None else None,
        "hiringOrganization": {"@type": "Organization", "name": x["org"]}, "employmentType": x["emp"], "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress", "addressRegion": ", ".join(x["regions"]), "addressCountry": "KR"}},
        "description": x["title"]}, ensure_ascii=False)
    if x["dd"] is None: dl_txt = "상시 채용"
    else:
        _p = x["endS"].split("-"); dl_txt = f"{int(_p[1])}월 {int(_p[2])}일 마감"
    sub_txt = f'{dl_txt} · {"/".join(x["regions"][:3])} · {x["eduL"]}'
    main_txt = f'{x["emp"]} 채용 {x["count"]}명' if x.get("count") else f'{x["emp"]} 채용'
    card_ok = make_card(f'{out}/cards/{x["id"]}.png', x["org"], main_txt, sub_txt)
    OGMAP[x["id"]] = (title, desc, f'{SITE}/cards/{x["id"]}.png' if card_ok else "")
    open(f'{out}/j/{x["id"]}.html', "w", encoding="utf-8").write(page(title, desc, body, f'{SITE}/j/{x["id"]}.html', f'<script type="application/ld+json">{ld}</script>', f'{SITE}/cards/{x["id"]}.png' if card_ok else ""))
LITE = [{k: x[k] for k in ("id", "org", "title", "regions", "emp", "eduL", "car", "fields", "dd", "salary")} for x in items]
json.dump(LITE, open(f"{out}/data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
FIELDS = sorted({f for x in items for f in x["fields"]})
opt = lambda xs: "".join(f"<option>{e(v)}</option>" for v in xs)
body = f'''<header class="top"><h1>공공채용 나침반</h1><p>공공기관·공기업·공무직 채용을 마감순으로</p></header><main>
<input id="q" type="search" placeholder="기관명, 공고 검색">
<div class="row"><select id="f"><option value="">업종 전체</option>{opt(FIELDS)}</select><select id="r"><option value="">지역 전체</option>{opt(["전국"]+SIDO)}</select>
<select id="t"><option value="">고용형태</option>{opt(["정규직","무기계약직","계약직","인턴"])}</select><select id="ed"><option value="">학력</option>{opt(["학력무관","고졸","대졸(2~3년)","대졸(4년)","석사","박사"])}</select>
<select id="c"><option value="">신입/경력</option>{opt(["신입","경력","신입·경력"])}</select><select id="d"><option value="">마감 전체</option><option value="3">3일 내</option><option value="7">7일 내</option><option value="30">30일 내</option></select></div>
<p id="cnt"></p>{ad("list-top")}<div id="list"></div><button id="more">더 보기</button>{cpa(0)}</main>
<script>{open(f"{ROOT}/templates/app.js", encoding="utf-8").read()}</script>'''
default_ok = make_card(f"{out}/cards/default.png", "공공채용 나침반", "공공·공기업 채용공고", "마감 임박순으로 한눈에 확인")
open(f"{out}/index.html", "w", encoding="utf-8").write(page("공공채용 나침반 | 공공기관·공기업 채용공고 마감순", "공공기관, 공기업, 공무직 채용공고를 업종·지역·고용형태·학력·마감일로 찾아보세요.", body, f"{SITE}/", "", f"{SITE}/cards/default.png" if default_ok else ""))
urls = [f"{SITE}/"] + [f'{SITE}/j/{x["id"]}.html' for x in items]
open(f"{out}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls) + "</urlset>")
open(f"{out}/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
if ADS: open(f"{out}/ads.txt", "w").write(f"google.com, {ADS.replace('ca-', '')}, DIRECT, f08c47fec0942fa0\n")
if os.environ.get("CNAME"): open(f"{out}/CNAME", "w").write(os.environ["CNAME"])
# ===== 옛 ID 링크 보존 스텁 (2026-11-10) =====
# 수집원 ID 교체로 상세 페이지가 사라지면 이미 공유된 링크(쓰레드 등)가 404가 되어 링크 카드가 깨진다.
# data/redirects.json: {"옛ID": "새ID"} — 새 공고가 없으면 빈 문자열(홈으로 안내).
# 스텁은 대상 페이지의 OG를 그대로 실어 공유 카드가 유지되고, 방문자는 즉시 대상 페이지로 이동한다.
# 대상 공고가 마감돼 사라지면 다음 빌드에서 자동으로 홈 안내로 강등된다.
try:
    REDIR = json.load(open(f"{ROOT}/data/redirects.json", encoding="utf-8"))
except Exception:
    REDIR = {}
HOME_OG = ("공공채용 나침반 | 공공기관·공기업 채용공고 마감순",
           "공공기관, 공기업, 공무직 채용공고를 업종·지역·고용형태·학력·마감일로 찾아보세요.",
           f"{SITE}/cards/default.png" if default_ok else "")
nstub = 0
for old, new in REDIR.items():
    if old in OGMAP: continue  # 살아 있는 ID는 건드리지 않는다
    if new and new in OGMAP:
        t, dsc, ogi = OGMAP[new]; target = f"{SITE}/j/{new}.html"
    else:
        t, dsc, ogi = HOME_OG; target = f"{SITE}/"
    stub_body = f'''<main class="detail"><h1>공고 주소가 바뀌었습니다</h1><p>찾으시는 공고 페이지 주소가 변경되어 자동으로 이동합니다. 이동하지 않으면 아래 링크를 눌러주세요.</p><p><a href="{target}">→ 이동된 페이지 보기</a></p></main>'''
    extra = f'<meta http-equiv="refresh" content="0; url={target}"><script>location.replace("{target}")</script>'
    open(f'{out}/j/{old}.html', "w", encoding="utf-8").write(page(t, dsc, stub_body, target, extra, ogi))
    nstub += 1
print("built", len(items), "| redirect stubs:", nstub)
