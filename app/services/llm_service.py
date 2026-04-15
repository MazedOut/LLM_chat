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

    prompt = f"<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant\n"
    result = llm(prompt, max_tokens=200, stream=False)
    return result["choices"][0]["text"].strip()

import os

_llm = None


def get_llm():
    global _llm
    if _llm is not None:
        return _llm

    model_path = "model.gguf"
    if not os.path.exists(model_path):
        print("WARNING: model.gguf not found")
        return None

    from llama_cpp import Llama
    print("Loading model...")
    _llm = Llama(model_path=model_path, n_ctx=512, n_threads=4)
    print("Model loaded")
    return _llm


def generate_response(user_message: str) -> str:
    llm = get_llm()

    if llm is None:
        return "[Model not loaded. Place model.gguf in project root]"

    prompt = f"<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant\n"
    result = llm(prompt, max_tokens=200, stream=False, stop=["<|im_end|>", "<|im_start|>"])
    return result["choices"][0]["text"].strip()


def stream_response(user_message: str):
    llm = get_llm()

    if llm is None:
        yield "[Model not loaded]"
        return

    prompt = f"<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant\n"
    stream = llm(prompt, max_tokens=200, stream=True, stop=["<|im_end|>", "<|im_start|>"])

    for chunk in stream:
        token = chunk["choices"][0]["text"]
        if token:
            yield token