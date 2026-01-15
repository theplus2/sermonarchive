import sqlite3
import os
import re

# DB 연결
db_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary", "library.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 창세기 태그가 있는 설교 검색
c.execute("SELECT title, bible_tags FROM sermons WHERE bible_tags LIKE '%창세기%' ORDER BY date DESC")
rows = [dict(r) for r in c.fetchall()]

BIBLE_ORDER = ["창세기","출애굽기","레위기","민수기","신명기","여호수아","사사기","룻기","사무엘상","사무엘하","열왕기상","열왕기하","역대상","역대하","에스라","느헤미야","에스더","욥기","시편","잠언","전도서","아가","이사야","예레미야","예레미야애가","에스겔","다니엘","호세아","요엘","아모스","오바댜","요나","미가","나훔","하박국","스바냐","학개","스가랴","말라기","마태복음","마가복음","누가복음","요한복음","사도행전","로마서","고린도전서","고린도후서","갈라디아서","에베소서","빌립보서","골로새서","데살로니가전서","데살로니가후서","디모데전서","디모데후서","디도서","빌레몬서","히브리서","야고보서","베드로전서","베드로후서","요한1서","요한2서","요한3서","유다서","요한계시록"]

def get_bible_sort_key(row):
    tags = row.get('bible_tags', '')
    title = row.get('title', '')
    
    if not tags:
        return (len(BIBLE_ORDER), 0)
    
    first_tag = tags.split(',')[0].strip()
    
    for i, book in enumerate(BIBLE_ORDER):
        if first_tag == book:
            chapter = 0
            
            # 정식명 + 숫자 패턴
            match = re.search(rf'{re.escape(book)}\s*(\d+)', title)
            if match:
                chapter = int(match.group(1))
            else:
                # 축약형 + 숫자 패턴
                short_names = ["창","출","레","민","신","수","삿","룻","삼상","삼하","왕상","왕하","대상","대하","스","느","에","욥","시","잠","전","아","사","렘","애","겔","단","호","욜","암","옵","욘","미","나","합","습","학","슥","말","마","막","눅","요","행","롬","고전","고후","갈","엡","빌","골","살전","살후","딤전","딤후","딛","몬","히","야","벧전","벧후","요일","요이","요삼","유","계"]
                for short in short_names:
                    match = re.search(rf'(?:^|[\s(]){re.escape(short)}\s*(\d+)', title)
                    if match:
                        chapter = int(match.group(1))
                        break
            
            return (i, chapter)
    
    return (len(BIBLE_ORDER), 0)

print(f"=== 창세기 검색 결과: {len(rows)}건 ===\n")

# 새 정렬 키 함수
def get_sort_key_new(row):
    title = row['title']
    chapter = 0
    
    # 1. 정식명 + 숫자 패턴
    match = re.search(r'창세기\s*(\d+)', title)
    if match:
        chapter = int(match.group(1))
    # 2. 축약형 + 숫자 패턴 (더 단순화)
    else:
        match = re.search(r'창(\d+)', title)
        if match:
            chapter = int(match.group(1))
    return chapter

print("=== 장 번호 추출 테스트 ===")
for row in rows:
    title = row['title']
    chapter = get_sort_key_new(row)
    if chapter > 0:
        print(f"  장 {chapter:2d}: {title[:50]}")
    else:
        print(f"  장 없음: {title[:50]}")

print("\n=== 장 번호순 정렬 후 ===")
sorted_rows = sorted(rows, key=get_sort_key_new)
for i, row in enumerate(sorted_rows):
    chapter = get_sort_key_new(row)
    print(f"{i+1}. 장 {chapter:2d}: {row['title'][:50]}")

conn.close()
