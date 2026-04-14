from pathlib import Path

from assistant.config import settings


def _read_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


_ANTI_HALLUCINATION_BLOCK = """
## ПРАВИЛА ЧЕСТНОСТИ (ОБЯЗАТЕЛЬНО СОБЛЮДАТЬ)
- ❌ ЗАПРЕЩЕНО выдумывать версии библиотек, параметры API, имена авторов или статистику
- ✅ Если не уверен в факте — явно скажи: «Нужно проверить» или «Я не уверен»
- После каждого фактического утверждения (версии, числа, имена, даты) добавляй тег:
  <confidence>N/5: краткая причина</confidence>
  Где N: 1=догадка, 2=не уверен, 3=вероятно верно, 4=уверен, 5=проверенный факт из базы знаний
- Если N <= 2, явно предложи пользователю нажать кнопку «Verify» для проверки
- Никогда не вставляй этот тег в середину кода — только после текстовых утверждений
"""


def build_system_prompt(memory_context: str = "", coach_mode_context: str = "") -> str:
    """
    Assemble the full system prompt from:
    - Role definition + instructions
    - 2-week study plan (full text)
    - Theory curriculum map (section headers only, to save tokens)
    - Injected RAG memory context from past sessions
    - Anti-hallucination rules
    """
    root = settings.workspace_root
    template = _read_safe(root / "assistant" / "core" / "system_prompt_template.txt")

    # Extract only ## headings from the theory file to keep context short
    theory_text = _read_safe(root / "MASTER_THEORY_LM_DEVOPS_MLOPS.md")
    theory_map = "\n".join(
        line for line in theory_text.splitlines() if line.startswith("##")
    )

    fallback_template = (
        "Ты — персональный AI-ментор и ML-коуч.\n"
        "## КАРТА ТЕМ (теоретическая база)\n{THEORY_MAP}\n"
        "## КОНТЕКСТ ИЗ ПРЕДЫДУЩИХ СЕССИЙ\n{MEMORY_CONTEXT}\n"
        "## АКТИВНЫЙ РЕЖИМ КОУЧИНГА\n{COACH_MODE_CONTEXT}\n"
    )
    active_template = template or fallback_template

    base = active_template.format(
        THEORY_MAP=theory_map,
        MEMORY_CONTEXT=memory_context.strip() or "Нет релевантных записей.",
        COACH_MODE_CONTEXT=coach_mode_context.strip() or "Режим: study (стандартный менторинг).",
    )
    return base + _ANTI_HALLUCINATION_BLOCK
