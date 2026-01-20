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

VERSION = "v5.1.2"
print(f"🚀 빌드 준비 중... ({VERSION}) 기존 빌드 폴더를 정리합니다.")

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
current_dir = os.path.dirname(os.path.abspath(__file__))

# 아이콘 설정 (맥은 빌드 에러 방지를 위해 일단 제외하거나 .icns 확인이 필요함)
# 현재 맥 빌드에서 .icns 포맷 에러가 발생하므로, 윈도우만 아이콘을 적용합니다.
use_icon = False
icon_path = ""

if platform.system() == "Windows":
    icon_file = "icon.ico"
    icon_path = os.path.join(current_dir, icon_file)
    if os.path.exists(icon_path):
        use_icon = True
elif platform.system() == "Darwin":
    icon_file = "icon.icns"
    icon_path = os.path.join(current_dir, icon_file)
    if os.path.exists(icon_path):
       use_icon = True

required_files = ['run.py', 'app.py', 'tabs.py', 'styles.py', 'processor.py']
if use_icon:
    required_files.append(icon_file)

for f in required_files:
    if not os.path.exists(f):
        print(f"❌ 오류: '{f}' 파일이 없습니다! 폴더를 확인해주세요.")
        exit()

print(f"📦 PyInstaller 공장 가동! {VERSION} 버전으로 포장합니다...")

# 3. PyInstaller 실행 설정
sep = ';' if platform.system() == "Windows" else ':'

# 기본 옵션 리스트 생성
build_args = [
    'run.py',                       # 1. 실행 진입점
    f'--name=설교자의서재{VERSION}',  # 2. 파일 이름
    '--onefile',                    # 4. 파일 하나로
    '--clean',                      # 5. 캐시 초기화
    '--noconsole',                  # 6. 콘솔창 숨기기
    
    # 소스 코드 포함
    f'--add-data=app.py{sep}.',
    f'--add-data=tabs.py{sep}.',
    f'--add-data=styles.py{sep}.',
    f'--add-data=processor.py{sep}.',
    
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
    
    # 라이브러리 수집
    '--collect-all=streamlit',
    '--collect-all=altair',             
    '--collect-all=pandas',
    '--collect-all=wordcloud',
    '--collect-all=tkinter',            
    '--collect-all=matplotlib',
    '--collect-all=docx',
]

# 아이콘 옵션 추가 (사용 가능한 경우에만)
if use_icon:
    build_args.insert(2, f'--icon={icon_path}')

# 빌드 실행
PyInstaller.__main__.run(build_args)

print("\n" + "="*50)
print(f"✅ 빌드 성공! [dist] 폴더 안에 '설교자의서재{VERSION}' 파일을 확인하세요.")
print("="*50)