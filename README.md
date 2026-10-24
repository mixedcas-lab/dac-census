<p>
  <a href="https://mcas.uos.ac.kr"><img src="assets/mcaslab.png" alt="MCAS Lab" height="34"></a>
  &nbsp;&nbsp;
  <a href="https://www.uos.ac.kr"><img src="assets/uos.png" alt="University of Seoul" height="20"></a>
</p>

# DAC Census

ISSCC, VLSI, JSSC, CICC, ESSCIRC/ESSERC, A-SSCC, SSC-L, TCAS-I/II, TVLSI에 실린 DAC(디지털-아날로그 변환기) 논문을 모아 보여주는 사이트입니다. MCAS Lab(서울시립대학교 첨단융합학부)에서 운영합니다. ADC는 자매 사이트 [ADC Census](https://mixedcas-lab.github.io/adc-census/)에서 다룹니다. 2026-10-24에 ADC Census의 DAC 부분을 이 사이트로 분리했습니다.

- 사이트: https://mixedcas-lab.github.io/dac-census/
- 데이터 출처: IEEE Xplore API (서지 메타데이터와 링크만 공개, 초록·본문은 올리지 않음)

## 구성

```
index.html, app.js, style.css   사이트 (빌드 과정 없음, GitHub Pages가 그대로 서비스)
data/papers.json                DAC 논문 목록 (빌더가 생성)
data/meta.json                  갱신일, 범위, 집계
data/annotations.csv            검수 값 (사람이 편집)
collector/build.py              adc-census 캐시를 읽어 papers.json 생성 (Python 3.8+, 표준 라이브러리만)
collector/classify.py           DAC 판별, 유형(Nyquist/Oversampling)·구조·응용 태깅, 수치 추출 규칙
collector/venues.json           시작 연도, 캐시 위치, venue 매칭 규칙
scripts/update.sh               랩 서버 cron용: 재생성 → 커밋 → push
```

## 동작 방식

1. **데이터**: adc-census 수집기가 같은 학회·저널의 전체 논문을 랩 서버 캐시(`~/adc-census/cache/raw`)에 받아 둡니다. 이 저장소는 그 캐시를 읽기만 하므로 IEEE API를 따로 쓰지 않습니다. IEEE Access는 adc-census가 변환기 논문만 받기 때문에 제외했습니다.
2. **분류**: 제목에 DAC, digital-to-analog, D/A, RF-DAC가 있으면 core입니다. ADC·ΔΣ 변조기·CIM 안의 DAC(SAR ADC의 커패시터 DAC, CTDSM의 피드백 DAC 등)는 ADC 논문이므로 제외하고, 송신기·링크 안의 DAC는 related로 둡니다.
3. **수치**: 제목·초록에서 분해능, 샘플링 속도, SFDR, IM3, NSD, ACLR, SNDR/SNR/DR, 전력, 공정, 면적을 정규식으로 뽑습니다. 제목 값을 우선하고, 초록에 같은 항목의 값이 여럿이면(주파수·모드별) 추측하지 않고 비워 둡니다. 샘플당 에너지 P/f<sub>s</sub>는 전력과 샘플링 속도로 계산합니다.
4. **공개**: cron이 매일 06:42(adc-census 06:17 갱신 뒤) 재생성하고, 바뀐 것이 있으면 커밋·push합니다.

## 그래프

Chart 메뉴: SFDR vs. 샘플링 속도, 분해능 vs. 샘플링 속도, 전력 vs. 샘플링 속도, 샘플당 에너지 vs. 샘플링 속도, SNDR/DR vs. 샘플링 속도, 연도별 SFDR, Custom(x·y축 직접 선택).

## 검수 값 넣기

GitHub 웹에서 `data/annotations.csv`를 열어 연필 아이콘으로 편집합니다. 수집기를 다시 돌릴 필요 없이 사이트에 즉시 반영됩니다.

| 열 | 내용 |
|---|---|
| `id` | IEEE article number (Xplore 주소 끝의 숫자) |
| `exclude` | `1`이면 목록에서 제외 (오탐) |
| `type` | `Nyquist` 또는 `Oversampling` |
| `arch`, `app` | 여러 개면 `;`로 구분 (예: `Current-steering;RF-DAC`) |
| `res` | bit |
| `fs` | S/s (`10G`, `100M`) |
| `sfdr`, `aclr`, `sndr` | dB(c) |
| `imd`, `nsd` | dBc, dB/Hz (음수) |
| `p` | W (`9.4m`) |
| `node`, `area` | nm, mm² |
| `cal` | `1`이면 보정 기법 사용, `0`이면 미사용 (비우면 자동 판정) |
| `note`, `by` | 메모, 검수자. 메모는 목록에 표시되고 검색창에서도 찾을 수 있습니다 |

## 랩 서버 설정 (1회)

adc-census가 같은 서버에 설정되어 있어야 합니다(`~/adc-census/cache/raw`).

```bash
ssh-keygen -t ed25519 -f ~/.ssh/dac_census -N "" -C "dac-census@lab-server"   # 공개키를 저장소 Deploy keys에 쓰기 권한으로 등록
cat >> ~/.ssh/config <<'CFG'
Host github-dac-census
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/dac_census
  IdentitiesOnly yes
CFG
git clone github-dac-census:mixedcas-lab/dac-census.git ~/dac-census
cd ~/dac-census && git config user.name "MCAS Lab bot" && git config user.email "연구실-메일-주소"
mkdir -p logs
( crontab -l; echo "42 6 * * * PYTHON=$(command -v python3) $HOME/dac-census/scripts/update.sh >> $HOME/dac-census/logs/update.log 2>&1" ) | crontab -
```

GitHub Pages: 저장소 **Settings → Pages**에서 Source를 **Deploy from a branch**, Branch를 **main / (root)**로 지정합니다.

### 수치 수정 요청

- 사이트의 각 논문 아래 **Report a fix**를 누르면 GitHub 이슈 작성 화면이 열립니다. 논문 id, 현재 값과 출처, annotations.csv 행 형식이 미리 채워져 있으니 고칠 항목·값·근거(표·그림·쪽)만 적으면 됩니다(GitHub 계정 필요).
- 연구실은 이슈를 확인해 `data/annotations.csv`에 행을 추가하고 이슈를 닫습니다. 저장소 쓰기 권한이 있으면 annotations.csv를 직접 고쳐도 됩니다.
- DAC가 송신기·링크의 블록인 논문(related)은 논문의 수치가 DAC 값이 아니므로 자동·AI 수치를 표시하지 않고 "—"로 둡니다. 사람이 검수한 값은 표시합니다.

### 값의 출처와 삭제

- 사이트는 값마다 출처를 표시합니다: `T` 제목, `A` 초록(둘 다 정규식 자동 추출, 회색), `AI` AI 도구 추출(보라색 기울임, 미검수), `✓` 연구실 검수(진한 색).
- annotations.csv의 행은 기본적으로 **사람 검수**로 처리합니다. `by` 열에 Codex·GPT·Claude 같은 AI 도구 이름이 있거나 `source` 열이 `ai`이면 **AI 추출**로 처리합니다.
- 값이 서로 다를 때 우선순위: 사람 검수 > AI 추출 > 정규식(제목·초록). AI 값은 더 높은 출처를 덮어쓰지 않고, 다르면 목록에 `Review` 태그를 붙입니다. AI 행의 메모는 표시하지 않습니다.
- 칸을 비우면 기존 값을 유지합니다. **잘못된 자동값을 지우려면 `-`(또는 `NA`)** 를 넣습니다. 사이트에는 "—"로 표시됩니다.
- 사이트의 Values 필터로 검수된 값만 보거나, 그래프에서 검수 값(채운 점)·AI 값(점선 테두리)·자동 값(테두리)을 구분해 볼 수 있습니다.

## 참고

- IEEE Xplore API 이용약관을 따릅니다. 초록과 본문은 공개하지 않고, 서지 정보와 Xplore 링크만 제공합니다.
- 자동 추출 수치는 오류가 있을 수 있습니다. SFDR은 논문마다 측정 출력 주파수가 다르니 비교 시 원문을 확인하세요.
