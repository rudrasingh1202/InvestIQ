"""Helper utilities for InvestIQ - Groq API."""
from __future__ import annotations
import re
import time


def clean_llm_response(text: str) -> str:
    if not text:
        return ""
    cjk = re.search(
        r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]{2,}', text)
    if cjk:
        text = text[:cjk.start()].strip()
    text = re.sub(r'\b(\w{1,3})\s+(\1\s+){3,}', '', text)
    spam = re.search(r'(.)\1{4,}', text)
    if spam:
        text = text[:spam.start()].strip()
    for g in ['<|endoftext|>', '<|im_end|>', '[INST]',
              'AnimationClip', '\x00', '<pad>']:
        if g in text:
            text = text[:text.index(g)].strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean = []
    for sent in sentences:
        words = sent.split()
        if len(words) > 4 and len(set(words)) / len(words) < 0.35:
            break
        clean.append(sent)
    return ' '.join(clean).strip() or "Response not available."


def call_llm(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 300
) -> str:
    import config

    groq_key = getattr(config, "GROQ_API_KEY", None)
    full_prompt = (
        f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    )

    # Models to try in order - all free on Groq
    models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile", 
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama3-70b-8192",
    ]

    if not groq_key:
        return "Groq API key not found. Add GROQ_API_KEY to .env"

    for model in models:
        for attempt in range(2):
            try:
                from groq import Groq

                client = Groq(api_key=groq_key)

                messages = []
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                messages.append({
                    "role": "user",
                    "content": prompt
                })

                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.2,
                )

                content = response.choices[0].message.content
                if content:
                    content = clean_llm_response(content.strip())
                    print(
                        f"[InvestIQ] Groq success "
                        f"({model}): {content[:80]}..."
                    )
                    return content

            except Exception as exc:
                err = str(exc)
                print(
                    f"[InvestIQ] Groq {model} "
                    f"attempt {attempt+1}: {err[:80]}"
                )
                if any(x in err.lower() for x in
                       ['429', 'rate', 'limit', 'quota']):
                    wait = 10 * (attempt + 1)
                    print(f"[InvestIQ] Rate limit - waiting {wait}s")
                    time.sleep(wait)
                    continue
                break

    print("[InvestIQ] All Groq models failed")
    return "AI temporarily unavailable. Please try again."