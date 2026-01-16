import PyInstaller.__main__
import os
import shutil

print("🚀 빌드 준비 중... 기존 빌드 폴더를 정리합니다.")

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

# 2. 필수 파일 및 아이콘 경로 확인
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "icon.ico")

required_files = ['run.py', 'app.py', 'tabs.py', 'styles.py', 'processor.py', 'icon.ico']
for f in required_files:
    if not os.path.exists(f):
        print(f"❌ 오류: '{f}' 파일이 없습니다! 폴더를 확인해주세요.")
        exit()

print("📦 PyInstaller 공장 가동! v4.9.5 버전으로 포장합니다...")

# 3. PyInstaller 실행 설정
PyInstaller.__main__.run([
    'run.py',                       # 1. 실행 진입점
    '--name=설교자의서재v4.9.5',        # 2. [수정] 파일 이름 v4.9.5로 변경!
    f'--icon={icon_path}',          # 3. 아이콘 (절대경로)
    '--onefile',                    # 4. 파일 하나로
    '--clean',                      # 5. 캐시 초기화
    '--noconsole',                  # 6. 콘솔창 숨기기
    
    # 소스 코드 포함
    '--add-data=app.py;.',
    '--add-data=tabs.py;.',
    '--add-data=styles.py;.',
    '--add-data=processor.py;.',
    
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
    '--hidden-import=hwp5',             # HWP 텍스트 추출용 (pyhwp)
    '--hidden-import=olefile',          # HWP fallback 추출용
    
    # 라이브러리 통째로 수집
    '--collect-all=streamlit',
    '--collect-all=altair',             
    '--collect-all=pandas',
    '--collect-all=wordcloud',
    '--collect-all=tkinter',            
    '--collect-all=matplotlib',
    '--collect-all=docx',
    '--collect-all=hwp5',               # HWP 텍스트 추출용 (pyhwp)
    '--collect-all=olefile',            # HWP fallback 추출용
])

print("\n" + "="*50)
print("✅ 빌드 성공! [dist] 폴더 안에 '설교자의서재v4.9.5.exe' 파일을 확인하세요.")
print("="*50)