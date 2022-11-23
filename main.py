from dataclasses import dataclass
import sys
import os
sys.path.append("vendor")
import uvicorn

from fastapi import Request, FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from nerualpha.neru import Neru
from nerualpha.providers.voice.voice import Voice
from nerualpha.providers.voice.contracts.vapiEventParams import VapiEventParams
from nerualpha.providers.voice.contracts.channelPhoneEndpoint import ChannelPhoneEndpoint

app = FastAPI()
neru = Neru()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

    to = ChannelPhoneEndpoint(number)
    vonageContact = ChannelPhoneEndpoint(os.getenv('VONAGE_NUMBER'))

    ncco = [
                {
                    'action': 'talk',
                    'text': 'Hi! This is a call made by the Voice API and NeRu'
                }
        ]

    response = await voice.vapiCreateCall(vonageContact, [to], ncco).execute()

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