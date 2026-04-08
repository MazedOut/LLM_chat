import os

_llm = None


def get_llm():
    global _llm
    if _llm is not None:
        return _llm

    model_path = "model.gguf"
    if not os.path.exists(model_path):
        return None

    from llama_cpp import Llama
    _llm = Llama(model_path=model_path, n_ctx=512, n_threads=4)
    return _llm


def generate_response(user_message: str) -> str:
    llm = get_llm()

    if llm is None:
        return "[Model not loaded. Place model.gguf in the project root.]"

    prompt = f"User: {user_message}\nAssistant:"
    result = llm(prompt, max_tokens=200, stream=False)
    return result["choices"][0]["text"].strip()
