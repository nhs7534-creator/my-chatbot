from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from pdf_search import load_all_pdfs, search_relevant_text
import os

load_dotenv()

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("📚 PDF 문서 로딩 중...")
pdf_texts = load_all_pdfs("docs")
print(f"✅ 총 {len(pdf_texts)}개 PDF 로드 완료")


def get_ai_answer(question, context):
    system_prompt = """당신은 평택지역자활센터의 상담 챗봇입니다.
국민기초생활보장제도와 자활사업에 대해 친절하고 정확하게 안내합니다.

답변 규칙:
1. 제공된 문서 내용을 바탕으로 답변하세요
2. 모르는 내용은 솔직하게 모른다고 하고, 센터 방문을 안내하세요
3. 전화번호나 주소 문의는 "031-000-0000으로 연락 주세요"라고 안내하세요
4. 답변은 3~5문장으로 간결하게 작성하세요
5. 친근하고 따뜻한 말투를 사용하세요"""

    user_message = f"""질문: {question}

관련 문서 내용:
{context}

위 내용을 참고하여 질문에 답변해주세요."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
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

        context = search_relevant_text(user_question, pdf_texts)
        answer = get_ai_answer(user_question, context)
        print(f"💬 생성된 답변: {answer[:50]}...")

        return kakao_response(answer)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return kakao_response("오류가 발생했습니다. 잠시 후 다시 시도해주세요.")


def kakao_response(text):
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)