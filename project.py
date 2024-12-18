import csv
import os
import re
from fuzzywuzzy import fuzz, process
from logger_config import setup_log


class PriceMachine():

    def __init__(self):
        self.data = []
        self.logger = setup_log()  # Настройка логирования
        # self.result = ''
        # self.name_length = 0

    def load_prices(self, file_path='.'):
        '''
            Сканирует указанный каталог. Ищет файлы со словом price в названии.
            В файле ищет столбцы с названием товара, ценой и весом.
            Допустимые названия для столбца с товаром:
                товар
                название
                наименование
                продукт

            Допустимые названия для столбца с ценой:
                розница
                цена

            Допустимые названия для столбца с весом (в кг.)
                вес
                масса
                фасовка
        '''
        self.logger.info('Загрузка файлов из каталога: %s', file_path)

        for filename in os.listdir('file_path'):
            # print(f"Проверка файла: {filename}")  # выводим все имена файлов
            self.logger.debug(f"Проверка файла: %s", filename)
            if 'price' in filename and filename.endswith('.csv'):
                filepath = os.path.join(file_path, filename)
                self.replace_with_semicolon(filepath)  # Замена запятой на точку с запятой
                with open(filepath, encoding='utf-8') as file:
                    reader = csv.reader(file, delimiter=';')
                    headers = next(reader)

                    product_idx, price_idx, weight_idx = self._search_product_price_weight(headers)

                    for r in reader:
                        if product_idx is not None and price_idx is not None and weight_idx is not None:
                            product_name = r[product_idx]
                            price = float(r[price_idx])
                            weight = float(r[weight_idx])
                            if weight <= 0:
                                self.logger.warning('Пропуск товара %s с некорректным весом: %s', product_name, weight)
                                continue

                            price_kg = price / weight
                            self.data.append({
                                'name': product_name,
                                'price': price,
                                'file_path': filename,
                                'weight': weight,
                                'price_kg': price_kg,
                            })
        self.logger.info('Загрузка цен завершена. Загружено позиций: %d', len(self.data))
        return len(self.data)

    def replace_with_semicolon(self, file_path):
        """Заменяет все запятые на точку с запятой в CSV-файле"""
        self.logger.info('Обработка файла: %s', file_path)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Заменяем все запятые на точку с запятой, игнорируя строки с кавычками
        content = re.sub(r'(?<!")\,(?!")', ';', content)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

        self.logger.debug('Файл %s успешно обработан.', file_path)

    def _search_product_price_weight(self, headers):

        product_headers = ["название", "продукт", "товар", "наименование"]
        price_headers = ["цена", "розница"]
        weight_headers = ["фасовка", "масса", "вес"]

        product_idx = next((i for i, h in enumerate(headers) if h in product_headers), None)
        price_idx = next((i for i, h in enumerate(headers) if h in price_headers), None)
        weight_idx = next((i for i, h in enumerate(headers) if h in weight_headers), None)

        return product_idx, price_idx, weight_idx

    def export_to_html(self, fname='output.html'):
        """Экспортируем данные в HTML-файл."""

        result = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Позиции продуктов</title>
        </head>
        <body>
            <table>
                <tr>
                    <th>Номер</th>
                    <th>Название</th>
                    <th>Цена</th>
                    <th>Фасовка</th>
                    <th>Файл</th>
                    <th>Цена за кг.</th>
                </tr>
        '''
        for index, item in enumerate(self.data, start=1):
            # Формируем таблицу
            result += f'''
                    <tr><td>{index}</td><td>{item['name']}</td><td>{item['price']:.2f}</td><td>{item['weight']}</td><td>{item['file_path']}</td><td>{item['price_kg']:.2f}</td></tr>'''

        result += '''
                    </table>
                </body>
                </html>
                '''

        with open(fname, 'w', encoding='utf-8') as file:
            file.write(result)
        self.logger.info('Данные успешно экспортированы в %s.', fname)
        return f'Данные успешно импортированы в {fname}.'

    def find_text(self, text):
        ''' Ищет и возвращает продукты с названиями, похожими на введённый текст.

    Проверяет на наличие опечаток в названиях, приводя текст к нижнему регистру и удаляя лишние пробелы.
    Использует алгоритм сравнения строк для определения сходства названии продуктов с введённым текстом.
    '''

        text = text.lower().strip()  # Приводим текст к нижнему регистру и удаляем пробелы

        # Получаем названия продуктов для поиска
        product_names = [item['name'].strip().lower() for item in self.data]

        # Получаем подходящие строки по схожести
        matched_items = process.extract(text, product_names, limit=None, scorer=fuzz.ratio)

        # Получаем названия, которые имеют схожесть выше 60
        matched_names = {match for match, score in matched_items if score > 60}

        # Проверяем наличие соответствующих товаров
        results = [item for item in self.data if
                   re.search(r'\b' + re.escape(text) + r'\b', item['name'].lower()) or item[
                       'name'].strip().lower() in matched_names]

        return sorted(results, key=lambda x: x['price_kg'])


#     Логика работы программы
if __name__ == '__main__':

    pm = PriceMachine()
    print(pm.load_prices('file_path'))
    print(pm.export_to_html())

    while True:
        search_text = input('Введите текст для поиска или "exit" для выхода: ')
        if search_text == 'exit':
            pm.logger.info('Завершаем работу')
            print('Завершаем работу')
            break

        found_items = pm.find_text(search_text)

        if found_items:
            pm.logger.info('Найдено %d позиций по запросу "%s"', len(found_items), search_text)
            print(f'Найдено {len(found_items)} позиций:')
            print('№\tНаименование\t\t\t\t\t\t\tЦена\t Вес\tФайл\t\t\tЦена за кг.')

            for index, item in enumerate(found_items, start=1):
                # Форматируем вывод с выравниванием столбцов
                print(f'{index:<3}\t'
                      f'{item["name"]:<35}\t'
                      f'{item["price"]:>10.2f}\t'  # Цена, выравнивание по правому краю
                      f'{item["weight"]:>5}\t'  # Вес, выравнивание по правому краю
                      f'{item["file_path"]:<15}\t'
                      f'{item["price_kg"]:>8.2f}')  # Цена за кг, выравнивание по правому краю

        else:
            pm.logger.info('Ничего не найдено для запроса "%s"', search_text)
            print('Ничего не найдено')
