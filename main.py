from dataclasses import dataclass
import sys
import os
sys.path.append("vendor")
import uvicorn
import json

from fastapi import Request, FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from nerualpha.neru import Neru
from nerualpha.providers.voice.voice import Voice
from nerualpha.providers.voice.contracts.vapiEventParams import VapiEventParams
from nerualpha.providers.voice.contracts.IPhoneContact import IPhoneContact

app = FastAPI()
neru = Neru()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@dataclass
class Contact(IPhoneContact):
    type_: str
    number: str
    id: str
    def __init__(self):
        pass
    def reprJSON(self):
        dict = {}
        keywordsMap = {"from_":"from","del_":"del","import_":"import","type_":"type"}
        for key in self.__dict__:
            val = self.__dict__[key]

            if type(val) is list:
                parsedList = []
                for i in val:
                    if hasattr(i,'reprJSON'):
                        parsedList.append(i.reprJSON())
                    else:
                        parsedList.append(i)
                val = parsedList

            if hasattr(val,'reprJSON'):
                val = val.reprJSON()
            if key in keywordsMap:
                key = keywordsMap[key]
            dict.__setitem__(key.replace('_hyphen_', '-'), val)
        return dict

@app.get('/')
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/_/health')
async def health():
    return 'OK'

@app.post('/call')
async def call(request: Request, number: str = Form()):
    session = neru.createSession()
    voice = Voice(session)
    vonageContact = json.loads(os.getenv('NERU_CONFIGURATIONS'))['contact']

    vonageNumber = Contact()
    vonageNumber.type_ = vonageContact['type']
    vonageNumber.number = vonageContact['number']

    to = Contact()
    to.type_ = 'phone'
    to.number = number

    ncco = [
                {
                    'action': 'talk',
                    'text': 'Hi! This is a call made by the Voice API and NeRu'
                }
        ]

    response = await voice.vapiCreateCall(vonageNumber, [to], ncco).execute()

    vapiEventParams = VapiEventParams()
    vapiEventParams.callback = 'onEvent'
    vapiEventParams.vapiUUID = response['uuid']

    await voice.onVapiEvent(vapiEventParams).execute()
    return templates.TemplateResponse("index.html", {"request": request})

@app.post('/onEvent')
async def onCall(request: Request):
    body = await request.json()
    print('event status is:', body['status'])
    print('event direction is:', body['direction'])
    return 'OK'

if __name__ == "__main__":
    port = int(os.getenv('NERU_APP_PORT'))
    uvicorn.run(app, host="0.0.0.0", port=port)