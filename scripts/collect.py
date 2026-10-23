"""채용공고 수집 → data/jobs.json  (키 값은 출력하지 않음)
1) 알리오  : https://apis.data.go.kr/1051000/recruitment/list (DATA_GO_KR_KEY, JSON)          data.go.kr/data/15125273
2) 나라일터: https://apis.data.go.kr/1760000/PblJobService/getList (DATA_GO_KR_KEY, XML)      data.go.kr/data/15156780
3) 고용24 공채속보: https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L21.do (WORK24_AUTH_KEY, XML)
소스별 실패는 건너뛰고 로그에 원인만 남김."""
import json, os, re, sys, time, datetime, collections, socket, urllib.parse, urllib.request, xml.etree.ElementTree as ET
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "jobs.json")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
K, WK = os.environ.get("DATA_GO_KR_KEY", "").strip(), os.environ.get("WORK24_AUTH_KEY", "").strip()
def red(s):
    s = str(s)
    for k in (K, WK, urllib.parse.quote(K, safe=""), urllib.parse.quote(WK, safe="")):
        if k: s = s.replace(k, "***")
    return s[:300]
def get(url, t=45):
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=t) as r: return r.read().decode("utf-8", "replace")
def qs(d): return urllib.parse.urlencode(d, safe="%")
def diag(host):
    for port in (443, 80):
        try: socket.create_connection((host, port), timeout=8).close(); print(f"[진단] {host}:{port} 연결 가능"); return
        except Exception as e: print(f"[진단] {host}:{port} 연결 불가: {type(e).__name__}")

def alio():
    out = []
    for page in range(1, 6):
        txt = None
        for base in ("https://apis.data.go.kr", "http://apis.data.go.kr"):
            try: txt = get(f"{base}/1051000/recruitment/list?" + qs({"serviceKey": K, "resultType": "json", "numOfRows": 500, "pageNo": page, "ongoingYn": "Y"})); break
            except Exception as e: print("[알리오]", base.split(":")[0], red(e))
        if txt is None: raise RuntimeError("연결 실패")
        try: d = json.loads(txt)
        except Exception: raise RuntimeError("JSON 아님: " + red(txt[:200]))
        rows = d.get("result") or []
        if page == 1: print("[알리오] resultCode", d.get("resultCode"), d.get("resultMsg"), "total", d.get("totalCount"), "필드", list(rows[0].keys())[:20] if rows else [])
        for r in rows:
            out.append({"id": f"A{r.get('recrutPblntSn')}", "src": "알리오", "org": r.get("instNm"), "title": r.get("recrutPbancTtl"), "type": r.get("hireTypeNmLst"),
                "region": r.get("workRgnNmLst"), "career": r.get("recrutSeNm"), "count": r.get("recrutNope"), "start": r.get("pbancBgngYmd"), "end": r.get("pbancEndYmd"),
                "url": r.get("srcUrl") or f"https://job.alio.go.kr/recruitview.do?idx={r.get('recrutPblntSn')}", "edu": r.get("acbgCondNmLst"), "field": r.get("ncsCdNmLst"), "salary": "",
                "detail": {k: r.get(f) for k, f in (("응시자격", "aplyQlfcCn"), ("우대사항", "prefCn"), ("전형절차", "scrnprcdrMthdExpln"), ("결격사유", "disqlfcRsn")) if r.get(f)}})
        if len(rows) < 500: break
    return out

NARA = "https://apis.data.go.kr/1760000/PblJobService/getList"
def nara_page(page, extra=None, tries=(60, 90)):
    p = {"serviceKey": K, "numOfRows": 100, "pageNo": page, **(extra or {})}
    last = None
    for t in tries:
        try:
            root = ET.fromstring(get(NARA + "?" + qs(p), t))
            err = root.findtext(".//errMsg") or root.findtext(".//returnAuthMsg")
            if err: raise RuntimeError(red(err))
            return int(root.findtext(".//totalCount") or 0), [{c.tag: (c.text or "") for c in it} for it in root.findall(".//item")]
        except Exception as e:
            last = e; print(f"[나라일터] page {page} 재시도({t}s):", red(e)); time.sleep(5)
    raise RuntimeError(red(last))
