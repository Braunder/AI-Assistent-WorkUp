from peft import LoraConfig

def create_lora_config():
    """
    Создай LoraConfig для fine-tuning модели:
    - r=8 (ранг матриц)
    - alpha=16 (сила влияния адаптеров)
    - target_modules=['q_proj', 'v_proj'] (слои, куда вставляем LoRA)
    - lora_dropout=0.1
    
    Верни экземпляр LoraConfig, готовый к использованию с моделью.
    """
    config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=['q_proj', 'v_proj'],
        lora_dropout=0.1,
        bias='none'  # по умолчанию не трогать bias-параметры
    )
    return config

# ТЕСТ (не удаляй):
def test_lora_config():
    config = create_lora_config()
    
    assert isinstance(config, LoraConfig), "Не возвращен LoraConfig"
    assert config.r == 8, f"r должен быть 8, а не {config.r}"
    assert config.lora_alpha == 16, f"alpha должен быть 16, а не {config.lora_alpha}"
    assert set(config.target_modules) == {'q_proj', 'v_proj'}, \
        f"target_modules: {config.target_modules}, ожидается ['q_proj', 'v_proj']"
    assert config.lora_dropout == 0.1, f"dropout должен быть 0.1, а не {config.lora_dropout}"
    
print("Задача №5 готова для решения.")