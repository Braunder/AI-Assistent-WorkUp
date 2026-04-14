# Эталонное решение: ЗАДАЧА №1 — Python asyncio + генераторы

import asyncio
import time


async def fetch_data_async(urls: list[str]) -> list[str]:
    """Асинхронно обрабатывает список URL'ов"""
    results = []
    for url in urls:
        await asyncio.sleep(0.5)  # имитация запроса
        results.append(f"Processed {url}")
    return results


def data_events():
    """Синхронный генератор событий (для обучения)"""
    counter = 0
    while True:
        yield f"Event: {counter}"
        counter += 1
        time.sleep(0.2)


# ТЕСТЫ
def test_fetch_data_async():
    """Проверка fetch_data_async"""
    start = time.perf_counter()
    result = asyncio.run(fetch_data_async(['http://a.com', 'http://b.com']))
    end = time.perf_counter()
    
    assert isinstance(result, list), "Результат должен быть списком"
    assert len(result) == 2, f"Ожидается 2 элемента, получено {len(result)}"
    print(f"✅ fetch_data_async время: {(end - start):.3f} сек (ожидаем ~1.0)")


def test_data_events():
    """Проверка data_events"""
    start = time.perf_counter()
    events = list(data_events())  # Получаем первые события
    end = time.perf_counter()
    
    assert len(events) >= 3, f"Ожидается минимум 3 события, получено {len(events)}"
    print(f"✅ data_events время: {(end - start):.3f} сек (ожидаем ~0.6)")


if __name__ == "__main__":
    test_fetch_data_async()
    test_data_events()

# ВАРИАНТ Б (для production — async генератор):
# 
# async def data_events():
#     counter = 0
#     while True:
#         yield f"Event: {counter}"
#         counter += 1
#         await asyncio.sleep(0.2)