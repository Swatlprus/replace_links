import re
import os
import datetime
from environs import Env
from pathlib import Path
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from yourls import YOURLSClient, YOURLSKeywordExistsError, YOURLSNoLoopError



def main(request):
    return render(request, './templates/main.html')