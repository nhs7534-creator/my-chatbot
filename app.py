from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import glob

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def read_pdf_texts(docs_folder="docs"):
    texts = []
    try:
        import fitz
        for pdf_path in glob.glob(f"{docs_folder}/*.pdf"):
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            if text.strip():
                texts.append({"file": os.path.basename(pdf_path), "text": text[:3000]})
            doc.close()
    except Exception as e:
        print(f"PDF 읽기 오류: {e}")
    return texts

def get_ai_answer(question):
    pdf_texts = read_pdf_texts("docs")
    
    context = ""
    for pdf in pdf_texts[:3]:
        context += f"\n[{pdf['file']}]\n{pdf['text']}\n"

    system_prompt = """당신은 평택지역자활센터의 전문 상담 챗봇입니다.
국민기초생활보장제도와 자활사업에 대해 친절하고 정확하게 안내합니다.

답변 규칙:
1. 제공된 문서 내용을 최대한 활용하여 구체적으로 답변하세요
2. 신청자격, 절차, 필요서류 등을 구체적으로 안내하세요
3. 모르는 내용은 "평택지역자활센터(031-000-0000)로 문의해 주세요"라고 안내하세요
4. 답변은 5~8문장으로 구체적으로 작성하세요
5. 친근하고 따뜻한 말투를 사용하세요"""

    user_message = f"""질문: {question}

참고 문서:
{context}

위 문서를 참고하여 구체적으로 답변해주세요."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI 오류: {e}")
        return "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "running", "message": "자활센터 챗봇 서버 정상 작동 중"})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        user_question = data.get('userRequest', {}).get('utterance', '')
        print(f"📩 받은 질문: {user_question}")
        if not user_question:
            return kakao_response("질문을 입력해주세요.")
        answer = get_ai_answer(user_question)
        return kakao_response(answer)
    except Exception as e:
        print(f"❌ 오류: {e}")
        return kakao_response("오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

def kakao_response(text):
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}]
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)