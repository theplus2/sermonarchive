import sqlite3
import os
import glob
from datetime import datetime
from docx import Document
import re

def init_db(db_path):
    # [수정 1] timeout=30 : DB가 잠겨있으면 30초까지 기다렸다가 재시도함 (기존 5초)
    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()
    
    # [수정 2] WAL 모드 적용 : 읽기와 쓰기를 동시에 할 수 있게 하여 'Locked' 오류를 획기적으로 줄임
    c.execute("PRAGMA journal_mode=WAL;")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT UNIQUE,
            title TEXT,
            date TEXT,
            content TEXT,
            bible_tags TEXT,
            bible_chapter INTEGER DEFAULT 0,
            last_modified FLOAT
        )
    ''')
    
    # 기존 DB에 bible_chapter 컬럼이 없으면 추가
    try:
        c.execute("ALTER TABLE sermons ADD COLUMN bible_chapter INTEGER DEFAULT 0")
    except:
        pass  # 이미 존재하면 무시
    
    conn.commit()
    conn.close()

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except: return ""

def extract_text_from_hwp(file_path):
    """
    HWP 파일에서 텍스트를 추출합니다.
    
    우선순위:
    1. hwp5 라이브러리 main() 직접 호출 (In-Process) - 가장 안정적
    2. olefile - PrvText 섹션 (fallback)
    
    Returns:
        str: 추출된 텍스트 (실패시 빈 문자열)
    """
    import tempfile
    import sys
    import os
    
    # 1차 시도: hwp5txt 메인 함수 직접 호출
    # subprocess를 쓰지 않고 파이썬 내부에서 실행하므로 가장 확실함
    try:
        from hwp5.hwp5txt import main as hwp5txt_main
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name
            
        saved_argv = sys.argv
        try:
            # argv를 조작하여 hwp5txt가 마치 커맨드라인에서 실행된 것처럼 속임
            sys.argv = ['hwp5txt', '--output', tmp_path, file_path]
            
            # 메인 함수 실행 (여기서 파일에 씀)
            hwp5txt_main()
            
            # 결과 읽기
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read().strip()
                if text:
                    return text
                    
        except Exception as e:
            # print(f"hwp5txt main failed: {e}")
            pass
            
        finally:
            sys.argv = saved_argv
            if os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except: pass
                
    except ImportError:
        pass
    except Exception:
        pass

    # 2차 시도 (fallback): olefile로 PrvText 섹션 추출
    try:
        import olefile
        with olefile.OleFileIO(file_path) as ole:
            if ole.exists("PrvText"):
                encoded_text = ole.openstream("PrvText").read()
                return encoded_text.decode('utf-16-le', errors='ignore').strip()
    except Exception:
        pass
    
    return ""
 

def parse_date_from_filename(filename):
    """
    파일명에서 날짜를 추출합니다.
    
    지원 패턴:
    - 250115 (YYMMDD)
    - 20250115 (YYYYMMDD)
    - 2025-01-15 (YYYY-MM-DD)
    - 25-01-15 (YY-MM-DD)
    - 25.01.15 (YY.MM.DD)
    - 2025.01.15 (YYYY.MM.DD)
    - 2025 0115 (YYYY MMDD) - 연도와 월일 사이 공백
    - p250115 (pYYMMDD) - 알파벳 접두사 + 6자리
    - B)250115 등 - 특수문자 접두사 + 6자리
    """
    patterns = [
        # 구분자 있는 패턴 (우선순위 높음)
        (r"(\d{4})[-./](\d{2})[-./](\d{2})", lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),  # 2025-01-15, 2025.01.15, 2025/01/15
        (r"(\d{2})[-./](\d{2})[-./](\d{2})", lambda m: f"20{m.group(1)}-{m.group(2)}-{m.group(3)}"),  # 25-01-15, 25.01.15
        
        # YYYY MMDD (연도 공백 월일)
        (r"(\d{4})\s+(\d{4})", lambda m: f"{m.group(1)}-{m.group(2)[:2]}-{m.group(2)[2:]}"),  # 2025 0115
        
        # 알파벳/특수문자 접두사 + 6자리 (pYYMMDD, B)YYMMDD 등)
        (r"[a-zA-Z)]+(\d{6})", lambda m: f"20{m.group(1)[:2]}-{m.group(1)[2:4]}-{m.group(1)[4:]}"),  # p250115, B)250115
        
        # 8자리 붙여쓰기
        (r"(\d{8})", lambda m: f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}"),  # 20250115
        
        # 6자리 붙여쓰기 (가장 마지막 - 다른 패턴에 안 걸릴 때)
        (r"(\d{6})", lambda m: f"20{m.group(1)[:2]}-{m.group(1)[2:4]}-{m.group(1)[4:]}"),  # 250115
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                result = converter(match)
                # 유효성 검사 (월 1-12, 일 1-31)
                parts = result.split('-')
                if len(parts) == 3:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    if 1 <= m <= 12 and 1 <= d <= 31 and 1990 <= y <= 2099:
                        return result
            except:
                continue
    return ""

def extract_bible_tags(text, title):
    """
    제목과 본문 초반에서 성경 본문 태그를 추출합니다.
    
    규칙:
    - 파일명(제목) + 본문 초반 150자만 검색
    - 성경이름 + 숫자(장) 패턴이 있어야 태깅 (예: 창14, 창세기 14장)
    - 단순히 성경 이름만 있으면 태깅하지 않음
    - 한 글자 축약형은 단어 경계에서만 인식 (오탐지 방지)
    
    Returns:
        tuple: (태그 문자열, 첫 번째 성경의 장 번호)
    """
    # 축약형 → 정식명 매핑
    short_to_full = {
        # 2글자 이상 축약형 (오탐지 위험 낮음)
        "창세기": "창세기", "출애굽기": "출애굽기", "레위기": "레위기", "민수기": "민수기", "신명기": "신명기",
        "삼상": "사무엘상", "삼하": "사무엘하", "왕상": "열왕기상", "왕하": "열왕기하",
        "대상": "역대상", "대하": "역대하", "고전": "고린도전서", "고후": "고린도후서",
        "살전": "데살로니가전서", "살후": "데살로니가후서", "딤전": "디모데전서", "딤후": "디모데후서",
        "벧전": "베드로전서", "벧후": "베드로후서", "요일": "요한1서", "요이": "요한2서", "요삼": "요한3서",
    }
    
    # 한 글자 축약형 (오탐지 위험 높음 - 특별 처리 필요)
    single_char_short = {
        "창": "창세기", "출": "출애굽기", "레": "레위기", "민": "민수기", "신": "신명기",
        "수": "여호수아", "삿": "사사기", "룻": "룻기",
        "스": "에스라", "느": "느헤미야", "에": "에스더", "욥": "욥기", "시": "시편",
        "잠": "잠언", "전": "전도서", "아": "아가", "사": "이사야", "렘": "예레미야",
        "애": "예레미야애가", "겔": "에스겔", "단": "다니엘", "호": "호세아", "욜": "요엘",
        "암": "아모스", "옵": "오바댜", "욘": "요나", "미": "미가", "나": "나훔",
        "합": "하박국", "습": "스바냐", "학": "학개", "슥": "스가랴", "말": "말라기",
        "마": "마태복음", "막": "마가복음", "눅": "누가복음", "요": "요한복음",
        "행": "사도행전", "롬": "로마서", "갈": "갈라디아서", "엡": "에베소서",
        "빌": "빌립보서", "골": "골로새서", "딛": "디도서", "몬": "빌레몬서",
        "히": "히브리서", "야": "야고보서", "유": "유다서", "계": "요한계시록",
    }
    
    # 정식명 목록
    full_names = ["창세기","출애굽기","레위기","민수기","신명기","여호수아","사사기","룻기",
                  "사무엘상","사무엘하","열왕기상","열왕기하","역대상","역대하","에스라","느헤미야",
                  "에스더","욥기","시편","잠언","전도서","아가","이사야","예레미야","예레미야애가",
                  "에스겔","다니엘","호세아","요엘","아모스","오바댜","요나","미가","나훔","하박국",
                  "스바냐","학개","스가랴","말라기","마태복음","마가복음","누가복음","요한복음",
                  "사도행전","로마서","고린도전서","고린도후서","갈라디아서","에베소서","빌립보서",
                  "골로새서","데살로니가전서","데살로니가후서","디모데전서","디모데후서","디도서",
                  "빌레몬서","히브리서","야고보서","베드로전서","베드로후서","요한1서","요한2서",
                  "요한3서","유다서","요한계시록"]
    
    # 제목 + 본문 초반 150자 (범위 축소)
    combined = title + " " + text[:150]
    
    found = []  # (성경이름, 장번호) 튜플 목록
    first_chapter = 0  # 첫 번째 성경의 장 번호
    
    # 1. 정식명 + 숫자 패턴 검색 (우선순위 높음)
    for full in full_names:
        pattern = rf"{re.escape(full)}\s*(\d+)"
        match = re.search(pattern, combined)
        if match:
            chapter = int(match.group(1))
            found.append((full, chapter))
    
    # 2. 2글자 이상 축약형 + 숫자 패턴 검색
    for short, full in short_to_full.items():
        if full in [f[0] for f in found]:  # 이미 찾은 것은 스킵
            continue
        pattern = rf"{re.escape(short)}\s*(\d+)"
        match = re.search(pattern, combined)
        if match:
            chapter = int(match.group(1))
            found.append((full, chapter))
    
    # 3. 한 글자 축약형 검색 (단어 경계 필수)
    for short, full in single_char_short.items():
        if full in [f[0] for f in found]:  # 이미 찾은 것은 스킵
            continue
        pattern = rf"(?:^|[\s:;,.()\[\]「」『』]){re.escape(short)}\s*(\d+)"
        match = re.search(pattern, combined)
        if match:
            chapter = int(match.group(1))
            found.append((full, chapter))
    
    # 첫 번째 성경의 장 번호 추출
    if found:
        first_chapter = found[0][1]
    
    tags = ",".join(sorted(set(f[0] for f in found)))
    return tags, first_chapter

def _process_single_file(file_path):
    """
    단일 파일 처리 (병렬 실행용 헬퍼 함수)
    텍스트 추출 및 메타데이터 파싱만 수행 (DB 작업 제외)
    """
    filename = os.path.basename(file_path)
    mtime = os.path.getmtime(file_path)
    
    content = ""
    if file_path.lower().endswith(".docx"):
        content = extract_text_from_docx(file_path)
    elif file_path.lower().endswith(".hwp"):
        content = extract_text_from_hwp(file_path)
    elif file_path.lower().endswith(".txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            pass
    
    sermon_date = parse_date_from_filename(filename)
    title = os.path.splitext(filename)[0]
    bible_tags, bible_chapter = extract_bible_tags(content, title)
    
    return (filename, title, sermon_date, content, bible_tags, bible_chapter, mtime)


def sync_files(target_folder, progress_callback=None, status_callback=None):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # DB 연결 (타임아웃 30초)
    db_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary", "library.db")
    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL;")  # WAL 모드 활성화

    files = glob.glob(os.path.join(target_folder, "**/*.*"), recursive=True)
    files = [f for f in files if f.lower().endswith(('.docx', '.hwp', '.txt'))]
    
    # 현재 폴더에 있는 파일명 목록
    current_filenames = set(os.path.basename(f) for f in files)
    
    # [최적화 1] DB 정보 일괄 로드 (파일명 → mtime 캐시)
    c.execute("SELECT file_name, last_modified FROM sermons")
    db_cache = {row[0]: row[1] for row in c.fetchall()}
    db_filenames = set(db_cache.keys())
    
    # DB에 있지만 폴더에 없는 파일 삭제
    deleted_files = db_filenames - current_filenames
    deleted_cnt = 0
    if deleted_files:
        for filename in deleted_files:
            c.execute("DELETE FROM sermons WHERE file_name=?", (filename,))
            deleted_cnt += 1
        conn.commit()
    
    # 변경된 파일만 필터링 (캐시 활용)
    files_to_update = []
    for file_path in files:
        filename = os.path.basename(file_path)
        mtime = os.path.getmtime(file_path)
        cached_mtime = db_cache.get(filename)
        if cached_mtime != mtime:
            files_to_update.append(file_path)
    
    total = len(files)
    update_total = len(files_to_update)
    updated_cnt = 0
    
    if update_total == 0:
        conn.close()
        msg = f"총 {total}개 파일 중 {updated_cnt}개 업데이트"
        if deleted_cnt > 0:
            msg += f", {deleted_cnt}개 삭제됨"
        return updated_cnt, msg
    
    # [최적화 2] ThreadPoolExecutor로 병렬 처리 (워커 4개)
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_file = {executor.submit(_process_single_file, f): f for f in files_to_update}
        
        for i, future in enumerate(as_completed(future_to_file)):
            file_path = future_to_file[future]
            filename = os.path.basename(file_path)
            
            # 진행률 콜백 (전체 파일 대비)
            if progress_callback:
                progress_callback((total - update_total + i + 1) / total)
            
            if status_callback:
                status_callback(f"처리 중: {filename}")
            
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # 개별 파일 오류는 무시하고 계속 진행
                pass
    
    # DB INSERT는 메인 스레드에서 순차 처리 (SQLite 안전성)
    for result in results:
        filename, title, sermon_date, content, bible_tags, bible_chapter, mtime = result
        c.execute('''
            INSERT INTO sermons (file_name, title, date, content, bible_tags, bible_chapter, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_name) DO UPDATE SET
                title=excluded.title,
                date=excluded.date,
                content=excluded.content,
                bible_tags=excluded.bible_tags,
                bible_chapter=excluded.bible_chapter,
                last_modified=excluded.last_modified
        ''', (filename, title, sermon_date, content, bible_tags, bible_chapter, mtime))
        
        updated_cnt += 1
        
        # 50개마다 커밋 (DB 잠금 최소화)
        if updated_cnt % 50 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    
    # 결과 메시지 생성
    msg = f"총 {total}개 파일 중 {updated_cnt}개 업데이트"
    if deleted_cnt > 0:
        msg += f", {deleted_cnt}개 삭제됨"
    return updated_cnt, msg

def get_stats():
    conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary", "library.db"), timeout=30)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM sermons")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM sermons WHERE bible_tags = ''")
    no_tag = c.fetchone()[0]
    
    c.execute("SELECT bible_tags FROM sermons")
    rows = c.fetchall() # [{'bible_tags': '...'}] 형태가 아님. 튜플임.
    
    # 딕셔너리 형태로 변환해서 리턴
    dict_rows = [{'bible_tags': r[0]} for r in rows]
    
    conn.close()
    return total, no_tag, dict_rows

def get_all_sermons_metadata():
    conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary", "library.db"), timeout=30)
    conn.row_factory = sqlite3.Row # 컬럼명으로 접근 가능하게 설정
    c = conn.cursor()
    c.execute("SELECT file_name, title, date, bible_tags, content FROM sermons ORDER BY date DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def search_sermons(query, bible_filter, sort_by_date=True):
    """
    설교 검색 함수
    
    Args:
        query: 검색어
        bible_filter: 성경 필터 목록
        sort_by_date: True면 날짜 내림차순 정렬, False면 정렬 안함 (Python에서 별도 정렬 예정)
    """
    conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary", "library.db"), timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    sql = "SELECT * FROM sermons WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
        
    if bible_filter:
        # 성경 필터 (OR 조건) - 간단 구현
        # 실제로는 태그가 '창세기,출애굽기' 처럼 되어 있으므로 LIKE 검색 필요
        sub_conditions = []
        for b in bible_filter:
            sub_conditions.append("bible_tags LIKE ?")
            params.append(f"%{b}%")
        
        if sub_conditions:
            sql += " AND (" + " OR ".join(sub_conditions) + ")"
    
    # 날짜순 정렬 옵션
    if sort_by_date:
        sql += " ORDER BY date DESC"
    
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_wordcloud_text():
    conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary", "library.db"), timeout=30)
    c = conn.cursor()
    c.execute("SELECT content FROM sermons")
    text = " ".join([r[0] for r in c.fetchall()])
    conn.close()
    return text