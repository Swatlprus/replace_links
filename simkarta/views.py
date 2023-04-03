import os
import sys
import requests
from pathlib import Path
from environs import Env
from .forms import SimkartaForm
from django.conf import settings
from docxtpl import DocxTemplate
from json import JSONDecodeError
from transliterate import translit
from django.shortcuts import render
from django.http import HttpResponse
from requests.auth import HTTPBasicAuth


def simkarta(request):
    if request.method == 'POST':
        form = SimkartaForm(request.POST)       
        error_log = []
        message_log = []

        if form.is_valid():
            form.save()
            env = Env()
            env.read_env()

            id_ticket = form.cleaned_data['id_ticket']
            jira_login = env("JIRA_LOGIN")
            jira_password = env("JIRA_PASSWORD")
            auth = HTTPBasicAuth(jira_login, jira_password)

            # Составляем параметры для запроса
            params = {'fields': ['customfield_38701', 'customfield_27301', 'customfield_11904', 'customfield_44000',
                                'customfield_25511', 'customfield_44001', 'customfield_24001', 'customfield_18802',
                                'customfield_14304', 'customfield_44100', 'customfield_45001', 'customfield_25504',
                                'customfield_27300', 'customfield_30702', 'customfield_20708', 'customfield_44901']}

            # создаем GET запрос
            try:
                fullReq = requests.get('https://ticket.ertelecom.ru/rest/api/2/issue/' + id_ticket, params=params,
                                 auth=auth).json()
            except JSONDecodeError as err:
                print(err.__str__(), file=sys.stderr)
                error_log.append(f'Одно из полей в тикете {id_ticket} не заполнено.')
                return render(request, 'simkarta/succes.html', {'message_log': message_log, 'error_log': error_log})

            if fullReq != None:
                fioPerson = fullReq['fields']['customfield_38701']  # ФИО
                pasportPerson = fullReq['fields']['customfield_27301']  # Серия и номер паспорта
                fullAdressPerson = fullReq['fields']['customfield_11904']  # Полный адрес
                cityPerson = fullReq['fields']['customfield_44000']  # Город
                ufmsPerson = fullReq['fields']['customfield_25511']  # Кем выдан
                codeUfmsPerson = int(fullReq['fields']['customfield_44001'])  # Код подразделения, кто выдал паспорт
                positionPerson = fullReq['fields']['customfield_24001'][0]  # Должность сотрудника
                otdelPerson = fullReq['fields']['customfield_18802'][0]  # Отдел сотрудника
                cityCompanyPerson = fullReq['fields']['customfield_14304'][0]  # Город филиала
                typeSimkarta = fullReq['fields']['customfield_25504']['value']  # Тип симкарты
                numberSimkarta = fullReq['fields']['customfield_27300']  # Номер симкарты
                operatorSimkarta = fullReq['fields']['customfield_30702']['value']  # Оператор
                tarifSimkarta = fullReq['fields']['customfield_20708']  # Тариф симкарты
                dateBornPersonTemp = fullReq['fields']['customfield_44100'] # Дата рождения
                datePassportPersonTemp = fullReq['fields']['customfield_45001'] # Дата выдачи паспорта
                limitSimkarta = int(fullReq['fields']['customfield_44901'])  # Лимит по симкарте

                listTemp = {fioPerson: 'ФИО', pasportPerson: 'Серия и номер паспорта', fullAdressPerson: 'Полный адрес',
                            cityPerson: 'Город', ufmsPerson: 'Кем выдан', codeUfmsPerson: 'Код подразделения',
                            positionPerson: 'Должность сотрудника', otdelPerson: 'Отдел сотрудника',
                            cityCompanyPerson: 'Город филиала', typeSimkarta: 'Тип симкарты',
                            numberSimkarta: 'Номер симкарты', operatorSimkarta: 'Оператор симкарты',
                            tarifSimkarta: 'Тариф симкарты', dateBornPersonTemp: 'Дата рождения',
                            datePassportPersonTemp: 'Дата выдачи паспорта '}

                for item in listTemp.keys():
                    if item is None:
                        error_log.append(f'У тикета {id_ticket} есть пустое значение поля {listTemp.get(item)}')

                # Составление нормализованной даты рождения

                dateBornList = dateBornPersonTemp.split('-')  # Список из чисел
                dateBornListReversed = list(reversed(dateBornList))  # Переворачиваем список
                dateBornPerson = str(dateBornListReversed[0])  # Присваем переменной первое число
                # Цикл для составлия полной даты
                for k in dateBornListReversed[1:]:
                    dateBornPerson += '.' + k

                # Составление нормализованной даты выдачи паспорта
                datePassportPersonList = datePassportPersonTemp.split('-')  # Список из чисел
                datePassportPersonListReversed = list(reversed(datePassportPersonList))  # Переворачиваем список
                datePassportPerson = str(datePassportPersonListReversed[0])  # Присваем переменной первое число
                # Цикл для составлия полной даты
                for i in datePassportPersonListReversed[1:]:
                    datePassportPerson += '.' + i

                # Дополнительный текст
                if typeSimkarta == 'Дополнительная':
                    textDopoln = 'Прошу ежемесячно удерживать стоимость услуг Оператора по SIM-карте из моей заработной платы'
                elif typeSimkarta == 'Производственная':
                    textDopoln = ''
                elif typeSimkarta == 'Основная' and limitSimkarta > 0:
                    textDopoln = 'Установленный ежемесячный Лимит возмещения затрат составляет ' + str(limitSimkarta) + \
                                ' рублей. В случае, если фактическая стоимость услуг Оператора по SIM-карте за месяц ' \
                                'превысит установленный Лимит, прошу ежемесячно, начиная с даты настоящего Заявления, ' \
                                'удерживать из моей заработной платы сумму превышения.'
                elif typeSimkarta == 'Основная':
                    textDopoln = 'Установленный ежемесячный Лимит возмещения затрат составляет 0 рублей. Прошу ежемесячно ' \
                                'удерживать стоимость услуг Оператора по SIM-карте из моей заработной платы'
                else:
                    error_log.append('Ошибка с полем Тип-симкарты')

                if len(error_log) > 0:
                    return render(request, 'simkarta/succes.html', {'message_log': message_log, 'error_log': error_log})
                else:
                    # Начинаем работать с docx заявлением
                    filepath = os.path.join('static', 'zayva.docx')
                    template = DocxTemplate(filepath)

                    # Переменные
                    context = {
                        'numberTicket': id_ticket,
                        'fioPerson': fioPerson,
                        'pasportPerson': pasportPerson,
                        'fullAdressPerson': fullAdressPerson,
                        'cityPerson': cityPerson,
                        'ufmsPerson': ufmsPerson,
                        'codeUfmsPerson': codeUfmsPerson,
                        'positionPerson': positionPerson,
                        'otdelPerson': otdelPerson,
                        'cityCompanyPerson': cityCompanyPerson,
                        'dateBornPerson': dateBornPerson,
                        'datePassportPerson': datePassportPerson,
                        'typeSimkarta': typeSimkarta,
                        'numberSimkarta': numberSimkarta,
                        'operatorSimkarta': operatorSimkarta,
                        'tarifSimkarta': tarifSimkarta,
                        'textDopoln': textDopoln,
                    }

                    # Рендеринг заявления
                    template.render(context)
                    ru_filename = f'Заявление_для_{fioPerson}_для_сим-карты.docx'
                    filename = translit(ru_filename, language_code='ru', reversed=True)
                    filepath = os.path.join(settings.MEDIA_ROOT, 'docx', filename)
                    folder_docx = os.path.join(settings.MEDIA_ROOT, 'docx')
                    Path(folder_docx).mkdir(parents=True, exist_ok=True)
                    template.save(filepath)

                    message_log.append(f'Заявление для {fioPerson} создано')
                    if os.path.exists(filepath):
                        return render(request, 'simkarta/succes.html', {'filename': filename, 'message_log': message_log, 'error_log': error_log})
                    else:
                        error_log.append('Мы не нашли сгенерированный файл')
                        return render(request, 'simkarta/succes.html', {'message_log': message_log, 'error_log': error_log})
        else:
            error_log.append('Некорректно заполнено поле тикета, пожалуйста попробуйте снова')
            return render(request, 'simkarta/succes.html', {'error_log': error_log})
    else:
        form = SimkartaForm
    return render(request, 'simkarta/simkarta.html', {'form':form})


def simkarta_succes(request):
    return render(request, 'simkarta/simkarta.html')


def simkarta_download(request, filename):
    filepath = os.path.join(settings.MEDIA_ROOT, 'docx', filename)
    with open(filepath, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(filepath)
        return response
