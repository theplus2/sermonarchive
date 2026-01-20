"""
HWPX 파싱 테스트 스크립트
실제 HWPX 파일에서 텍스트를 추출할 수 있는지 검증합니다.
"""
import os
import sys

# processor 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processor import extract_text_from_hwpx

def test_hwpx_extraction():
    """실제 HWPX 파일로 텍스트 추출 테스트"""
    test_file = os.path.join(os.path.dirname(__file__), "2019 목사고시 설교문-윤영천 전도사.hwpx")
    
    if not os.path.exists(test_file):
        print(f"❌ 테스트 파일을 찾을 수 없습니다: {test_file}")
        return False
    
    print(f"📄 테스트 파일: {test_file}")
    print("-" * 50)
    
    text = extract_text_from_hwpx(test_file)
    
    if text:
        print(f"✅ 텍스트 추출 성공! (총 {len(text)}자)")
        print("-" * 50)
        print("📝 추출된 텍스트 미리보기 (처음 500자):")
        print(text[:500])
        print("-" * 50)
        return True
    else:
        print("❌ 텍스트 추출 실패 (빈 문자열 반환)")
        return False

if __name__ == "__main__":
    success = test_hwpx_extraction()
    sys.exit(0 if success else 1)
