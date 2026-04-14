# ЭТАЛОННОЕ РЕШЕНИЕ ЗАДАЧИ №4: Типизация — List vs Sequence
from typing import List, Sequence
import torch


def process_batch_v1(data: List[int]) -> List[int]:
    """
    Обработчик данных — строгий тип List[int].
    
    Используется там, где данные должны быть именно списком (list).
    Например, когда порядок элементов важен и доступ по индексу.
    """
    return [x * 2 for x in data]


def process_batch_v2(data: Sequence[int]) -> Sequence[int]:
    """
    Обработчик данных — последовательность Sequence[int].
    
    Используется в PyTorch для гибкости: принимает list, tuple, numpy.ndarray.
    Например, функции inference принимают данные в разных форматах.
    """
    return [x * 2 for x in data]


# ТЕСТЫ (полный coverage):
def test_process_batch_v1():
    """Проверка строгого List[int]"""
    
    # ✅ Работает с list
    result = process_batch_v1([1, 2, 3])
    assert result == [2, 4, 6], f"Ожидается [2, 4, 6], получено {result}"
    
    # ❌ Не должно работать с tuple (TypeError)
    try:
        process_batch_v1((1, 2, 3))
        assert False, "process_batch_v1 не должен принимать tuple"
    except TypeError as e:
        pass  # Ожидаем ошибку
    
    print("✅ test_process_batch_v1 пройден")


def test_process_batch_v2():
    """Проверка Sequence[int]"""
    
    # ✅ Работает с list
    result = process_batch_v2([1, 2, 3])
    assert result == [2, 4, 6], f"Ожидается [2, 4, 6], получено {result}"
    
    # ✅ Работает с tuple
    result = process_batch_v2((1, 2, 3))
    assert result == [2, 4, 6], f"Ожидается [2, 4, 6], получено {result}"
    
    # ✅ Работает с numpy (если импортирован)
    import numpy as np
    arr = np.array([1, 2, 3])
    result = process_batch_v2(arr)
    assert result == [2, 4, 6], f"Ожидается [2, 4, 6], получено {result}"
    
    print("✅ test_process_batch_v2 пройден")


# ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: проверка типизации в PyTorch
def test_torch_sequence_usage():
    """Проверка использования Sequence в контексте PyTorch"""
    
    # Имитация функции inference, которая принимает batch данных
    def infer(batch: Sequence[int]) -> torch.Tensor:
        """Функция инференса — принимает любую последовательность"""
        return torch.tensor([x * 2 for x in batch])
    
    # Работает с list
    result1 = infer([1, 2, 3])
    assert torch.equal(result1, torch.tensor([2, 4, 6]))
    
    # Работает с tuple
    result2 = infer((1, 2, 3))
    assert torch.equal(result2, torch.tensor([2, 4, 6]))
    
    print("✅ test_torch_sequence_usage пройден")


if __name__ == "__main__":
    test_process_batch_v1()
    test_process_batch_v2()
    test_torch_sequence_usage()
    print("\n🎉 Все тесты пройдены!")