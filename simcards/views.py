import os
import requests

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError

from pathlib import Path
from json import JSONDecodeError
from docxtpl import DocxTemplate
from transliterate import translit
from .forms import SimcardsForm


def format_raw_date(date):  # 2023-02-02 --> 02.02.2023
    dateBornList = date.split('-')
    dateBornListReversed = list(reversed(dateBornList))
    normal_date = str(dateBornListReversed[0])
    for k in dateBornListReversed[1:]:
        normal_date += '.' + k
    return normal_date


def add_extra_text(simcard_type, simcard_limit, error_log):
    if simcard_type == 'Дополнительная':
        extra_text = 'Прошу ежемесячно удерживать стоимость услуг Оператора \
            по SIM-карте из моей заработной платы'
    elif simcard_type == 'Производственная':
        extra_text = ''
    elif simcard_type == 'Основная' and simcard_limit > 0:
        extra_text = 'Установленный ежемесячный Лимит возмещения затрат \
                    составляет ' + str(simcard_limit) + ' рублей. В случае, \
                    если фактическая стоимость услуг Оператора по SIM-карте \
                    за месяц превысит установленный Лимит, прошу ежемесячно, \
                    начиная с даты настоящего Заявления, удерживать из моей \
                    заработной платы сумму превышения.'
    elif simcard_type == 'Основная':
        extra_text = 'Установленный ежемесячный Лимит возмещения затрат \
                    составляет 0 рублей. Прошу ежемесячно удерживать \
                    стоимость услуг Оператора по SIM-карте из моей \
                    заработной платы'
    else:
        error_log.append('Ошибка с полем Тип-симкарты')
    return extra_text, error_log


def validate_ticket(ticket_id, ticket, error_log):
    jira_ticket = {
        'ticket_id': ticket_id,
        'full_name': ticket['fields']['customfield_38701'],
        'passport': ticket['fields']['customfield_27301'],
        'adress': ticket['fields']['customfield_11904'],
        'city': ticket['fields']['customfield_44000'],
        'ufms': ticket['fields']['customfield_25511'],
        'ufms_code': int(ticket['fields']['customfield_44001']),
        'position': ticket['fields']['customfield_24001'][0],
        'department': ticket['fields']['customfield_18802'][0],
        'company_city': ticket['fields']['customfield_14304'][0],
        'simcard_type': ticket['fields']['customfield_25504']['value'],
        'simcard_number': ticket['fields']['customfield_27300'],
        'operator': ticket['fields']['customfield_30702']['value'],
        'tariff': ticket['fields']['customfield_20708'],
        'birth_date': ticket['fields']['customfield_44100'],
        'issue_date': ticket['fields']['customfield_45001'],
        'simcard_limit': int(ticket['fields']['customfield_44901'])}

    for key, value in jira_ticket.items():
        if value is None:
            error_log.append(f'У тикета {ticket_id} есть пустое значение поля \
                             {key}')
    return jira_ticket, error_log


def application_generation(request):
    if request.method == 'POST':
        form = SimcardsForm(request.POST)
        error_log = []
        message_log = []

        if form.is_valid():
            ticket_id = form.cleaned_data['ticket']
            auth = HTTPBasicAuth(settings.JIRA_LOGIN, settings.JIRA_PASSWORD)

            # Составляем параметры для запроса
            params = {'fields': ['customfield_38701', 'customfield_27301',
                                 'customfield_11904', 'customfield_44000',
                                 'customfield_25511', 'customfield_44001',
                                 'customfield_24001', 'customfield_18802',
                                 'customfield_14304', 'customfield_44100',
                                 'customfield_45001', 'customfield_25504',
                                 'customfield_27300', 'customfield_30702',
                                 'customfield_20708', 'customfield_44901']}

            # создаем GET запрос
            try:
                ticket = requests.get(f'https://ticket.ertelecom.ru/rest/api \
                                      /2/issue/{ticket_id}', params=params,
                                      auth=auth).json()
                ticket.raise_for_status()
            except JSONDecodeError:
                error_log.append(f'Одно из полей в тикете {ticket} \
                                 не заполнено.')
                return render(request, 'simcards/result.html',
                              {'message_log': message_log,
                               'error_log': error_log})
            except HTTPError:
                error_log.append('Не могу соединиться с JIRA')
                return render(request, 'simcards/result.html', {
                                        'message_log': message_log,
                                        'error_log': error_log
                                        })
            jira_ticket, error_log = validate_ticket(ticket_id, ticket,
                                                     error_log)
            birth_date = format_raw_date(jira_ticket['birth_date'])
            issue_date = format_raw_date(jira_ticket['issue_date'])
            extra_text, error_log = add_extra_text(
                                                jira_ticket['simcard_type'],
                                                jira_ticket['simcard_limit'],
                                                error_log)
            jira_ticket['birth_date'] = birth_date
            jira_ticket['issue_date'] = issue_date
            jira_ticket['extra_text'] = extra_text

            if len(error_log) > 0:
                return render(request, 'simcards/result.html', {
                                        'message_log': message_log,
                                        'error_log': error_log
                                        })

            # Начинаем работать с docx заявлением
            filepath = os.path.join('static', 'zayva.docx')
            application = DocxTemplate(filepath)
            application.render(jira_ticket)
            full_name = jira_ticket['full_name']
            ru_filename = f'Заявление_для_{full_name}_для_сим-карты.docx'
            filename = translit(ru_filename, language_code='ru', reversed=True)
            filepath = os.path.join(settings.MEDIA_ROOT, 'docx', filename)
            folder_docx = os.path.join(settings.MEDIA_ROOT, 'docx')
            Path(folder_docx).mkdir(parents=True, exist_ok=True)
            application.save(filepath)
            message_log.append(f'Заявление для {full_name} создано')
            return render(request, 'simcards/result.html', {
                                                    'filename': filename,
                                                    'message_log': message_log,
                                                    'error_log': error_log
                                                    })

        else:
            error_log.append('Некорректно заполнено поле тикета, \
                             пожалуйста попробуйте снова')
            return render(request, 'simcards/result.html',
                          {'error_log': error_log})
    else:
        form = SimcardsForm
    return render(request, 'simcards/simcards.html', {'form': form})


def display_results(request):
    return render(request, 'simcards/result.html')


def download_docx(request, filename):
    filepath = os.path.join(settings.MEDIA_ROOT, 'docx', filename)
    with open(filepath, 'rb') as fh:
        response = HttpResponse(fh.read(),
                                content_type="application/vnd.openxmlformats- \
                                officedocument.wordprocessingml.document")
        response['Content-Disposition'] = f'inline; \
                                        filename={os.path.basename(filepath)}'
        return response
