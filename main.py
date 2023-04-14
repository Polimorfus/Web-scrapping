import requests
from requests_html import HTMLSession, HTMLResponse
import re
from bs4 import BeautifulSoup
from fake_headers import Headers
import json


def get_headers():
    return Headers(browser='chrome', os='win').generate()


def process_vacancy(link: str) -> dict:
    # Получаем текст страницы с объявлением
    vacancy_text = requests.get(link, headers=get_headers()).text
    vacancy_soup = BeautifulSoup(vacancy_text, 'lxml')
    vacancy_desc_tag = vacancy_soup.find('div', class_='vacancy-description')

    # Ищем по шаблону
    find_pattern = r'(Django|Flask)'
    try:
        ret = re.search(find_pattern, vacancy_desc_tag.text, flags=re.IGNORECASE)
    except AttributeError:
        print(f'Ошибка получения данных по вакансии, пустой текст описания: {link}')
        return dict()

    if ret is not None:
        try:
            vacancy_title_tag = vacancy_soup.find('div', class_='vacancy-title')
            vacancy_title_text = vacancy_title_tag.find('h1', class_='bloko-header-section-1').text
            vacancy_salary_tag = vacancy_title_tag.find('span',
                                                        class_='bloko-header-section-2 bloko-header-section-2_lite')

            vacancy_company_tag = vacancy_soup.find('div', class_='vacancy-company-redesigned')
            vacancy_company_name = vacancy_company_tag.find('span', class_='vacancy-company-name').text

            err = 0
            try:
                vacancy_company_location = vacancy_company_tag.find('p', {'data-qa': 'vacancy-view-location'}).text
            except AttributeError:
                err = 1

            # Попытка получить данные по другому тегу
            if err == 1:
                try:
                    vacancy_company_location = \
                    vacancy_company_tag.find('span', {'data-qa': 'vacancy-view-raw-address'}).text.split(',')[0]
                except:
                    print(f'Ошибка получения "города" по вакансии: {link}')
                    vacancy_company_location = ''

            return {'title': vacancy_title_text,
                    'link': link,
                    'salary': vacancy_salary_tag.text.replace(u'\xa0', ' '),
                    'company': vacancy_company_name.replace(u'\xa0', ' '),
                    'city': vacancy_company_location.replace(u'\xa0', ' ')
                    }

        except:
            print(f'Ошибка получения данных по вакансии: {link}')
            return dict()
    else:
        return dict()


def main():
    # Получаем текст главной страницы поиска

    ## Альтернативный вариант загрузки через requests_html
    # session = HTMLSession()
    # resp = session.get('https://spb.hh.ru/search/vacancy?text=python&area=1&area=2', headers=get_headers())
    # resp.html.render(sleep=5, keep_page=True)
    # main_page_text = resp.text

    main_page_text = requests.get(
        'https://spb.hh.ru/search/vacancy?text=python&area=1&area=2',
        headers=get_headers()).text

    main_soup = BeautifulSoup(main_page_text, 'lxml')
    div_main_tag = main_soup.find('div', id='a11y-main-content')

    results = []

    # Получаем список тегов с объявлениями
    div_list = div_main_tag.find_all('div', class_='serp-item')
    for div in div_list:
        # Ищем ссылку на объявление
        a_tag = div.find('a', class_='serp-item__title')
        vacancy_link = a_tag['href']

        print(f'Обработка вакансии: {vacancy_link}')
        vac_ret = process_vacancy(vacancy_link)
        if vac_ret != dict():
            results.append(vac_ret)

    # если результат не пустой, сохраняем в файл
    if len(results) > 0:
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False)


if __name__ == '__main__':
    main()

