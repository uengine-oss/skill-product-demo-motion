# Render configuration

Python 3 + Pillow + FFmpeg/ffprobe가 필요하다. FFmpeg에는 `zoompan`, `perspective`, `rotate`, `xfade` 필터가 있어야 한다. 입력 파일은 로컬에서만 처리한다.

```sh
python3 /absolute/path/to/product-demo-motion/scripts/render.py \
  --config /absolute/path/to/reel.json \
  --output-dir /absolute/path/to/reel-output \
  --jobs 2
```

대표 장면만 확인하려면 `--scene 0`을 추가한다(0부터 시작). 전체 실행은 각 장면, 표지·끝 장면, `showcase.mp4`, `preview.jpg`를 만든다. 기존 출력에 덮어쓰므로 새 출력 폴더를 선택한다.

```json
{
  "product_name": "Process GPT Lite",
  "outro_title": "보안에서 업무까지",
  "scene_duration": 3.8,
  "crop_top_px": 180,
  "scenes": [
    {
      "file": "vault-demo.mp4",
      "start": 10,
      "title": "보안 로그인",
      "section": "PERSONAL VAULT",
      "keywords": ["인증 정보", "암호화 저장"],
      "motion": "orbit",
      "zoom": 1.10,
      "focus": [0.55, 0.36]
    },
    {
      "file": "panelapp-demo.mp4",
      "start": 43,
      "title": "스프레드시트 연동",
      "section": "PANEL APP",
      "keywords": ["패널 데이터", "시트 연동"],
      "motion": "sweep",
      "zoom": 1.12,
      "focus": [0.68, 0.45]
    }
  ]
}
```

- `file`: JSON 파일 폴더 기준 상대 경로 또는 절대 경로.파일 경로만 넣고 제목에 경로를 노출하지 않는다.
- `start`: 원본 영상의 시작 초. 장면 길이만큼 원본에 남아 있어야 한다.
- `scene_duration`: 전체 장면 공통 길이, 기본 3.8초, 지원 범위 2.5~8초. 표지·끝 장면은 각각 1.5초이며 전환마다 0.28초 겹친다. 전체 길이는 대략 `3 + 장면 수 × scene_duration - (장면 수+1) × 0.28`초다.
- `crop_top_px`: 입력을 비율 유지 1920×1080 캔버스에 맞춘 뒤 위에서 제거할 픽셀 수(0~300). 기본은 0. 예시의 180은 최초 원본에 들어 있던 설명 말풍선을 잘라내기 위한 값이며 다른 영상에 무조건 적용하지 않는다.
- `motion`: `orbit`, `push`, `pull`, `sweep`, `crane`, `reveal`.
- `zoom`: 1~2. UI 텍스트 가독성을 위해 보통 1.08~1.25를 출발점으로 한다.
- `focus`: `[가로, 세로]` 각각 0~1. 확대 시 유지할 관심 영역이다.
- `title`: 짧은 기능명. `keywords`는 짧은 명사 2개. 긴 설명 문장은 화면을 읽기 어렵게 하므로 분할한다.
- `font_ko`, `font_en`: 선택적 서체 파일 경로. 자동 탐색은 macOS 나눔명조·Baskerville 및 Linux Noto Serif CJK·나눔명조·DejaVu Serif를 지원한다. 폰트 파일은 스킬에 배포하지 않는다.

레이아웃은 가로 영상용이다. 세로 영상·긴 제목·다른 해상도 출력은 이 코드를 작업 폴더로 복사한 뒤 레이아웃을 조정하고 다시 검증한다. 필요시 실제 화면을 가리는 상단 크롭을 줄인다.

검증 예:

```sh
ffprobe -v error -show_streams -show_format -of json /absolute/path/to/reel-output/showcase.mp4
ffmpeg -v error -i /absolute/path/to/reel-output/showcase.mp4 -f null -
```

60fps 메타데이터만으로 시각적 부드러움이 증명되지는 않는다. 움직이는 가장자리와 자막이 한 프레임씩 멈추거나 떨리지 않는지도 확인한다.
