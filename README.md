# 공공채용 나침반 (MVP)
정적 사이트 + JSON + GitHub Actions(4시간). `scripts/collect.py` → `data/jobs.json` → `scripts/build.py` → `dist/`
- Secrets: `DATA_GO_KR_KEY`(알리오·나라일터), `WORK24_AUTH_KEY`(고용24) / Variables: `SITE_URL`, `ADSENSE_CLIENT`, `CNAME`
- 현재 data/jobs.json 은 예시 데이터(sample: true)
- 로컬: `python3 scripts/build.py && python3 -m http.server -d dist 8080`
