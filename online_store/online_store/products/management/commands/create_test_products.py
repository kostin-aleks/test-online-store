"""
Manage command to create test categories
"""

from django.core.management.base import BaseCommand
from django.conf import settings

from djmoney.money import Money

from online_store.products.models import Product, SubCategory

PRODUCT_DATA = [
    {
        'name': 'Каска Salewa Pura S/M сірий 1823',
        'description': '''Шолом Salewa Pura Helmet є надійним та універсальним. Він гарантує необхідний захист під час скелелазіння та активного відпочинку. Добре регулюється та легко підлаштовується під індивідуальні особливості. Підійде як для жінок, так і для чоловіків. Є і дитячі варіації.''',
        'details': ['міцна і зручна внутрішня оболонка із пінополістиролу',
                    'регулюється та легко підлаштовується під індивідуальні особливості',
                    '4 великі отвори для вентиляції',
                    'зручна у догляді оббивка'],
        'features': {'Виробник': 'Salewa', 'Колір': 'Сірий'},
        'technical_features': {
            'Вага': '310 г',
            'Розміри': ['S/M (48-50 см)', 'L/XL (56-62 см)'],
            'Стати': 'Unisex'
        },
        'price': 2940,
        'category': 'kaski'
    },
    {
        'name': 'Каска Singing Rock Plasma Work AQ Blue',
        'description': '''Робоча каска Plasma Work бренду Singing Rock Singing Rock Plasma Work - легка та міцна каска для промальпу, будівельних та висотно-монтажних робіт. Вона легко регулюється для комфортної посадки на голові та компактно складається для перевезення.
        ''',
        'details': ['10 вентиляційних отворів',
                    'Кріплення під усі види налобних ліхтарів',
                    'Усередині знімна підкладка - зручно мити і чистити',
                    'Сумісна зі спеціальним візором та навушниками'],
        'features': {'Виробник': 'Singing Rock', 'Колір': 'Синій'},
        'technical_features': {
            'Вага': '380 г',
            'Розміри': ['один універсальний, на окружність голови 51-62 см'],
            'Сертифікація': '(CE) EN 397',
            'Матеріали': 'поліпропілен'
        },
        'price': 8228,
        'category': 'kaski'
    },
    {
        'name': 'Карабін First Ascent Goliath 50 kN 2023',
        'description': '''Карабін First Ascent Goliath 50 kN 2023''',
        'details': [],
        'features': {'Виробник': 'First Ascent'},
        'technical_features': {},
        'price': 385,
        'category': 'karabiny'
    },
    {
        'name': 'Карабін Maillon Rapid 10,0 1 / 2RD IN CE D10мм дельта нержавейка 2014',
        'description': '''Карабін Maillon Rapid 10,0 1 / 2RD IN CE D10мм дельта нержавейка 2014''',
        'details': [],
        'features': {'Виробник': 'Rapid'},
        'technical_features': {},
        'price': 839,
        'category': 'karabiny'
    },
    {
        'name': 'Затиск кроль Petzl Basic B18 AAA 2019',
        'description': '''Затиск кроль Petzl Basic B18 AAA 2019''',
        'details': [],
        'features': {'Виробник': 'Petzl'},
        'technical_features': {},
        'price': 2856,
        'category': 'zazhimy'
    },
    {
        'name': 'Жумар правий Black Diamond INDEX Ascender Right',
        'description': '''Жумар Black Diamond Index Ascender - пристрій для підйому мотузкою, сконструйований для роботи на важких ділянках, у важких умовах протягом усього маршруту в будь-яку погоду. Новий курок затискача дозволяє легко пересувати його, що додає швидкості та маневреності. Агресивні зубці для надійного фіксування на зледенілій мотузці. Є можливість працювати з широким діапазоном мотузок, лівою чи правою (різні модифікації) рукою.''',
        'details': ['Робота з затискачем вказівним пальцем для швидкого пересування мотузкою',
                    'Ергономічна рукоятка',
                    'Полегшена конструкція',
                    'Агресивні зубці для роботи на зледенілій мотузці',
                    'Велика провушина для карабіна'],
        'features': {'Виробник': 'Black Diamond'},
        'technical_features': {
            'Вага': '200 г',
            'Для мотузок': 'діаметром від 8 до 13 мм',
            'Сертифікація': 'CE та UIAA'},
        'price': 3731,
        'category': 'zazhimy'
    },
    {
        'name': 'Намет Hannah Hawk 2 Treetop 2022',
        'description': '''Намет Hannah Hawk 2 Treetop 2022''',
        'details': [],
        'features': {'Виробник': 'Hannah', 'Кількість тамбурів': 1, 'Колір': 'Зелений'},
        'technical_features': {
            'Вага': '2 - 2,5 кг',
            'Вентиляційні клапани тенту': 2,
            'Місткість': 'Двомісна',
            'Водостійкість дна, мм': 7000,
            'Водостійкість тенту, мм': 5000,
            'Кількість входів': 'Один',
            'Кількість спальних відділень': 1,
            'Матеріал дуг': 'Алюміній',
            'Матеріал каркасу (дуги)': 'Dural – Дюралюміній',
            'Розміри внутрішньої частини': '125/90 x 205 x 100 см',
            'Розміри з тентом': '135 x 295 x 115 см',
            'Сезонність': 'Весна, Літо, Осінь',
            'Колір тенту': 'Зелений'},
        'price': 15036,
        'category': 'palatki'
    },
    {
        'name': 'Спальник пуховий Turbat Kuk 500 Blue - синій - 185',
        'description': '''Нова серія спальних мішків від Turbat задовільнить найвимогливіших користувачів, які потребують максимального комфорту при мінімальному об'ємі та вазі. Легкий і надзвичайно практичний трисезонний спальник для використання у міжсезонний період. Хороші термоізоляційні властивості досягаються завдяки натуральному матеріалу наповнювача - гусячому пуху високого класу. Такий наповнювач перевершує усі синтетичні аналоги за показниками теплоізоляції на одиницю ваги. Добре компресується у зручний мішок. Компактна та практична форма, легкість у використанні є перевагами даної моделі.

Призначення: гірський туризм, піший туризм, кемпінг, велотуризм, альпінізм.''',
        'details': ['компактна модель',
                    'трисезонний- анатомічна форма',
                    'широкий комір всередині спальника для додаткового теплозбереження',
                    'подовжена центральна блискавка',
                    'збільшений простір для ніг (footbox)',
                    'додатковий мішечок для довготривалого зберігання',
                    'добре компресується',
                    'пружність пуху FP 750, показники підтверджені сертифікатом швейцарського інституту IDFL Europe AG'],
        'features': {'Виробник': 'Turbat', 'Стан': 'Новий', 'Колір': 'Синій'},
        'technical_features': {
            'Температурний режим': '(Comfort / Limit / Extreme): 0°C / -6°C / -23°C',
            'Cертифікований по стандарту': 'ISO 23537-1',
            'Довжина': '215 см',
            'Ширина верхньої частини (в плечах)': '85 см',
            'Ширина в нижній частині': '58 см',
            'Вага наповнювача': '500 г',
            'Вага спальніка': '920 г',
            'Розмір у компресійному чохлі': '20 см x 20 см',
            'Загальна вага з компресійним чохлом': '980 г',
            'Зовнішній матеріал': '20D Нейлон Rip-stop DWR 38 г/м2',
            'Внутрішній матеріал': '20D Нейлон',
            'Наповнювач': 'український гусячий пух 750FP'
        },
        'price': 11995,
        'category': 'spalnye-meshki'
    },
    {
        'name': 'Байдарка Neris Alu-2 Standart 2022',
        'description': '''''',
        'details': [],
        'features': {'Виробник': 'Neris'},
        'technical_features': {},
        'price': 35190,
        'category': 'bajdarki'
    },
]


class Command(BaseCommand):
    """
    This manage command creates test categories
    """
    help = """Create test categories."""

    def handle(self, *args, **kwargs):

        for item in PRODUCT_DATA:
            print(f"NAME: {item['name']}")
            product = Product.objects.filter(name=item['name']).first()
            if product is None:
                product = Product.objects.create(
                    name=item['name'],
                    description=item['description'],
                    details=item['details'],
                    features=item['features'],
                    technical_features=item['technical_features'],
                    price=Money(item['price'], 'UAH'),
                    subcategory=SubCategory.objects.get(slug=item['category']),
                    moderation_status='approved',
                )
            else:
                product.name = item['name']
                product.description = item['description']
                product.details = item['details']
                product.features = item['features']
                product.technical_features = item['technical_features']
                product.price = Money(item['price'], 'UAH')
                product.subcategory = SubCategory.objects.get(slug=item['category'])
                product.moderation_status = 'approved'
                product.save()



