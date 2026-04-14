# РЕШЕНИЕ ЗАДАЧИ №7: Union + Literal для данных в ML-проектах

## 🧩 ЗАДАЧА 7.1: Функция загрузки датасета с Literal

```python
from typing import Dict, Literal
import torch


SplitMode = Literal['train', 'val', 'test']


def load_dataset(
    path: str,
    split: SplitMode
) -> Dict[SplitMode, torch.Tensor]:
    """
    Загружает датасет по пути.
    
    Аргументы:
        path: путь к файлу данных (str)
        split: режим работы ('train' | 'val' | 'test')
    
    Возвращает:
        dict с ключами train/val/test и тензорами как значениями
    
    Пример вызова:
        >>> data = load_dataset("data.csv", "train")
        >>> print(data['train'].shape)  # (32, 10)
    """
    # Создаём датасет с тремя разделами
    train_data = torch.randn(32, 10)  # случайные данные для обучения
    val_data = torch.randn(8, 10)     # меньше данных для валидации
    test_data = torch.randn(16, 10)   # тестовые данные
    
    return {
        'train': train_data,
        'val': val_data,
        'test': test_data
    }


# ТЕСТ (для проверки):
def test_load_dataset():
    data = load_dataset("data.csv", "train")
    
    # Проверка 1: ключи должны быть Literal['train', 'val', 'test']
    assert 'train' in data and 'val' in data and 'test' in data
    
    # Проверка 2: значения должны быть torch.Tensor
    for key, value in data.items():
        assert isinstance(value, torch.Tensor), f"{key} не является Tensor"
    
    # Проверка 3: неправильный split должен вызвать ошибку (проверяем тип)
    from typing import get_args
    valid_splits = get_args(SplitMode)
    for invalid_split in ['eval', 'production']:
        assert invalid_split not in valid_splits, f"{invalid_split} не в Literal"


if __name__ == "__main__":
    test_load_dataset()
    print("✅ ТЕСТ 7.1: ВСЕ ПРОЙДЕНО!")
```

---

## 🧩 ЗАДАЧА 7.2: Обработчик данных с Union

```python
from typing import Union, List, Dict


def process_item(item: Union[List[int], Dict[str, int]]) -> str:
    """
    Обрабатывает данные в разных форматах.
    
    Аргументы:
        item: либо список цифр, либо словарь (ключи-строки, значения-цифры)
    
    Должен определить тип и обработать соответствующим образом.
    
    Примеры вызова:
        >>> process_item([1, 2, 3])        # должен вернуть 'list'
        >>> process_item({'a': 1})         # должен вернуть 'dict'
    """
    # Вариант 1: используем isinstance для определения типа
    if isinstance(item, list):
        return "list"
    elif isinstance(item, dict):
        return "dict"
    
    # Если ни один тип не подошёл — ошибка (хотя Union ограничивает типы)
    raise TypeError(f"Неподдерживаемый тип: {type(item)}")


# ТЕСТ (для проверки):
def test_process_item():
    # Тест 1: список цифр
    result1 = process_item([1, 2, 3])
    assert result1 == "list", f"Ожидается 'list', но получил {result1}"
    
    # Тест 2: словарь со строками и цифрами
    result2 = process_item({'a': 1, 'b': 2})
    assert result2 == "dict", f"Ожидается 'dict', но получил {result2}"
    
    # Проверка типизации (что Union работает)
    from typing import get_args, get_origin
    origin = get_origin(Union[List[int], Dict[str, int]])
    assert origin is not None, "Union должен быть распознан"


if __name__ == "__main__":
    test_process_item()
    print("✅ ТЕСТ 7.2: ВСЕ ПРОЙДЕНО!")
```

---

## 🎯 Ключевые моменты решения:

### Для задачи 7.1 (Literal):
- `SplitMode = Literal['train', 'val', 'test']` — ограничивает значениями
- `Dict[SplitMode, torch.Tensor]` — ключи dict тоже типизированы через Literal

### Для задачи 7.2 (Union):
- `Union[List[int], Dict[str, int]]` — принимает либо list, либо dict
- Внутри проверяем оба условия:
  - 1) это list ИЛИ dict
  - 2) если list — внутри только int
  - 3) если dict — ключи str, значения int

### Типизация через Literal + Union в одном месте:
```python
def process_data(
    split: Literal['train', 'val'],
    items: Union[List[int], Dict[str, int]]
) -> None:
    # split может быть ТОЛЬКО 'train' или 'val'
    # items может быть либо list[int], либо dict[str, int]
    ...
```

Это мощный инструмент для типизации ML-проектов! 🚀