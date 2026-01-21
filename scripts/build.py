import PyInstaller.__main__
import os
import shutil
import platform
import sys

# [중요] Windows GitHub Actions 등에서 한글 출력 시 인코딩 에러 방지
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

VERSION = "v5.2.5"
print(f"🚀 빌드 준비 중... ({VERSION}) 기존 빌드 폴더를 정리합니다.")

# 프로젝트 루트 디렉토리 설정 (scripts 폴더 상위)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
print(f"📂 작업 경로: {PROJECT_ROOT}")

# 1. 기존 빌드 잔여물 깨끗이 삭제
if os.path.exists("dist"):
    try: shutil.rmtree("dist")
    except: pass
if os.path.exists("build"):
    try: shutil.rmtree("build")
    except: pass
# 혹시 남아있을 수 있는 이전 버전 spec 파일들 삭제
for f in os.listdir('.'):
    if f.endswith(".spec"):
        try: os.remove(f)
        except: pass

# 2. 필수 파일 확인
assets_dir = os.path.join(PROJECT_ROOT, "assets")
scripts_dir = os.path.join(PROJECT_ROOT, "scripts")

# 아이콘 설정
use_icon = False
icon_path = ""

if platform.system() == "Windows":
    icon_file = "icon.ico"
    icon_path = os.path.join(assets_dir, icon_file)
    if os.path.exists(icon_path):
        use_icon = True
elif platform.system() == "Darwin":
    icon_file = "icon.icns"
    icon_path = os.path.join(assets_dir, icon_file)
    if os.path.exists(icon_path):
       use_icon = True

# 진입점 파일 확인
run_script = os.path.join(scripts_dir, "run.py")
if not os.path.exists(run_script):
    print(f"❌ 오류: 진입점 파일 '{run_script}'이 없습니다!")
    exit(1)

print(f"📦 PyInstaller 공장 가동! {VERSION} 버전으로 포장합니다...")

# 3. PyInstaller 실행 설정
sep = ';' if platform.system() == "Windows" else ':'

# 기본 옵션 리스트 생성
build_args = [
    run_script,                     # 1. 실행 진입점 (scripts/run.py)
    f'--name=SermonArchive_{VERSION}',  # 2. 파일 이름
    '--onefile',                    # 4. 파일 하나로
    '--clean',                      # 5. 캐시 초기화
    '--noconsole',                  # 6. 콘솔창 숨기기
    
    # 소스 코드 포함 (src 폴더 통째로 추가)
    f'--add-data=src{sep}src',
    f'--add-data=app.py{sep}.',
    f'--add-data=config.json{sep}.', # config.json도 필요하다면
    
    # 숨겨진 라이브러리 명시
    '--hidden-import=streamlit',
    '--hidden-import=pandas',
    '--hidden-import=sqlite3',
    '--hidden-import=docx',             
    '--hidden-import=wordcloud',        
    '--hidden-import=matplotlib',       
    '--hidden-import=tkinter',          
    '--hidden-import=tkinter.filedialog',
    '--hidden-import=PIL',
    '--hidden-import=hwp5',             
    '--hidden-import=olefile',
    '--hidden-import=pdfminer',
    '--hidden-import=pdfminer.high_level',
    '--hidden-import=pdfminer.layout',
    
    # 라이브러리 수집
    '--collect-all=streamlit',
    '--collect-all=altair',             
    '--collect-all=pandas',
    '--collect-all=wordcloud',
    '--collect-all=tkinter',            
    '--collect-all=matplotlib',
    '--collect-all=docx',
    '--collect-all=pdfminer',
]

# 아이콘 옵션 추가
if use_icon:
    build_args.insert(2, f'--icon={icon_path}')
else:
    print("⚠️ 경고: 아이콘 파일을 찾을 수 없어 기본 아이콘을 사용합니다.")

# 빌드 실행
PyInstaller.__main__.run(build_args)

print("\n" + "="*50)
print(f"✅ 빌드 성공! [dist] 폴더 안에 'SermonArchive_{VERSION}' 파일을 확인하세요.")
print("="*50)