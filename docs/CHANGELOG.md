## [v5.3.3] - 2026-01-25

문서 개선: macOS 실행 가이드 직관화(우클릭 권장)\n배포: v5.3.3 릴리즈

## [v5.3.2] - 2026-01-25

macOS 실행 문제 해결: Ad-hoc 코드 서명 적용\n보안 권한 설정: entitlements.plist 추가\n배포 개선: DMG 패키징 자동화 및 ZIP 대체

## [v5.3.1] - 2026-01-25

빌드 에러 수정: PyMuPDF(fitz) 라이브러리 누락 해결\n임포트 경로 충돌 해결: 절대 경로 사용으로 통일\n안정성 강화: 진입점 경로 로직 보강

## [v5.2.8] - 2026-01-21

PDF 텍스트 추출 개선: 줄바꿈 자동 병합 기능 추가

## [v5.2.7] - 2026-01-21

macOS 아이콘 빌드 오류 수정\nCI/CD 워크플로우 개선

## [v5.2.6] - 2026-01-21

빌드 스크립트 경로 오류 수정\nmacOS 아이콘 경로 오류 수정

# Changelog

## [5.3.0] - 2026-01-21

### Added
- Switched PDF extraction engine to PyMuPDF (fitz) for significantly faster and more accurate text extraction.
- Implemented custom coordinate-based word sorting and gap-aware merging to fix punctuation and particle spacing issues in PDF files.

### Changed
- Updated application version to v5.3.0 across all components.
- Cleaned up experimental scripts and temporary test files.


## [v5.2.5] - 2026-01-21

PDF 파일 포맷 지원 추가\n자동화 릴리즈 스크립트 추가

