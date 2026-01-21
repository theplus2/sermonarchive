import zipfile
import xml.etree.ElementTree as ET
import tempfile
import sys
import os
from docx import Document
from pdfminer.high_level import extract_text

def extract_text_from_pdf(file_path):
    try:
        text = extract_text(file_path).strip()
        return _merge_broken_lines(text)
    except Exception:
        return ""

def _merge_broken_lines(text):
    if not text:
        return ""
        
    lines = text.split('\n')
    merged_lines = []
    current_line = ""
    
    # Sentence ending characters
    end_chars = ('.', '?', '!', ':', ';', '”', '"', "'")
    # List item markers
    bullets = ('-', '*', '•', '·')
    
    for line in lines:
        line = line.strip()
        if not line:
            # Empty line -> preserve paragraph break
            if current_line:
                merged_lines.append(current_line)
                current_line = ""
            merged_lines.append("")
            continue
        
        # Check if this line is a list item
        # Safe check for index access
        is_list_item = (len(line) > 0 and line[0].isdigit()) or line.startswith(bullets)
        
        if not current_line:
            current_line = line
        else:
            # Check if previous line ended with punctuation OR current line is list item
            if current_line.endswith(end_chars) or is_list_item:
                # Ends with punctuation -> legitimate newline (probably)
                merged_lines.append(current_line)
                current_line = line
            else:
                # Doesn't end with punctuation -> probably hard wrap -> merge
                # Use space to join
                current_line += " " + line
                
    if current_line:
        merged_lines.append(current_line)
        
    return '\n'.join(merged_lines)

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
    """
    # 1차 시도: hwp5txt 메인 함수 직접 호출
    try:
        from hwp5.hwp5txt import main as hwp5txt_main
        
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
