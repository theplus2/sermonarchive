import os
# Lazy imports applied to: zipfile, xml, docx, fitz

def extract_text_from_pdf(file_path):
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        full_text = []
        
        for page in doc:
            # 단어 단위로 좌표와 함께 추출: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
            words = page.get_text("words")
            
            # Y 좌표를 기준으로 행(Line) 그룹화
            # y0가 비슷한 것끼리 묶음 (오차 범위 3~5픽셀)
            lines = {}  # key: representative_y, value: list of words
            
            for w in words:
                y0 = w[1]
                # 기존 라인 중 y0 차이가 5 이하인 것이 있는지 확인
                found_line = False
                for line_y in lines:
                    if abs(line_y - y0) < 5:
                        lines[line_y].append(w)
                        found_line = True
                        break
                
                if not found_line:
                    lines[y0] = [w]
            
            # Y 좌표 순으로 라인 정렬 (위에서 아래로)
            # sorted_lines = sorted(lines.items(), key=lambda item: item[0])
            sorted_y = sorted(lines.keys())
            
            page_text = ""
            for y in sorted_y:
                # 라인 내에서 X 좌표 순으로 단어 정렬 (왼쪽에서 오른쪽으로)
                line_words = sorted(lines[y], key=lambda x: x[0])
                
                # 단어들을 이어 붙일 때 간격 확인
                line_str = ""
                if not line_words:
                    continue
                    
                line_str = line_words[0][4]
                prev_x1 = line_words[0][2]
                
                for i in range(1, len(line_words)):
                    curr_word = line_words[i]
                    curr_x0 = curr_word[0]
                    word_text = curr_word[4]
                    
                    # 두 단어 사이의 간격 계산
                    gap = curr_x0 - prev_x1
                    
                    # 간격이 좁으면(예: 3px 미만) 붙이고, 넓으면 띄움
                    # 문장 부호나 조사가 분리된 경우를 해결하기 위함
                    if gap < 3.0: 
                        line_str += word_text
                    else:
                        line_str += " " + word_text
                    
                    prev_x1 = curr_word[2]
                
                page_text += line_str + "\n"
            
            full_text.append(page_text)
            
        # 전체 텍스트 병합 후 최종적으로 줄바꿈 정제 함수 호출
        # 사용자 정의 정렬로 인해 순서는 맞겠지만, 줄바꿈은 여전히 존재하므로 병합이 필요함.
        raw_text = "\n".join(full_text)
        return _merge_broken_lines(raw_text)

    except Exception:
        return ""

def _merge_broken_lines(text):
    if not text:
        return ""
        
    lines = text.split('\n')
    merged_lines = []
    current_line = ""
    
    # 문장 종결 및 구분을 위한 부호
    end_chars = ('.', '?', '!', ':', ';', '”', '"', "'", '>', '）', ')')
    # 목록 마커
    bullets = ('-', '*', '•', '·')
    # 공백 없이 앞 줄에 붙여야 하는 문장 부호 및 조사
    sticky_chars = ('.', ',', '!', '?', ':', ';', '”', '"', "'", ')', '}', ']', '>', '）')
    # 조사가 줄 바꿈으로 인해 분리되는 경우 (주요 조사 예시)
    particles = ('가', '이', '는', '은', '를', '을', '에', '와', '과', '도', '만', '의', '로', '으로', '고')
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_line:
                merged_lines.append(current_line)
                current_line = ""
            merged_lines.append("")
            continue
        
        is_list_item = (len(line) > 0 and line[0].isdigit()) or line.startswith(bullets)
        
        if not current_line:
            current_line = line
        else:
            # 1. 이전 줄이 문장 종결 부호로 끝나거나, 현재 줄이 목록 형태인 경우 -> 줄 바꿈 유지
            if current_line.endswith(end_chars) or is_list_item:
                merged_lines.append(current_line)
                current_line = line
            # 2. 현재 줄이 문장 부호(sticky_chars)나 특정 조사로 시작하는 경우 -> 공백 없이 붙임
            elif line[0] in sticky_chars or (len(line) == 1 and line in particles):
                current_line += line
            # 3. 그 외의 경우 (단어 중간 줄 바꿈 등) -> 공백 하나 넣고 합침
            else:
                current_line += " " + line
                
    if current_line:
        merged_lines.append(current_line)
        
    cleaned_text = '\n'.join(merged_lines)
    # 중복 공백 제거 로직 추가
    import re
    cleaned_text = re.sub(r'[ \t]{2,}', ' ', cleaned_text)
    return cleaned_text

def extract_text_from_docx(file_path):
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except: return ""

def extract_text_from_hwp(file_path):
    """
    HWP 파일에서 텍스트를 추출합니다.
    
    우선순위:
    1. hwp5 라이브러리 main() 직접 호출 (In-Process) - 가장 안정적
    2. olefile - PrvText 섹션 (fallback)
    """
    # 1차 시도: hwp5txt 메인 함수 직접 호출
    try:
        from hwp5.hwp5txt import main as hwp5txt_main
        import sys
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name
            
        saved_argv = sys.argv
        try:
            sys.argv = ['hwp5txt', '--output', tmp_path, file_path]
            hwp5txt_main()
            
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read().strip()
                if text:
                    return text
                    
        except Exception:
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

def extract_text_from_hwpx(file_path):
    """
    HWPX 파일에서 텍스트를 추출합니다.
    """
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        with zipfile.ZipFile(file_path, 'r') as zf:
            text_parts = []
            section_files = sorted([
                name for name in zf.namelist()
                if name.startswith('Contents/section') and name.endswith('.xml')
            ])
            
            for section_file in section_files:
                try:
                    with zf.open(section_file) as f:
                        xml_content = f.read()
                        root = ET.fromstring(xml_content)
                        for elem in root.iter():
                            if elem.tag.endswith('}t') or elem.tag == 't':
                                if elem.text:
                                    text_parts.append(elem.text)
                except Exception:
                    continue
            return '\n'.join(text_parts).strip()
    except Exception:
        pass
    return ""
