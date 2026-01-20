import sqlite3
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
# 새롭게 분리된 모듈 임포트
try:
    from src.core import extractors
    from src.utils import helpers
except ImportError:
    # 실행 환경에 따라 상대 경로가 다를 수 있으므로 폴백 처리
    import extractors
    import helpers

def init_db(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()
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
    try:
        c.execute("ALTER TABLE sermons ADD COLUMN bible_chapter INTEGER DEFAULT 0")
    except:
        pass
    conn.commit()
    conn.close()

def _process_single_file(file_path):
    filename = os.path.basename(file_path)
    mtime = os.path.getmtime(file_path)
    
    content = ""
    if file_path.lower().endswith(".docx"):
        content = extractors.extract_text_from_docx(file_path)
    elif file_path.lower().endswith(".hwp"):
        content = extractors.extract_text_from_hwp(file_path)
    elif file_path.lower().endswith(".hwpx"):
        content = extractors.extract_text_from_hwpx(file_path)
    elif file_path.lower().endswith(".txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            pass
    
    sermon_date = helpers.parse_date_from_filename(filename)
    title = os.path.splitext(filename)[0]
    bible_tags, bible_chapter = helpers.extract_bible_tags(content, title)
    
    return (filename, title, sermon_date, content, bible_tags, bible_chapter, mtime)

def sync_files(target_folder, db_path, progress_callback=None, status_callback=None):
    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL;")

    files = glob.glob(os.path.join(target_folder, "**/*.*"), recursive=True)
    files = [f for f in files if f.lower().endswith(('.docx', '.hwp', '.hwpx', '.txt'))]
    
    current_filenames = set(os.path.basename(f) for f in files)
    
    c.execute("SELECT file_name, last_modified FROM sermons")
    db_cache = {row[0]: row[1] for row in c.fetchall()}
    db_filenames = set(db_cache.keys())
    
    deleted_files = db_filenames - current_filenames
    deleted_cnt = 0
    if deleted_files:
        for filename in deleted_files:
            c.execute("DELETE FROM sermons WHERE file_name=?", (filename,))
            deleted_cnt += 1
        conn.commit()
    
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
    
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_file = {executor.submit(_process_single_file, f): f for f in files_to_update}
        for i, future in enumerate(as_completed(future_to_file)):
            if progress_callback:
                progress_callback((total - update_total + i + 1) / total)
            try:
                result = future.result()
                results.append(result)
                if status_callback:
                    status_callback(f"처리 중: {result[0]}")
            except Exception:
                pass
    
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
        if updated_cnt % 50 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    
    msg = f"총 {total}개 파일 중 {updated_cnt}개 업데이트"
    if deleted_cnt > 0:
        msg += f", {deleted_cnt}개 삭제됨"
    return updated_cnt, msg

def get_stats(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sermons")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sermons WHERE bible_tags = ''")
    no_tag = c.fetchone()[0]
    c.execute("SELECT bible_tags FROM sermons")
    rows = c.fetchall()
    dict_rows = [{'bible_tags': r[0]} for r in rows]
    conn.close()
    return total, no_tag, dict_rows

def get_all_sermons_metadata(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT file_name, title, date, bible_tags, content FROM sermons ORDER BY date DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def search_sermons(db_path, query, bible_filter, sort_by_date=True):
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sql = "SELECT * FROM sermons WHERE 1=1"
    params = []
    if query:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if bible_filter:
        sub_conditions = []
        for b in bible_filter:
            sub_conditions.append("bible_tags LIKE ?")
            params.append(f"%{b}%")
        if sub_conditions:
            sql += " AND (" + " OR ".join(sub_conditions) + ")"
    if sort_by_date:
        sql += " ORDER BY date DESC"
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_wordcloud_text(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()
    c.execute("SELECT content FROM sermons")
    text = " ".join([r[0] for r in c.fetchall()])
    conn.close()
    return text
