import logging
from difflib import SequenceMatcher
from .models import Category

logger = logging.getLogger(__name__)


def _normalize_category_text(value: str) -> str:
    text = (value or '').strip().lower()
    replacements = {
        'йі': 'ї',
        'йи': 'ї',
        'іжа': 'їжа',
        'іжу': 'їжа',
        'ізя': 'їжа',
        'ізю': 'їжа',
        'ізью': 'їжа',
        'изя': 'їжа',
        'изю': 'їжа',
        'изью': 'їжа',
        'йиж': 'їж',
        'йізя': 'їжа',
        'йізю': 'їжа',
        'їзя': 'їжа',
        'їзю': 'їжа',
        'їзью': 'їжа',
        'їжу': 'їжа',
        'їжі': 'їжа',
        'їжею': 'їжа',
        'jizha': 'їжа',
        'yizha': 'їжа',
        'продуктів': 'продукти',
        'продукты': 'продукти',
        'такси': 'таксі',
        'комуналка': 'комунальні',
    }
    text = text.replace('ґ', 'г').replace('ғ', 'г')
    for source, target in replacements.items():
        text = text.replace(source, target)
    return ' '.join(text.replace('-', ' ').replace('_', ' ').split())

class CategoryMatcher:
    def __init__(self, user):
        self.user = user
        self.categories = list(
            Category.objects.filter(user=user) | 
            Category.objects.filter(is_system=True)
        )
    
    def match(self, description: str, bank_category: str = '', amount: float = 0) -> tuple:
        description_lower = description.lower()
        bank_category_lower = bank_category.lower()
        best_match = None
        best_score = 0
        
        for category in self.categories:
            score = self._calculate_score(
                description_lower, 
                category.keywords,
                bank_category_lower,
                amount,
                category.type,
                category.name
            )
            
            if score > best_score:
                best_score = score
                best_match = category
        

        if best_score >= 1.0:
            return best_match, best_score
        
        fallback_name = 'Інший дохід' if amount > 0 else 'Інше'
        
        for category in self.categories:
            if category.name == fallback_name:
                logger.debug("No strong match for '%s…'. Fallback: %s", description[:30], fallback_name)
                return category, 0.1 
        
        return None, 0
    
    def _calculate_score(self, description: str, keywords: list, 
                         bank_category: str, amount: float, 
                         category_type: str, category_name: str) -> float:
        

        if not keywords:
            if (category_type == 'INCOME' and amount > 0) or (category_type == 'EXPENSE' and amount < 0):
                 return 0.1 
            return 0 

        score = 0
        
        if bank_category:
             if bank_category in category_name.lower() or category_name.lower() in bank_category:
                 score += 1.5
             for keyword in keywords:
                 if keyword.lower() in bank_category:
                     score += 1.0

        for keyword in keywords:
            keyword_lower = keyword.lower()
            if f" {keyword_lower} " in f" {description} ": 
                score += 1.0
            elif keyword_lower in description:
                score += 0.7
        
        if (category_type == 'INCOME' and amount > 0):
            score += 0.2
        elif (category_type == 'EXPENSE' and amount < 0):
            score += 0.2
            
        return score

def find_category_for_transaction(user, description: str, bank_category: str = '', amount: float = 0):
    matcher = CategoryMatcher(user)
    category, score = matcher.match(
        description=description,
        bank_category=bank_category,
        amount=amount
    )
    
    if category:
        logger.debug("Match: '%s…' -> %s (%.2f)", description[:30], category.name, score)
        return category, score
    
    logger.debug("No match for: '%s…'", description[:30])
    return None, 0


def find_category_by_name(user, category_name: str):
    normalized = _normalize_category_text(category_name)
    if not normalized:
        return None

    categories = list(
        Category.objects.filter(user=user) |
        Category.objects.filter(is_system=True)
    )

    for category in categories:
        if _normalize_category_text(category.name) == normalized:
            return category

    for category in categories:
        name = _normalize_category_text(category.name)
        if normalized in name or name in normalized:
            return category

    for category in categories:
        for keyword in category.keywords or []:
            keyword = _normalize_category_text(str(keyword))
            if keyword and (normalized == keyword or normalized in keyword or keyword in normalized):
                return category

    best_category = None
    best_score = 0.0
    for category in categories:
        candidates = [category.name, *(category.keywords or [])]
        for candidate in candidates:
            candidate_norm = _normalize_category_text(str(candidate))
            if not candidate_norm:
                continue
            score = SequenceMatcher(None, normalized, candidate_norm).ratio()
            if score > best_score:
                best_score = score
                best_category = category

    if best_score >= 0.78:
        return best_category

    return None


def create_default_categories(user):
    default_categories = [
        {'name': 'Перекази', 'type': 'INCOME', 'keywords': ['переказ на свою картку', 'перекази', 'платежі за реквізитами']},
        {'name': 'Продукти', 'type': 'EXPENSE', 'keywords': ['сільпо', 'атб', 'ашан', 'фреш','супермаркет', 'магазин', 'продукти', 'траш', 'silpo', 'mahazyn']},
        {'name': 'Транспорт', 'type': 'EXPENSE', 'keywords': ['бензин', 'авто', 'uber', 'uklon', 'bolt', 'таксі', 'метро', 'автобус', 'паркування']},
        {'name': 'Кафе та ресторани', 'type': 'EXPENSE', 'keywords': ['mcdonalds', 'kfc', 'кафе', 'ресторан', 'їжа', 'pizza']},
        {'name': 'Комунальні послуги', 'type': 'EXPENSE', 'keywords': ['комунальні', 'gas', 'вода', 'електроенергія', 'інтернет', 'kyivstar']},
        {'name': 'Розваги', 'type': 'EXPENSE', 'keywords': ['кіно', 'театр', 'концерт', 'розваги', 'steam', 'playstation', 'цифрові товари', 'Поповнення мобільного']},
        {'name': 'Одяг та взуття', 'type': 'EXPENSE', 'keywords': ['одяг', 'взуття', 'zara', 'h&m', 'бутік']},
        {'name': 'Здоров\'я', 'type': 'EXPENSE', 'keywords': ['аптека', 'лікарня', 'медицина', 'ліки', 'pharmacy', 'краса',  'аптека', 'аптеки']},
        {'name': 'Освіта', 'type': 'EXPENSE', 'keywords': ['курси', 'навчання', 'книги', 'освіта', 'udemy']},
        {'name': 'Зняття готівки', 'type': 'EXPENSE', 'keywords': ['зняття готівки', 'навчання', 'книги', 'освіта', 'udemy']},
        {'name': 'Інше', 'type': 'EXPENSE', 'keywords': []}, 

        
        {'name': 'Зарплата', 'type': 'INCOME', 'keywords': ['зарплата', 'salary', 'заробітна']},
        {'name': 'Надходження з інших карт', 'type': 'INCOME', 'keywords': ['зарахування переказу', 'переказ', 'зарахування']},
        {'name': 'Фріланс', 'type': 'INCOME', 'keywords': ['freelance', 'upwork', 'фріланс']},
        {'name': 'Подарунки', 'type': 'INCOME', 'keywords': ['подарунок', 'gift']},
        {'name': 'Стипендія', 'type': 'INCOME', 'keywords': ['стипендія', 'scholarship']},
        {'name': 'Інший дохід', 'type': 'INCOME', 'keywords': []}, 
    ]
    
    for cat_data in default_categories:
        Category.objects.update_or_create(
            user=user,
            name=cat_data['name'],
            defaults={
                'type': cat_data['type'],
                'keywords': cat_data['keywords']
            }
        )
