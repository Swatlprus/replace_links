import re
import os
import datetime
import time
from pathlib import Path
from environs import Env
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from .forms import MailingForm
from django.conf import settings
from django.http import HttpResponseRedirect
from yourls import YOURLSClient, YOURLSKeywordExistsError, YOURLSNoLoopError


def check_links(el_tag, field_name, yourls_token):
    filepath = os.path.join(settings.MEDIA_ROOT, 'files', 'check.txt')

    with open(filepath, 'wb+') as destination:  
        for chunk in field_name.chunks():
            destination.write(chunk)

    with open(destination.name, "r") as file_handler:
        code_letter = file_handler.read()

    links = []
    stop_links = ['http://www.w3.org/TR/REC-html40', 'http://schemas.microsoft.com/office/2004/12/omml',
                    'https://l.ertelecom.ru/vkdigest', 'https://l.ertelecom.ru/tgdigest',
                    'https://l.ertelecom.ru/220415digestrutube']
    
    
    # Находим все ссылки в исходном коде
    source_links = re.findall(r'(https?://\S+")', code_letter)
    for source_link in source_links:
        source_link = source_link.replace('"', '')
        if source_link not in stop_links:
            links.append(source_link)


    # Оставляем только уникальные ссылки
    links = sorted(set(links), key=links.index)
    message_log = []

    if len(links) == 0:
        message_log.append('В коде письма ссылки не найдены.')
        status_yourls = False
    else:
        links_with_utm = {}
        for count, link in enumerate(links, start=1):
            yourls = YOURLSClient('http://l.ertelecom.ru/yourls-api.php', signature=yourls_token)
            status_yourls = True
            try:
                yourls_link = yourls.shorten(link, keyword=f'{el_tag}{count}')
                links_with_utm[link] = yourls_link.shorturl
            except YOURLSKeywordExistsError:
                status_yourls = False
                message_log.append('Короткий адрес уже используется или зарезервирован.')
            except YOURLSNoLoopError:
                status_yourls = False
                message_log.append('В письме есть ссылки, которые уже сокращены.')
    context = [status_yourls, code_letter, links_with_utm, message_log]
    return context


def work_links(code_letter, links_with_utm, google_tag, event, cn_tag, cs_tag, ec_tag, ea_tag, el_tag, yourls_token):
    message_log = []
    # Удаляем из письма лишний код сверху письма
    index_start = code_letter.find('<div class=WordSection1>')
    index_end = code_letter.find('<div align=center>')
    code_letter_utm = code_letter[:index_start] + code_letter[index_end:]
    code_letter_utm = code_letter_utm.replace('<p class=MsoNormal><o:p>&nbsp;</o:p></p>', '')

    # Меняем обычные ссылки на сокращенные
    for link, link_utm in links_with_utm.items():
        code_letter_utm = code_letter_utm.replace(link, link_utm)

    # Генерируем Google Pixel
    google_url = f'http://www.google-analytics.com/collect?v=1&tid={google_tag}&t=' \
                    f'{event}&cid=|UNIQID|&cn={cn_tag}&cs={cs_tag}&ec={ec_tag}&ea=' \
                    f'{ea_tag}&el={el_tag} '

    # Сокращаем Google Pixel
    yourls = YOURLSClient('http://l.ertelecom.ru/yourls-api.php', signature=yourls_token)
    short_google_url = yourls.shorten(google_url, keyword=f'{el_tag}pixel')
    code_google_pixel = '</td><img src=' + short_google_url.shorturl + ' width=1 height=1>'

    # Вставляем Google Pixel
    index_td = code_letter_utm.rfind('</td>')
    if index_td != -1:
        code_letter_utm = code_letter_utm[:index_td] + code_google_pixel + code_letter_utm[index_td+5:]
    else:
        message_log.append('Программа не смогла вставить Google Pixel в письмо. Остальные ссылки сокращены и сохранены в новое письмо.')

    # Вставляем результат в новый файл
    now = datetime.datetime.now()
    name_with_date = now.strftime("%d.%m.%Y_%H-%M-%S")
    filepath = os.path.join(settings.MEDIA_ROOT, 'html', f'email_{name_with_date}.html')
    folder_html = os.path.join(settings.MEDIA_ROOT, 'html')
    Path(folder_html).mkdir(parents=True, exist_ok=True)
    with open(filepath, "w+", encoding='utf-8') as file:
        file.write(code_letter_utm)
        file.close()

    message_log.append('Файл обработан. Он сохранится в новом файле.')
    print('Файл обработан. Он сохранится в новом файле.')

    if os.path.exists(filepath):
        with open(filepath, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/html")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(filepath)
            return render(response, 'download.html')
    else:
        return redirect('/error/')
    

def download(request, file1):
    return render(request, 'download.html', {'file1': file1})


def upload_mailing(request):
    if request.method == 'POST':
        form = MailingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            env = Env()
            env.read_env()
            yourls_token = env("YOURLS_TOKEN")
            print(f'yourls_token: {yourls_token}')

            el_tag = form.cleaned_data['el_tag']
            field_name = form.cleaned_data['field_name']

            status_yourls, code_letter, links_with_utm, message_log = check_links(el_tag, field_name, yourls_token)
            if status_yourls:
                google_tag = form.cleaned_data['google_tag']
                event = form.cleaned_data['event']
                cn_tag = form.cleaned_data['cn_tag']
                cs_tag = form.cleaned_data['cs_tag']
                ec_tag = form.cleaned_data['ec_tag']
                ea_tag = form.cleaned_data['ea_tag']
                work_links(code_letter, links_with_utm, google_tag, event, cn_tag, cs_tag, ec_tag, ea_tag, el_tag, yourls_token)
            else:
                return render(request, 'download.html', {'message_log': message_log})
    else:
        form = MailingForm
    return render(request, 'upload.html', {'form':form})