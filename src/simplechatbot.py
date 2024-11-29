import os
from llama_cpp import Llama

# 모델 경로 설정
MODEL_PATH = "../models/llama-3.2-3B.gguf"
CONVERSATION_FILE = "conversation_history.txt"

# Llama 모델 로드
print("Loading model...")
llm = Llama(model_path=MODEL_PATH)
print("Model loaded successfully!")

# 대화 내역 저장 함수
def save_conversation(conversation, file_path):
    """대화 내역을 파일에 저장하는 함수."""
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(conversation + "\n")

# 대화 내역 불러오기 함수
def load_conversation(file_path):
    """저장된 대화 내역을 불러오는 함수."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    return ""

def generate_response(query, conversation_file, max_context=512):
    """사용자 입력(query)에 대한 모델 응답 생성."""
    # 기존 대화 기록 로드
    conversation_history = load_conversation(conversation_file)

    # 대화 기록 자르기
    trimmed_conversation = trim_conversation(conversation_history, max_context - 100)

    # 프롬프트 구성
    prompt = f"""[INST] <<SYS>>
You are a helpful assistant. Continue the following conversation:
{trimmed_conversation}
<</SYS>>

User: {query}
Assistant: """

    # 모델에 프롬프트 전달
    max_tokens = 100  # 응답 길이
    output = llm.create_completion(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.7,
        top_p=0.9,
        stop=["</s>", "[/INST]"]
    )

    response = output['choices'][0]['text'].strip() if 'choices' in output and len(output['choices']) > 0 else "No response generated."

    # 대화 내역 저장
    conversation = f"User: {query}\nAssistant: {response}"
    save_conversation(conversation, conversation_file)

    return response


def trim_conversation(conversation, max_length=400):
    """컨텍스트 제한을 넘지 않도록 대화 기록을 자르는 함수."""
    tokens = conversation.split()  # 토큰화를 간단히 처리 (정교하게 하려면 tokenizer 사용)
    if len(tokens) > max_length:
        return ' '.join(tokens[-max_length:])  # 최신 대화 기록만 유지
    return conversation


# 실시간 입력 루프
def chat_loop():
    """사용자 입력을 실시간으로 받아 모델 응답을 출력."""
    print("\nWelcome to Llama Chatbot! Type 'exit' to quit.")

    while True:
        query = input("\nUser: ")
        if query.lower() in ["exit", "quit"]:
            print("Exiting the chat. Goodbye!")
            break

        response = generate_response(query, CONVERSATION_FILE)
        print("Assistant:", response)

# 프로그램 실행
if __name__ == "__main__":
    # 기존 대화 내역 로드
    conversation_history = load_conversation(CONVERSATION_FILE)
    if conversation_history:
        print("Previous conversation history loaded.")
        print(conversation_history)
    else:
        print("No previous conversation found. Starting a new session.")

    # 챗봇 실행
    chat_loop()
