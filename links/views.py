import re
import os
import datetime
import requests

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

from pathlib import Path
from yourls import YOURLSClient, YOURLSKeywordExistsError, YOURLSNoLoopError
from .forms import MailingForm


def home(request):
    return render(request, 'links/home.html')


def download(request, filename):
    filepath = os.path.join(settings.MEDIA_ROOT, 'html', filename)
    with open(filepath, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/html")
        response['Content-Disposition'] = f'inline; filename= \
                        {os.path.basename(filepath)}'
        return response


def read_letter_code(field_name):
    filepath = os.path.join(settings.MEDIA_ROOT, 'files', 'check.txt')
    with open(filepath, 'wb+') as destination:
        for chunk in field_name.chunks():
            destination.write(chunk)

    with open(destination.name, "r", encoding='cp1251') as file_handler:
        letter_code = file_handler.read()

    return letter_code


def search_links(letter_code, stop_links):
    links = []
    error_log = []
    pixels = True
    source_links = re.findall(r'(https?://\S+")', letter_code)
    for source_link in source_links:
        source_link = source_link.replace('"', '')
        google_pixel = re.findall(r'(https:\/\/l.ertelecom.ru\/\S*pixel\S*)',
                                  source_link)
        if len(google_pixel) == 1:
            letter_code = letter_code.replace(google_pixel[0], '')
        elif len(google_pixel) > 1:
            pixels = False
            error_log.append('В коде письма есть несколько ссылок Pixel.')
        else:
            if source_link not in stop_links:
                links.append(source_link)
    links = sorted(set(links), key=links.index)
    return links, pixels, error_log


def check_links(el_tag, field_name, yourls, stop_links):
    letter_code = read_letter_code(field_name, stop_links)
    links, pixels, error_log = search_links()
    links_with_utm = {}
    if len(links) == 0:
        error_log.append('В коде письма ссылки не найдены.')
        status_yourls = False
    else:
        for count, link in enumerate(links, start=1):
            status_yourls = True
            try:
                yourls_link = yourls.shorten(link, keyword=f'{el_tag}_{count}')
                links_with_utm[link] = yourls_link.shorturl
            except YOURLSKeywordExistsError:
                status_yourls = False
                error_log.append('Короткий адрес уже используется.')
            except YOURLSNoLoopError:
                status_yourls = False
                error_log.append('В письме уже есть сокращенные ссылки.')
            except requests.HTTPError:
                status_yourls = False
    context = [status_yourls, letter_code, links, links_with_utm, error_log,
               pixels]
    return context


def clear_letter_code(letter_code, links_with_utm, short_link_google):
    message_log = []
    # Удаляем из письма лишний код сверху письма
    index_start = letter_code.find('<div class=WordSection1>')
    index_end = letter_code.find('<div align=center>')
    letter_code_utm = letter_code[:index_start] + letter_code[index_end:]
    letter_code_utm = letter_code.replace('<p class=MsoNormal><o:p>&nbsp; \
                                          </o:p></p>', '')

    # Меняем обычные ссылки на сокращенные
    for link, link_utm in links_with_utm.items():
        letter_code_utm = letter_code_utm.replace(link, link_utm)

    # Сокращаем Google Pixel
    code_google_pixel = '</td><img src=' + short_link_google + ' width=1 \
                                                            height=1>'

    # Вставляем Google Pixel
    index_td = letter_code_utm.rfind('</td>')
    if index_td != -1:
        letter_code_utm = letter_code_utm[:index_td] + code_google_pixel + \
            letter_code_utm[index_td+5:]
    else:
        message_log.append('Не смогли вставить Google Pixel в письмо. \
                            Остальные ссылки сокращены и сохранены в письмо.')
    return letter_code_utm, message_log


def generate_letter_code(letter_code, links_with_utm, short_link_google):
    letter_code_utm, message_log = clear_letter_code(letter_code,
                                                     links_with_utm,
                                                     short_link_google)
    now = datetime.datetime.now()
    name_with_date = now.strftime("%d.%m.%Y_%H-%M-%S")
    filename = f'email_{name_with_date}.html'
    filepath = os.path.join(settings.MEDIA_ROOT, 'html', filename)
    folder_html = os.path.join(settings.MEDIA_ROOT, 'html')
    Path(folder_html).mkdir(parents=True, exist_ok=True)

    with open(filepath, "w+", encoding='cp1251') as file:
        file.write(letter_code_utm)
        file.close()

    message_log.append('Файл обработан успешно')
    context = [filename, message_log]
    return context


def succes(request):
    return render(request, 'links/succes.html')


def upload_mailing(request):
    if request.method == 'POST':
        form = MailingForm(request.POST, request.FILES)
        if form.is_valid():
            el_tag = form.cleaned_data['el_tag']
            field_name = request.FILES['html_letter']
            yourls = YOURLSClient('https://l.ertelecom.ru/yourls-api.php',
                                  signature=settings.YOURLS_TOKEN)

            status_yourls, letter_code, links, links_with_utm, error_log, \
                pixels = check_links(el_tag, field_name, yourls,
                                     settings.STOP_LINKS)
            if (status_yourls and pixels):
                google_tag = form.cleaned_data['google_tag']
                event = form.cleaned_data['event']
                cn_tag = form.cleaned_data['cn_tag']
                cs_tag = form.cleaned_data['cs_tag']
                ec_tag = form.cleaned_data['ec_tag']
                ea_tag = form.cleaned_data['ea_tag']

                # Генерируем Google Pixel
                google_url = f'http://www.google-analytics.com/collect?v= \
                    1&tid={google_tag}&t={event}&cid=|UNIQID|&cn={cn_tag}& \
                        cs={cs_tag}&ec={ec_tag}&ea={ea_tag}&el={el_tag}'
                short_google_url = yourls.shorten(google_url,
                                                  keyword=f'{el_tag}pixel')
                short_link_google = short_google_url.shorturl

                filename, message_log = generate_letter_code(letter_code,
                                                             links_with_utm,
                                                             short_link_google)

                return render(request, 'links/succes.html',
                              {'filename': filename,
                               'message_log': message_log,
                               'error_log': error_log,
                               'links': links,
                               'links_with_utm': links_with_utm,
                               'google_url': google_url,
                               'short_google_url': short_link_google})

            else:
                return render(request, 'links/succes.html',
                              {'error_log': error_log})
    else:
        form = MailingForm
    return render(request, 'links/mailing.html', {'form': form})
