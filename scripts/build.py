"""data/jobs.json -> dist/ (index.html, data.json, j/<id>.html, sitemap.xml, robots.txt, ads.txt)"""
import json, os, re, html, shutil, datetime, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import region_of
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
    a = regions(AREA.get(str(r.get("areacode", "")).strip(), ""))
    if a != ["전국"]: return a
    g = region_of(r.get("org") or "")
    if g != "전국": return ["전남", "광주"] if g == "전남·광주" else [g]
    return regions(r.get("org", "") + " " + r.get("title", ""))
AREA = json.load(open(f"{ROOT}/data/nara_area.json", encoding="utf-8")) if os.path.exists(f"{ROOT}/data/nara_area.json") else {}
items = []
for r in D["data"]:
    end = ymd(r.get("end"))
    if end and end < TODAY: continue
    dd = (end - TODAY).days if end else None
    items.append({**r, "id": re.sub(r"[^A-Za-z0-9_-]", "", str(r["id"])), "regions": job_regions(r), "emp": emp((r.get("type") or "") + " " + (r.get("title") or "")), "eduL": edu(r.get("edu")),
        "car": car(r.get("career")), "fields": ([x.strip() for x in re.split(r"[,|]", r.get("field") or "") if x.strip()] or ([r["orgType"]] if r.get("orgType") else ["공무직·공공" if r.get("src")=="나라일터" else "기타"]))[:3], "dd": dd, "endS": end.isoformat() if end else "채용 시 마감"})
items.sort(key=lambda x: (x["dd"] is None, x["dd"] if x["dd"] is not None else 0))
ADHEAD = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>' if ADS else ""
def ad(slot): return f'<div class="ad">광고 자리 (애드센스 {slot})</div>'
SAMPLE = '<div class="sample">⚠ 예시 데이터입니다. 실제 채용공고가 아니며, API 연결 후 실제 공고로 바뀝니다.</div>' if D.get("sample") else ""
CSS = open(f"{ROOT}/templates/style.css", encoding="utf-8").read()
CPA = [("NCS·필기 인강 할인", "CPA 자리: 공기업 NCS 강의"), ("이력서·자소서 첨삭", "CPA 자리: 이력서 서비스"), ("컴활·한국사 자격증 단기 합격", "CPA 자리: 자격증 강의"), ("공무원 시험 무료 체험강의", "CPA 자리: 공무원 인강")]
def cpa(i): c = CPA[i % len(CPA)]; return f'<a class="cpa" href="#" rel="sponsored nofollow">{c[0]}<small>{c[1]}</small></a>'
def dlab(x): return "상시" if x["dd"] is None else ("오늘 마감" if x["dd"] == 0 else f"D-{x['dd']}")
def page(title, desc, body, canonical, extra=""):
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">{ADHEAD}{extra}<style>{CSS}</style></head><body>{SAMPLE}{body}
<footer>출처: 공공기관 채용정보(알리오)·나라일터·고용24 공개 데이터. 지원 전 반드시 원문 공고를 확인하세요.<br>업데이트: {e(D.get("generated_at"))}</footer></body></html>'''
out = f"{ROOT}/dist"; shutil.rmtree(out, ignore_errors=True); os.makedirs(f"{out}/j")
for i, x in enumerate(items):
    det = x.get("detail") or {}
    qual = summ = ""
    q = det.get("응시자격") or det.get("aplyQlfcCn") or ""
    qual = f'{x["eduL"]} · {x["car"]}'
    rel = [y for y in items if y["id"] != x["id"] and (set(y["regions"]) & set(x["regions"]) or set(y["fields"]) & set(x["fields"]))][:4]
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
{cpa(i)}
{f'<section class="card2 rel"><h2>비슷한 채용공고</h2>' + "".join(f'<a href="{y["id"]}.html"><strong>{e(y["org"])}</strong><span>{e(y["title"])} · {dlab(y)}</span></a>' for y in rel) + '</section>' if rel else ""}
{ad("detail-bottom")}</main>
{f'<div class="sticky"><a href="{e(x["url"])}" rel="nofollow noopener" target="_blank">원문 공고 보고 지원하기</a></div>' if x.get("url") else ""}'''
    title = f'{x["org"]} {x["emp"]} 채용 {dlab(x)} | {", ".join(x["regions"])} {x["eduL"]} | 공공채용 나침반'
    desc = f'{x["org"]} {x["title"]}. {x["emp"]}, {", ".join(x["regions"])}, {x["eduL"]}·{x["car"]}, 마감 {x["endS"]}.{(" 급여 "+x["salary"]+".") if x.get("salary") else ""}'[:155]
    ld = json.dumps({"@context": "https://schema.org", "@type": "JobPosting", "title": x["title"], "datePosted": str(x.get("start")), "validThrough": x["endS"] if x["dd"] is not None else None,
        "hiringOrganization": {"@type": "Organization", "name": x["org"]}, "employmentType": x["emp"], "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress", "addressRegion": ", ".join(x["regions"]), "addressCountry": "KR"}},
        "description": x["title"]}, ensure_ascii=False)
    open(f'{out}/j/{x["id"]}.html', "w", encoding="utf-8").write(page(title, desc, body, f'{SITE}/j/{x["id"]}.html', f'<script type="application/ld+json">{ld}</script>'))
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
open(f"{out}/index.html", "w", encoding="utf-8").write(page("공공채용 나침반 | 공공기관·공기업 채용공고 마감순", "공공기관, 공기업, 공무직 채용공고를 업종·지역·고용형태·학력·마감일로 찾아보세요.", body, f"{SITE}/"))
urls = [f"{SITE}/"] + [f'{SITE}/j/{x["id"]}.html' for x in items]
open(f"{out}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls) + "</urlset>")
open(f"{out}/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
if ADS: open(f"{out}/ads.txt", "w").write(f"google.com, {ADS.replace('ca-', '')}, DIRECT, f08c47fec0942fa0\n")
if os.environ.get("CNAME"): open(f"{out}/CNAME", "w").write(os.environ["CNAME"])
print("built", len(items))
