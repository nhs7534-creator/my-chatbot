import pdfplumber
import os

def load_all_pdfs(docs_folder="docs"):
    """docs 폴더의 모든 PDF를 읽어서 텍스트로 변환"""
    all_text = {}
    
    if not os.path.exists(docs_folder):
        return {}
    
    for filename in os.listdir(docs_folder):
        if filename.endswith(".pdf"):
            filepath = os.path.join(docs_folder, filename)
            text = ""
            try:
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                all_text[filename] = text
                print(f"✅ PDF 로드 완료: {filename}")
            except Exception as e:
                print(f"❌ PDF 읽기 실패 {filename}: {e}")
    
    return all_text


def search_relevant_text(question, pdf_texts, max_chars=2000):
    """질문과 관련된 PDF 내용 검색"""
    question_keywords = question.lower().split()
    relevant_sections = []
    
    for filename, text in pdf_texts.items():
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) < 10:
                continue
            
            score = 0
            para_lower = paragraph.lower()
            for keyword in question_keywords:
                if len(keyword) >= 2 and keyword in para_lower:
                    score += 1
            
            if score > 0:
                relevant_sections.append((score, paragraph.strip(), filename))
    
    relevant_sections.sort(key=lambda x: x[0], reverse=True)
    
    result_text = ""
    for score, text, filename in relevant_sections[:10]:
        result_text += f"[{filename}] {text}\n\n"
        if len(result_text) > max_chars:
            break
    
    return result_text if result_text else "관련 내용을 찾지 못했습니다."