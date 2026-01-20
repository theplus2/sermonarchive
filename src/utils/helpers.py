import re

def parse_date_from_filename(filename):
    """
    파일명에서 날짜를 추출합니다.
    """
    patterns = [
        (r"(\d{4})[-./](\d{2})[-./](\d{2})", lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
        (r"(\d{2})[-./](\d{2})[-./](\d{2})", lambda m: f"20{m.group(1)}-{m.group(2)}-{m.group(3)}"),
        (r"(\d{4})\s+(\d{4})", lambda m: f"{m.group(1)}-{m.group(2)[:2]}-{m.group(2)[2:]}"),
        (r"[a-zA-Z)]+(\d{6})", lambda m: f"20{m.group(1)[:2]}-{m.group(1)[2:4]}-{m.group(1)[4:]}"),
        (r"(\d{8})", lambda m: f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}"),
        (r"(\d{6})", lambda m: f"20{m.group(1)[:2]}-{m.group(1)[2:4]}-{m.group(1)[4:]}"),
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                result = converter(match)
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
    """
    short_to_full = {
        "창세기": "창세기", "출애굽기": "출애굽기", "레위기": "레위기", "민수기": "민수기", "신명기": "신명기",
        "삼상": "사무엘상", "삼하": "사무엘하", "왕상": "열왕기상", "왕하": "열왕기하",
        "대상": "역대상", "대하": "역대하", "고전": "고린도전서", "고후": "고린도후서",
        "살전": "데살로니가전서", "살후": "데살로니가후서", "딤전": "디모데전서", "딤후": "디모데후서",
        "벧전": "베드로전서", "벧후": "베드로후서", "요일": "요한1서", "요이": "요한2서", "요삼": "요한3서",
    }
    
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
    
    full_names = ["창세기","출애굽기","레위기","민수기","신명기","여호수아","사사기","룻기",
                  "사무엘상","사무엘하","열왕기상","열왕기하","역대상","역대하","에스라","느헤미야",
                  "에스더","욥기","시편","잠언","전도서","아가","이사야","예레미야","예레미야애가",
                  "에스겔","다니엘","호세아","요엘","아모스","오바댜","요나","미가","나훔","하박국",
                  "스바냐","학개","스가랴","말라기","마태복음","마가복음","누가복음","요한복음",
                  "사도행전","로마서","고린도전서","고린도후서","갈라디아서","에베소서","빌립보서",
                  "골로새서","데살로니가전서","데살로니가후서","디모데전서","디모데후서","디도서",
                  "빌레몬서","히브리서","야고보서","베드로전서","베드로후서","요한1서","요한2서",
                  "요한3서","유다서","요한계시록"]
    
    combined = title + " " + text[:150]
    found = []
    first_chapter = 0
    
    for full in full_names:
        pattern = rf"{re.escape(full)}\s*(\d+)"
        match = re.search(pattern, combined)
        if match:
            chapter = int(match.group(1))
            found.append((full, chapter))
    
    for short, full in short_to_full.items():
        if full in [f[0] for f in found]:
            continue
        pattern = rf"{re.escape(short)}\s*(\d+)"
        match = re.search(pattern, combined)
        if match:
            chapter = int(match.group(1))
            found.append((full, chapter))
    
    for short, full in single_char_short.items():
        if full in [f[0] for f in found]:
            continue
        pattern = rf"(?:^|[\s:;,.()\[\]「」『』]){re.escape(short)}\s*(\d+)"
        match = re.search(pattern, combined)
        if match:
            chapter = int(match.group(1))
            found.append((full, chapter))
    
    if found:
        first_chapter = found[0][1]
    
    tags = ",".join(sorted(set(f[0] for f in found)))
    return tags, first_chapter
