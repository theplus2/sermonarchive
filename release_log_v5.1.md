# 설교자의 서재 v5.1 작업 일지

**날짜**: 2026-01-20
**버전**: v5.1
**작업자**: Antigravity (with User)

## 1. 개요
이번 v5.1 업데이트의 핵심 목표는 기존 HWP, DOCX 파일뿐만 아니라 **HWPX (한글 개방형 문서 포맷)** 파일을 지원하여 검색 및 본문 텍스트 추출이 가능하게 하는 것입니다.

## 2. 주요 변경 사항

### 2.1 HWPX 파일 포맷 지원 기능 추가
- **구현 방식**: 외부 라이브러리 없이 파이썬 표준 라이브러리인 `zipfile`과 `xml.etree.ElementTree`만을 사용하여 구현했습니다.
- **핵심 파일 수정**: `processor.py`

### 2.2 버전 업데이트
- `app.py`, `tabs.py`, `build.py` 전체 동기화

## 3. 검증 (Verification)
- `test_hwpx.py` 스크립트로 HWPX 텍스트 추출 검증
- Streamlit 앱 통합 테스트 완료

## 4. 배포 (Deployment)
- GitHub Main 브랜치 푸시 완료

---

### v5.1.2 ~ v5.1.8 업데이트 (2026-01-20)
- **macOS DMG 지원 시도**: create-dmg, hdiutil, codesign 등 다양한 방법으로 DMG 생성 시도
- **문제점**: GitHub Actions Runner에서 `codesign` 명령어 실행 시 `Bus error: 10` 발생
- **원인 추정**: Runner 환경의 한글 파일명 처리 또는 서명 관련 시스템 제한

---

### v5.1.9 업데이트 (2026-01-20) - **macOS ZIP 배포 전환**

**결론**: DMG 생성이 지속적으로 실패하여 **ZIP 배포 방식으로 전환**했습니다.

**변경 사항**:
- `release.yml`: DMG 생성 로직 제거, ZIP 압축으로 대체
- codesign 단계 제거 (Bus error 원인)
- 릴리즈 자산: `sermon_archive_v5.1.9.exe` (Windows), `sermon_archive_v5.1.9_mac.zip` (macOS)

**macOS 사용자 설치 방법**:
1. `sermon_archive_vX.X.X_mac.zip` 다운로드
2. 더블클릭으로 압축 해제 (자동)
3. `.app` 파일을 Applications(응용 프로그램) 폴더로 드래그
4. 처음 실행 시: **마우스 우클릭 > [열기]** 클릭 (Gatekeeper 우회)
5. 그래도 안 되면 터미널에서: `sudo xattr -cr /Applications/앱이름.app`
