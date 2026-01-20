# 설교자의 서재 v5.1~v5.2 작업 일지

**날짜**: 2026-01-20
**작업자**: Antigravity (with User)

## v5.1 개요
HWPX 파일 포맷 지원 추가

---

## v5.1.2 ~ v5.1.9 (2026-01-20)
macOS DMG/ZIP 배포 시도 및 다양한 빌드 오류 해결 시도:
- create-dmg, hdiutil, codesign 등 시도
- Bus error: 10 발생 (codesign 한글 파일명 문제)
- 최종적으로 ZIP 배포로 전환

---

## v5.2.0 (2026-01-20) - **macOS 호환성 해결**

**핵심 변경**: 앱 파일명을 **한글에서 영문으로 변경**

**원인 분석**:
1. macOS의 `codesign` 도구가 한글 파일명을 처리할 때 Bus error 발생
2. 터미널에서 한글 경로 입력 시 사용자 실수 유발 (공백, 인코딩 문제)
3. 격리 속성 제거 명령어(`xattr -cr`) 실행 어려움

**변경 사항**:
- `build.py`: `--name=설교자의서재{VERSION}` → `--name=SermonArchive_{VERSION}`
- 릴리즈 파일명: `SermonArchive_v5.2.0.exe`, `sermon_archive_v5.2.0_mac.zip`
- ZIP 내부: `SermonArchive_v5.2.0.app`

**macOS 사용자 설치 방법**:
1. `sermon_archive_v5.2.0_mac.zip` 다운로드
2. 더블클릭으로 압축 해제
3. `SermonArchive_v5.2.0.app`을 Applications 폴더로 드래그
4. 처음 실행 시: **마우스 우클릭 > [열기]**
5. 그래도 안 되면:
   ```bash
   sudo xattr -cr /Applications/SermonArchive_v5.2.0.app
   ```
