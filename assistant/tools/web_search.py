from tavily import TavilyClient

from assistant.config import settings


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web via Tavily and return a formatted result string.
    Raises ValueError if TAVILY_API_KEY is not configured.
    """
    if not settings.tavily_api_key:
        return "❌ TAVILY_API_KEY не настроен. Добавь его в файл .env."

    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(
        query=query,
        max_results=max_results,
        include_answer=True,
    )

    parts: list[str] = []

    answer = response.get("answer")
    if answer:
        parts.append(f"💡 Краткий ответ: {answer}\n")

    for result in response.get("results", []):
        title = result.get("title", "")
        url = result.get("url", "")
        excerpt = result.get("content", "")[:400]
        parts.append(f"📄 {title}\n   {url}\n   {excerpt}\n")

    return "\n".join(parts) if parts else "Результаты не найдены."
