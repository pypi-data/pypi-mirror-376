import os
import sys
from django.conf import settings as dj_settings
from django.utils.module_loading import import_string

AI_KEY =  os.environ.get("OPENAI_API_KEY",None)
AI_MODEL = os.environ.get('AI_MODEL','gpt-5')
AI_MODEL = 'gpt-5'
OPENAI_UPLOAD_STORAGE =  os.environ.get("OPENAI_UPLOAD_STORAGE",'/tmp/openaifiles')
os.makedirs(OPENAI_UPLOAD_STORAGE, exist_ok=True)
API_APP = 'localhost'
DJANGO_RAGAMUFFIN_DB = os.environ.get("DJANGO_RAGAMUFFIN_DB",None) 
d = dj_settings.DATABASES['default'];
PGDATABASE = d['NAME'];
PGHOST = d['HOST']
PGUSER = d['USER'];
PGPASSWORD = d['PASSWORD']
if not hasattr(dj_settings, 'SUBDOMAIN' ):
    SUBDOMAIN = os.environ.get('SUBDOMAIN','query')
MAXWAIT = 120 ; # WAIT MAX 120 seconds
DEFAULT_TEMPERATURE = 0.2;
LAST_MESSAGES = 99
MAX_NUM_RESULTS = None
MAX_TOKENS = 8000 # NOT IMPLMENTED AS OF openai==1.173.0 
AI_MODELS = {'staff' : 'gpt-5' , 'default' : AI_MODEL }
MEDIA_ROOT = OPENAI_UPLOAD_STORAGE
if not 'django_ragamuffin' in dj_settings.LOGGING['loggers'] :
    dj_settings.LOGGING['loggers']['django_ragamuffin'] = {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
            }


RUNTESTS = "pytest" in sys.modules
if not RUNTESTS :
    if not hasattr('dj_settings','DATABASE_ROUTERS') :
        DATABASE_ROUTERS = ['django_ragamuffin.db_routers.RagamuffinRouter'] 
    else :
        DATABASE_ROUTERS = ['django_ragamuffin.db_routers.RagamuffinRouter'] + dj_settings.DATABASE_ROUTERS

APP_KEY = os.environ.get('APP_KEY',None)
APP_ID = os.environ.get('APP_ID',None)
USE_MATHPIX = os.environ.get('USE_MATHPIX','False') == 'True'
if APP_KEY == None or APP_ID == None :
    USE_MATHPIX = False
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
CHATGPT_TIMEOUT = 60
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
AI_KEY =  os.environ.get("AI_KEY",None)
USE_CHATGPT =  os.environ.get("USE_CHATGPT",False) == 'True'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
APP_KEY = os.environ.get('APP_KEY',None)
APP_ID = os.environ.get('APP_ID',None)
USE_MATHPIX = os.environ.get('USE_MATHPIX','False') == 'True'
if APP_KEY == None or APP_ID == None :
    USE_MATHPIX = False

MAXWAIT = 120 ; # WAIT MAX 120 seconds
DEFAULT_TEMPERATURE = 0.2;
LAST_MESSAGES = 99
MAX_NUM_RESULTS = None
MAX_TOKENS = 8000 # NOT IMPLMENTED AS OF openai==1.173.0 
AI_MODELS = {'staff' : 'gpt-5-mini', 'default' : AI_MODEL }
API_APP = 'localhost'
EFFORT = 'low'

DEFAULTS = {
        "ENABLED" : True,
        "AI_KEY": AI_KEY,
        "AI_MODEL": AI_MODEL,
        'OPENAI_UPLOAD_STORAGE' : OPENAI_UPLOAD_STORAGE ,
        'API_APP' : API_APP ,
        'DJANGO_RAGAMUFFIN_DB' : DJANGO_RAGAMUFFIN_DB ,
        'PGHOST' : PGHOST ,
        'PGUSER' : PGUSER ,
        'PGPASSWORD' : PGPASSWORD ,
        'MAXWAIT' : MAXWAIT, 
        'DEFAULT_TEMPERATURE,' : DEFAULT_TEMPERATURE, 
        'LAST_MESSAGES,' : LAST_MESSAGES,
        'MAX_NUM_RESULTS,' : MAX_NUM_RESULTS, 
        'MAX_TOKENS,' : MAX_TOKENS,
        'AI_MODELS,' : AI_MODELS,
        'MEDIA_ROOT,' : MEDIA_ROOT,
        'RUNTESTS,' : RUNTESTS,
        'APP_KEY,' : APP_KEY,
        'APP_ID,' : APP_ID,
        'USE_MATHPIX,' : USE_MATHPIX,
        'DEFAULT_FILE_STORAGE,' : DEFAULT_FILE_STORAGE,
        'MAXWAIT' : MAXWAIT ,
        'EFFORT' : EFFORT ,
        'DATABASE_ROUTERS' : DATABASE_ROUTERS,
        }

