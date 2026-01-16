import json

db_filename = "sermon_database.json"

def load_database():
    try:
        with open(db_filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def search_sermons(keyword, db):
    # 결과를 담을 두 개의 바구니 준비
    title_matches = []   # 제목(주제)에 있는 경우
    content_matches = [] # 본문에만 있는 경우
    
    print(f"\n🔍 '{keyword}' 검색 중...\n")
    
    for sermon in db:
        # 1. 제목에 키워드가 있는지 확인
        if keyword in sermon['title']:
            title_matches.append(sermon)
        
        # 2. 본문에 키워드가 있는지 확인 (제목에 없을 때만 추가)
        elif keyword in sermon['content']:
            content_matches.append(sermon)
            
    return title_matches, content_matches

# --- 메인 실행 ---
sermon_db = load_database()

if sermon_db:
    while True:
        query = input("검색어 입력 (종료: q) >> ")
        if query == 'q':
            print("\n👋 프로그램을 종료합니다. 오늘도 평안한 하루 되세요!")
            break
        
        # 검색 실행
        titles, contents = search_sermons(query, sermon_db)
        
        # --- 결과 출력 (미니멀리즘 스타일) ---
        print("\n" + "="*40)
        
        # 1. 주제 설교 섹션 (강조)
        if titles:
            print(f"📖 [주제/제목 일치] - {len(titles)}건")
            for item in titles:
                print(f"  • {item['title']}")
        else:
             print("📖 [주제/제목 일치] - 없음")

        print("-" * 40)

        # 2. 본문 언급 섹션 (참고)
        if contents:
            print(f"📄 [본문 단순 언급] - {len(contents)}건")
            for item in contents:
                # 본문 내용을 다 보여주지 않고, 앞부분만 살짝 보여줌
                preview = item['content'][:60].replace('\n', ' ')
                print(f"  • {item['title']} (..{preview}..)")
        else:
            print("📄 [본문 단순 언급] - 없음")
            
        print("="*40 + "\n")