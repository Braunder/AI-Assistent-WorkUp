cache = {}

class User:
    def __init__(self, id):
        self.id = str(id)

    def __hash__(self):
        return hash(self.id)  # Хэш от ID

    def __eq__(self, other):
        return isinstance(other, User) and self.id == other.id

# Вставка
user1 = User("u-123")

# Пользователь обновляет профиль через API
user1.id = "u-456"  # ОШИБКА! Хэш изменился!

print(f"user1 in cache: {user1 in cache}")  # ?