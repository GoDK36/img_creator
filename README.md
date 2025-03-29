# AI 이미지 생성기

OpenAI DALL-E 3 또는 Claude를 사용하여 이미지를 생성하는 Streamlit 애플리케이션입니다.

## 기능

- OpenAI DALL-E 3 또는 Claude API 선택 가능
- 1536x1024 크기의 이미지 생성
- JPG 형식으로 이미지 다운로드
- 프롬프트 기반 이미지 생성
- 토큰 사용량 표시

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
`.env` 파일을 생성하고 다음 내용을 추가하세요:
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## 실행 방법

다음 명령어로 애플리케이션을 실행합니다:
```bash
streamlit run app.py
```

## 사용 방법

1. 웹 브라우저에서 Streamlit 인터페이스가 열립니다.
2. 사용할 API를 선택합니다 (OpenAI DALL-E 3 또는 Claude).
3. 이미지 생성을 위한 프롬프트를 입력합니다.
4. "이미지 생성" 버튼을 클릭합니다.
5. 생성된 이미지를 확인하고 필요한 경우 다운로드합니다.

## 주의사항

- API 키는 반드시 안전하게 보관하세요.
- Claude API의 이미지 생성 기능은 현재 개발 중입니다. 