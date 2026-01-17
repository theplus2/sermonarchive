import sqlite3
import os
import re

db_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary", "library.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 창세기 2장 파일 찾기
c.execute("SELECT title, bible_tags FROM sermons WHERE bible_tags LIKE '%창세기%'")
rows = [dict(r) for r in c.fetchall()]

print(f"=== 창세기 태그 파일: {len(rows)}건 ===\n")

# 창세기 2장 관련 파일 찾기
print("=== '2장' 또는 '창2' 포함 파일 ===")
for row in rows:
    title = row['title']
    if '2장' in title or '창2' in title or '창세기 2' in title or '창세기2' in title:
        # 장 번호 추출 테스트
        chapter = 0
        match = re.search(r'창세기\s*(\d+)', title)
        if match:
            chapter = int(match.group(1))
        else:
            match = re.search(r'창(\d+)', title)
            if match:
                chapter = int(match.group(1))
        print(f"  장 {chapter:2d}: {title}")

print("\n=== 전체 파일 장 번호 추출 ===")
for row in rows:
    title = row['title']
    chapter = 0
    match = re.search(r'창세기\s*(\d+)', title)
    if match:
        chapter = int(match.group(1))
    else:
        match = re.search(r'창(\d+)', title)
        if match:
            chapter = int(match.group(1))
    print(f"  장 {chapter:2d}: {title[:60]}")

conn.close()
