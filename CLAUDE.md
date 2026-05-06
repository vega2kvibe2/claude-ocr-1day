# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

영수증 지출 관리 앱 — Receipt Expense Tracker. 영수증 이미지/PDF를 업로드하면 Upstage Vision LLM(LangChain 경유)이 자동으로 파싱하여 구조화된 지출 데이터를 JSON 파일로 저장하는 경량 웹 애플리케이션입니다. 데이터베이스를 사용하지 않습니다.

**목표**: 1일 스프린트 MVP → Vercel 배포

## 개발 명령어

### 백엔드 (FastAPI)

```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 의존성 설치
pip install -r backend/requirements.txt

# 개발 서버 실행 (프로젝트 루트에서)
uvicorn backend.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 프론트엔드 (React + Vite)

```bash
cd frontend
npm install
npm run dev        # → http://localhost:5173
npm run build      # 프로덕션 빌드 → frontend/dist/
```

## 환경변수

`.env.example`을 복사해 `.env`를 만들고 값을 채웁니다. `.env`는 절대 커밋하지 않습니다.

| 변수명 | 사용 위치 |
|--------|----------|
| `UPSTAGE_API_KEY` | 백엔드 OCR 서비스 (프로덕션에서는 Vercel 환경변수) |
| `VITE_API_BASE_URL` | 프론트엔드 Axios baseURL (프로덕션에서는 빈 문자열 = 같은 도메인) |
| `DATA_FILE_PATH` | 백엔드: `VERCEL=1` 감지 시 자동으로 `/tmp/expenses.json` 사용 |

## 아키텍처

### 요청 흐름

```
브라우저 (React/Vite) → POST /api/upload (multipart)
                      → FastAPI 라우터 (upload.py)
                      → ocr_service.py: 이미지 전처리 → Base64 인코딩
                      → LangChain Chain: ChatUpstage Vision LLM 호출
                      → JsonOutputParser → 구조화 dict
                      → storage_service.py: expenses.json에 append
                      → 파싱된 JSON을 프론트엔드에 반환
```

### 디렉토리 구조 (목표)

```
receipt-tracker/
├── frontend/src/
│   ├── pages/          # Dashboard.jsx, UploadPage.jsx, ExpenseDetail.jsx
│   ├── components/     # DropZone, ParsePreview, ExpenseCard, SummaryCard,
│   │                   # FilterBar, Badge, Modal, Toast, ProgressBar, Header
│   └── api/axios.js    # Axios 인스턴스 — baseURL은 VITE_API_BASE_URL 사용
├── backend/
│   ├── main.py         # FastAPI 앱 초기화, CORS 설정, 라우터 등록
│   ├── routers/        # upload.py, expenses.py, summary.py
│   ├── services/
│   │   ├── ocr_service.py      # LangChain + ChatUpstage, 이미지→Base64, PDF→이미지 변환
│   │   └── storage_service.py  # expenses.json 읽기/쓰기/추가
│   └── data/expenses.json      # append 전용 JSON 배열 (UUID 키)
└── vercel.json         # @vercel/static-build (프론트) + @vercel/python (백엔드)
```

### API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/upload` | 영수증 파일 업로드 → OCR 파싱 → JSON 반환 |
| GET | `/api/expenses` | 지출 내역 조회, `?from=&to=` 날짜 필터 선택 |
| DELETE | `/api/expenses/{id}` | UUID로 항목 삭제 (없으면 404) |
| PUT | `/api/expenses/{id}` | UUID로 항목 부분 수정 |
| GET | `/api/summary` | 총합계 + 카테고리별 통계, `?month=YYYY-MM` 선택 |

### 데이터 스키마 (expenses.json 항목)

```json
{
  "id": "uuid-v4",
  "created_at": "ISO8601",
  "store_name": "string",
  "receipt_date": "YYYY-MM-DD",
  "receipt_time": "HH:MM or null",
  "category": "식료품|외식|교통|쇼핑|의료|기타",
  "items": [{ "name": "", "quantity": 0, "unit_price": 0, "total_price": 0 }],
  "subtotal": 0, "discount": 0, "tax": 0, "total_amount": 0,
  "payment_method": "string or null",
  "raw_image_path": "uploads/..."
}
```

## 주요 제약사항

- **DB 미사용** — 데이터는 `backend/data/expenses.json`에 배열로 누적 저장됩니다. Vercel 서버리스 환경에서는 컨테이너가 재시작되면 파일이 유실되므로 `/tmp/expenses.json`을 사용하고(`VERCEL=1` 감지 시 자동 전환), 프론트엔드에서 localStorage에 병행 저장합니다.
- **PDF 지원**은 `pdf2image` + Poppler가 필요합니다. Vercel에서는 사용 불가할 수 있으므로, 실패 시 명확한 오류 메시지와 함께 JPEG 업로드를 안내합니다.
- **파일 검증**은 서버 측에서 반드시 재검증합니다 (허용 MIME: `image/jpeg`, `image/png`, `application/pdf`; 최대 10MB).
- **OCR 시스템 프롬프트**는 LLM이 위 스키마에 맞는 JSON만 반환하도록 강제해야 합니다 — 다른 텍스트 포함 금지.

## 디자인 시스템

- **프레임워크**: TailwindCSS v3 (4px 기반 간격 시스템)
- **주요 색상**: `indigo-600` (`#4F46E5`) — CTA 버튼 및 포커스 링
- **폰트**: Pretendard → Noto Sans KR → 시스템 sans-serif
- **커스텀 애니메이션** (`slide-up`, `scale-in`, `fade-in`)은 `tailwind.config.js`에 keyframes로 등록
- **카테고리 뱃지 색상**: green=식료품, orange=외식, blue=교통, purple=쇼핑, red=의료, gray=기타
- 레이아웃 최대 너비: `max-w-4xl mx-auto`; 반응형 그리드: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`

## 바이브 코딩 3원칙

1. **완료 기준 먼저** — 각 Phase 구현 전, 완료 체크리스트(3~5개)를 먼저 명시합니다.
2. **조사 먼저, 구현 나중** — 새 라이브러리(`langchain-upstage`, `pdf2image`, Vercel Python 런타임)는 코드 작성 전에 반드시 `context7`으로 최신 문서를 확인합니다.
3. **버그: 원인 먼저, 수정 나중** — 버그 발생 시 코드 수정 전에 원인을 분석하고 수정 방향을 제안한 후 진행합니다.

### 예상 버그 유형별 체크리스트

| 버그 유형 | 확인할 것 |
|-----------|----------|
| OCR 500 에러 | LLM 응답이 JSON 형식인지 / 프롬프트가 JSON만 출력하도록 강제하는지 / `UPSTAGE_API_KEY` 설정 여부 |
| CORS 오류 | FastAPI `allow_origins` 설정 / Vercel 라우팅 경로 일치 여부 |
| PDF 변환 실패 | Poppler 설치 여부 / Vercel에서 `/tmp` 경로 사용 여부 |
| Vercel 데이터 손실 | `VERCEL=1` 환경변수 감지 여부 / localStorage 병행 저장 동작 여부 |
| 환경변수 미적용 | `VITE_` 접두사 확인 / Vercel 환경변수 등록 여부 / 변경 후 재배포 여부 |
