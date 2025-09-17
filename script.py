# Создаем обновленный шаблон CSV с правильной структурой Country|Prompt|Website
import pandas as pd

# Создаем тестовый файл с примерами бытовой техники для UK, USA, Germany
test_data = {
    'Country': [
        'UK', 'UK', 'UK', 'UK', 'UK',
        'USA', 'USA', 'USA', 'USA', 'USA', 
        'Germany', 'Germany', 'Germany', 'Germany', 'Germany'
    ],
    'Prompt': [
        # UK prompts
        'Dyson V15 cordless vacuum cleaner best price',
        'KitchenAid stand mixer reviews UK',
        'Samsung washing machine 9kg front loading',
        'Ninja air fryer large capacity reviews',
        'Bosch dishwasher integrated 60cm',
        
        # USA prompts  
        'Dyson V15 cordless vacuum cleaner best deal',
        'KitchenAid stand mixer reviews USA',
        'Samsung washing machine 9kg front load',
        'Ninja air fryer XL reviews ratings',
        'Bosch dishwasher built-in stainless steel',
        
        # Germany prompts
        'Dyson V15 kabelloser Staubsauger bester Preis',
        'KitchenAid Küchenmaschine Test Bewertungen',
        'Samsung Waschmaschine 9kg Frontlader',
        'Ninja Heißluftfritteuse groß Test',
        'Bosch Geschirrspüler Einbau 60cm'
    ],
    'Website': [
        # All pointing to amazon.com as requested
        'amazon.com', 'amazon.com', 'amazon.com', 'amazon.com', 'amazon.com',
        'amazon.com', 'amazon.com', 'amazon.com', 'amazon.com', 'amazon.com',
        'amazon.com', 'amazon.com', 'amazon.com', 'amazon.com', 'amazon.com'
    ]
}

df_template = pd.DataFrame(test_data)
df_template.to_csv('ai_visibility_template.csv', index=False)

print("=== ФИНАЛЬНЫЙ ШАБЛОН CSV СОЗДАН ===")
print("Структура: Country | Prompt | Website")
print("=" * 60)
print(df_template.to_csv(index=False))

print("=" * 60)
print("Файл создан: ai_visibility_template.csv")
print("Готов для тестирования!")