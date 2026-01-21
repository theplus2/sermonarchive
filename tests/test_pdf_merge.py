
def merge_broken_lines(text):
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
        is_list_item = line[0].isdigit() or line.startswith(bullets)
        
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

def test_merge():
    # Example text simulating PDF hard wrapping
    sample = """
This is a sentence that has been broken
into multiple lines because of the
PDF format.
But this is a new sentence.

Also, here is a list:
1. First item
2. Second item ends here.
3. Third item continues
on the next line.

Korean text example:
안녕하세요. 반갑습니다.
이 문장은 줄바꿈이
되어 있습니다.
잘 이어질까요?
    """
    
    print("--- Original ---")
    print(sample)
    print("\n--- Merged ---")
    merged = merge_broken_lines(sample)
    print(merged)
    
    # Simple assertions
    assert "broken into multiple lines" in merged
    assert "continues on the next line" in merged
    assert "줄바꿈이 되어 있습니다" in merged

if __name__ == "__main__":
    test_merge()