NARA_KW = ["2026", "공무직", "직원", "모집", "재공고", "경력경쟁", "연구원", "신규", "정규직", "청원경찰", "선발", "실무", "운영", "공무원", "채용", "기간제"]
def nara():
    """명세상 정렬·기간 파라미터 없음, 오래된 순 응답. 전체 마지막 페이지는 서버 시간초과 →
    제목 검색어별 totalCount로 마지막 페이지부터 역순 수집(45일 이전 등록이면 중단), 재시도·긴 타임아웃, 전체 12분 제한"""
    t0, cutoff = time.time(), (datetime.date.today() - datetime.timedelta(days=45)).strftime("%Y%m%d")
    rows, stat = [], {}
    for kw in NARA_KW:
        if time.time() - t0 > 720: print("[나라일터] 시간 제한 도달"); break
        try: total, _ = nara_page(1, {"title": kw}, tries=(60,))
        except Exception as e: stat[kw] = "실패"; continue
        last, got = (total + 99) // 100, 0
        for page in range(last, max(0, last - 4), -1):
            try: _, r = nara_page(page, {"title": kw})
            except Exception: break
            rows += r; got += len(r)
            regs = [re.sub(r"\D", "", x.get("regdate", ""))[:8] for x in r if x.get("regdate")]
            if regs and min(regs) < cutoff: break
        stat[kw] = f"{total}중 {got}"
    print("[나라일터] 검색어별", stat)
    if not rows: raise RuntimeError("0건")
    for k in ("areacode", "type01", "type02"):
        print(f"[나라일터] {k} 분포", collections.Counter(x.get(k) for x in rows).most_common(30))
    out, seen = [], set()
    for g in rows:
        i = g.get("idx")
        if not i or i in seen: continue
        seen.add(i)
        out.append({"id": f"G{i}", "src": "나라일터", "org": g.get("insttname"), "title": g.get("title"), "type": g.get("type02", ""), "region": "",
            "areacode": g.get("areacode", ""), "type01": g.get("type01", ""), "type02": g.get("type02", ""),
            "career": "", "count": "", "start": re.sub(r"\D", "", g.get("regdate", ""))[:8], "end": re.sub(r"\D", "", g.get("enddate", ""))[:8],
            "url": f"https://www.gojobs.go.kr/apmView.do?empmnsn={i}", "edu": "", "field": "", "salary": "", "detail": {}})
    return out

def work24():
    out = []
    for page in range(1, 11):
        x = ET.fromstring(get("https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L21.do?" + qs({"authKey": WK, "callTp": "L", "returnType": "XML", "startPage": page, "display": 100})))
        err = x.findtext(".//e") or x.findtext(".//errMsg") or x.findtext(".//message")
        if err: raise RuntimeError(red(err))
        rows = [{c.tag: (c.text or "").strip() for c in it} for it in x.findall(".//dhsOpenEmpInfo")]
        if page == 1: print("[공채속보] total", x.findtext(".//total"), "필드", list(rows[0].keys()) if rows else [], "root", x.tag)
        for g in rows:
            out.append({"id": f"W{g.get('empSeqno')}", "src": "고용24 공채속보", "org": g.get("empBusiNm"), "title": g.get("empWantedTitle"), "type": g.get("empWantedTypeNm"),
                "region": "", "career": "", "count": "", "start": g.get("empWantedStdt", ""), "end": g.get("empWantedEndt", ""), "orgType": g.get("coClcdNm", ""),
                "url": g.get("empWantedHomepgDetail") or g.get("empWantedMobileUrl") or f"https://www.work24.go.kr/wk/a/b/1500/retriveDtlEmpSrchList.do?empSeqno={g.get('empSeqno')}",
                "edu": "", "field": "", "salary": "", "detail": {}})
        if len(rows) < 100: break
    return out

def main():
    diag("apis.data.go.kr"); diag("www.work24.go.kr")
    items, ok, stats = [], [], {}
    for name, fn, key in (("알리오", alio, K), ("나라일터", nara, K), ("고용24 공채속보", work24, WK)):
        if not key: print(f"{name}: 키 없음"); stats[name] = "키 없음"; continue
        try: r = fn(); items += r; ok.append(name); stats[name] = len(r); print(f"== {name}: {len(r)}건")
        except Exception as e: stats[name] = f"실패 {type(e).__name__}: {red(e)}"; print(f"== {name}: 실패", red(e))
    json.dump(stats, open(os.path.join(os.path.dirname(OUT), "stats.json"), "w", encoding="utf-8"), ensure_ascii=False)
    if not items: print("수집 0건: 기존 데이터 유지"); return 0
    json.dump({"sample": False, "generated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M") + " (KST)", "sources": ok, "data": items}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print("saved", len(items)); return 0
if __name__ == "__main__": sys.exit(main())
