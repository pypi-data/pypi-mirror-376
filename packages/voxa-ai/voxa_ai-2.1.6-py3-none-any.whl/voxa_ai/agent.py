import os
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

console = Console()

try:
    from openai import OpenAI
    GPT_AVAILABLE = True
except Exception:
    GPT_AVAILABLE = False

try:
    from rapidfuzz import process, fuzz
    import re
except Exception as e:
    raise RuntimeError("rapidfuzz is required. Install with: pip install rapidfuzz") from e

BASE_DIR = os.path.dirname(__file__)
OFFLINE_PATHS = [
    os.path.join(BASE_DIR, "offline_qa.json"),
    os.path.join(os.getcwd(), "offline_qa.json"),
]

QA_LIST = []
for p in OFFLINE_PATHS:
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                QA_LIST = json.load(f)
            break
        except Exception:
            QA_LIST = []
            break

def _normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

NORM_CHOICES = []
NORM_MAP = {}
if QA_LIST:
    for idx, item in enumerate(QA_LIST):
        q = item.get("question", "")
        nq = _normalize_text(q)
        NORM_CHOICES.append(nq)
        if nq and nq not in NORM_MAP:
            NORM_MAP[nq] = idx

def save_to_txt(query: str, answer: str, filename: str = "voxa_ai_output.txt") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"--- Voxa AI Consultation ---\n{ts}\nYou: {query}\nVoxa AI: {answer}\n\n")

def offline_answer(query: str, threshold: int = 65) -> str:
    if not QA_LIST:
        return "I'll do my best to help you. Could you ask me something specific?"

    nq = _normalize_text(query)

    if NORM_CHOICES:
        match = process.extractOne(nq, NORM_CHOICES, scorer=fuzz.token_set_ratio)
        if match and len(match) >= 2 and match[1] >= threshold:
            matched_norm = match[0]
            idx = NORM_MAP.get(matched_norm)
            if idx is not None:
                return QA_LIST[idx].get("answer", "").strip()

    q_words = set(nq.split())
    best_idx = None
    best_overlap = 0
    for norm_q, idx in NORM_MAP.items():
        overlap = len(q_words.intersection(set(norm_q.split())))
        if overlap > best_overlap:
            best_overlap = overlap
            best_idx = idx

    if best_idx is not None and best_overlap >= 1:
        return QA_LIST[best_idx].get("answer", "").strip()

    return "I'm here to support you. Could you rephrase or ask another question?"

def validate_api_key(key: str) -> bool:
    """Validate OpenAI API key (personal or project key)"""
    if not key or not GPT_AVAILABLE:
        return False
    try:
        client = OpenAI(api_key=key)
        client.models.list()  # simple test without limit
        return True
    except Exception as e:
        err_str = str(e).lower()
        # Reject obviously invalid keys
        if "invalid" in err_str or "unauthorized" in err_str or "forbidden" in err_str:
            return False
        # Allow project keys that may raise warnings
        console.print(Panel(f"⚠️ Validation warning (project key?): {e}", border_style="yellow"))
        return True

def gpt_answer(query: str, primary: str = "gpt-4", fallback: str = "gpt-3.5-turbo") -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not GPT_AVAILABLE:
        return offline_answer(query)

    client = OpenAI(api_key=api_key)

    for model in (primary, fallback):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are Voxa AI, a professional and friendly assistant."},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=600
            )
            if hasattr(response, "choices") and response.choices:
                content = response.choices[0].message.content
                if content:
                    return content.strip()
        except Exception:
            continue

    return offline_answer(query)

def run_agent(query: str) -> str:
    ECHO_USER_INPUT = os.environ.get("ECHO_USER_INPUT", "false").lower() in ("1", "true", "yes")
    if ECHO_USER_INPUT:
        console.print(f"\n[bold white]💬 You › {query}[/bold white]\n")

    if os.environ.get("OPENAI_API_KEY") and GPT_AVAILABLE:
        try:
            answer = gpt_answer(query)
        except Exception:
            answer = offline_answer(query)
    else:
        answer = offline_answer(query)

    panel = Panel(Align.left(f"🤖 Voxa AI › {answer}"), border_style="bright_green", padding=(1, 2))
    console.print(panel)

    console.print("\n[bold bright_cyan]🤝 If you have any other question, I am here to answer you![/bold bright_cyan]\n")

    try:
        save_to_txt(query, answer)
    except Exception:
        pass

    return answer

def prompt_for_api_key():
    console.print("\n🔑 Press Enter for offline mode, or enter your OpenAI API key for GPT mode (type 'exit' to quit):")
    key = input(">>> ").strip()

    if key.lower() == "exit":
        console.print("\n👋 Exiting...")
        raise SystemExit(0)

    if not key:
        console.print(Panel("📴 Offline mode ENABLED.", border_style="red"))
        return None

    if validate_api_key(key):
        os.environ["OPENAI_API_KEY"] = key
        console.print(Panel("✅ GPT mode ENABLED!", border_style="green"))
        return key
    else:
        console.print(Panel("❌ Invalid API key. Switching to offline mode.", border_style="red"))
        return None

if __name__ == "__main__":
    prompt_for_api_key()
    while True:
        query = input("\n💬 Your Question › ")
        if query.lower().strip() in ("exit", "quit"):
            console.print("\n👋 Goodbye!")
            break
        run_agent(query)
