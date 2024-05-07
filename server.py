# stdlib imports
import logging
import time
from os import environ as env

# 3rd party imports
from fastapi.logger import logger as fastapi_logger
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from src import models
from src import consulta

# Define configuracoes basicas para o logger
msg_frt = "[%(asctime)s] %(levelname)s [%(name)s] - %(message)s"
time_frt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(msg_frt, time_frt)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
LOG_LEVEL = env.get('LOG_LEVEL', default='INFO')
fastapi_logger.addHandler(handler)
fastapi_logger.setLevel(LOG_LEVEL)

logger_name = env.get('BOT_NAME', default='transparencia-receita-fortaleza')
fastapi_logger.name = logger_name

desc = '<a href="https://transparencia.fortaleza.ce.gov.br/index.php/receita/index" target="_blank">FONTE</a>'

tags_metadata = [
    {
        'name': 'transparencia-receita-fortaleza',
        'description': 'Consulta Portal Tranparencia Fortaleza - Receita'
    }
]

responses = {
    407: {'model': models.ResponseError, 'description': 'Proxy Authentication Required'},
    422: {'model': models.ResponseError, 'description': 'Unprocessable Entity'},
    500: {'model': models.ResponseError, 'description': 'Erro interno no servidor'},
    502: {'model': models.ResponseError, 'description': 'Bad Gateway'},
    504: {'model': models.ResponseError, 'description': 'Conexao com o site excedeu tempo limite'},
    509: {'model': models.ResponseError, 'description': 'Nao foi possivel resolver o captcha'},
    512: {'model': models.ResponseError, 'description': 'Erro ao executar parse da pagina'},
    513: {'model': models.ResponseError, 'description': 'Argumentos invalidos'}

}

#---------------------------- Application -------------------------------
app = FastAPI(
    title='REST API - Consulta Portal Transparência Fortaleza - Receita', 
    description=desc, 
    debug=False, 
    openapi_tags=tags_metadata,
    openapi_url="/api/transparencia-receita-fortaleza/consulta/docs/openapi.json",
    docs_url='/api/transparencia-receita-fortaleza/consulta/docs'
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'])

#---------------------------- Query params -------------------------------
ano_exercicio = Query(
    ..., 
    description='Ano de exercicio',
    regex='\d{4}'
)

data_inicio = Query(
     ..., 
    description='Data de cadastro no formato: DD/MM/AAAA',
    regex='\d{2}/\d{2}/\d{4}'
)

data_fim = Query(
     ..., 
    description='Data de cadastro no formato: DD/MM/AAAA',
    regex='\d{2}/\d{2}/\d{4}'
)
#---------------------------- Endpoints -------------------------------
@app.get(
    path=f"/api/transparencia-receita-fortaleza/consulta", 
    tags=['transparencia-receita-fortaleza'],
    responses=responses)
async def get_consulta(data_inicio: str = data_inicio, data_fim: str = data_fim, ano_exercicio: str = ano_exercicio):    
    return await consulta.fetch(data_inicio, data_fim, ano_exercicio)



#--------------------------- Static Files ------------------------------
app.mount("/", StaticFiles(directory="static", html=True), name="static")