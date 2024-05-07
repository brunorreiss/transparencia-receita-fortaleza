# Importando libs
# stdlib imports
from os import environ as env
from datetime import datetime
from urllib.parse import urlencode

# 3rd party imports
import aiohttp
from fastapi.logger import logger
from fastapi.responses import JSONResponse
from fastapi import responses, status
from bs4 import BeautifulSoup

# Local imports
from src.models import Receita
from utils.util import get_headers, is_number

# Captura variaveis de ambiente e cria constants
TIMEOUT = env.get('TIMEOUT', default=180)

#---------------------------------------------------------------------------------------------------
async def process_detalhes(soup: BeautifulSoup) -> list[Receita]:
    logger.debug('Função process_detalhes() iniciou')
    
    results = []  # Lista para armazenar os resultados
    
    # Encontra todas as tabelas com a classe especificada
    tables = soup.find_all('table', class_='table table-striped')
    
    # Verifica se a tabela desejada está presente
    if len(tables) < 2:
        logger.error("A tabela necessária não foi encontrada.")
        return results
    table = tables[1]  # Seleciona a segunda tabela
    
    # Extrai os cabeçalhos da tabela
    headers = [
        th.text.strip().lower()
        .replace(' (r$)', '')
        .replace(' ', '_')
        .replace('%realizado', 'percentual_realizado')
        .replace('receita_arrecadada_no_período_(r$)', 'receita_arrecadada_no_período')
        .replace('receita_prevista_no_ano_(r$)', 'receita_prevista_no_ano')
        .replace('receita_recolhida_no_período_(r$)', 'receita_recolhida_no_período')
        for th in table.find_all('th')
    ]

    logger.debug(f"Cabeçalhos encontrados: {headers}")
    
    # Extrai as linhas da tabela
    rows = table.find_all('tr')
    
    # Itera por cada linha para extrair os dados
    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) != len(headers):
            logger.warning(f"Linha ignorada devido a contagem de células inconsistente: {row}")
            continue
        
        receita = {}
        # Usando a função no loop
        for i, cell in enumerate(cells):
            value = cell.text.strip().replace('.', '').replace(',', '.')
            if i in [2, 3, 4, 5]:  # Supondo que esses índices sejam para valores numéricos
                if is_number(value):
                    value = float(value)
                else:
                    logger.warning(f"Valor não numérico encontrado, usando 0.0: {value}")
                    value = 0.0
            if headers[i] == 'detalhamento' and cell.find('a'):
                value = cell.find('a')['href'] if cell.find('a')['href'] else None
            receita[headers[i]] = value
        
        results.append(Receita(**receita))
                
    logger.debug(f"Dados processados: {results}")
    return results
# ------------------------------------------------------------------------------------------------
async def fetch(data_inicio, data_fim, ano_exercicio):
    if (not data_inicio or not data_fim or not ano_exercicio):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"code": 422, "message": "Unprocessable Entity", 
                     "datetime": datetime.now().isoformat()}
        )
        
    logger.info(f"Fetching data from {data_inicio} to {data_fim} for year {ano_exercicio}")
    
    # Configura os timeouts
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    session = aiohttp.ClientSession(timeout=timeout)
    
    # Configurando headers
    session.headers.update(get_headers())
    
    session.headers.update({'Host': 'transparencia.fortaleza.ce.gov.br'})
    
    
    base_url = 'https://transparencia.fortaleza.ce.gov.br/index.php/receita/index'
    
    try:
        resp = await session.get(base_url, ssl=False, allow_redirects=True)
        logger.debug(f"GET {base_url} - {resp.status}")
        
        cookie_list = [f'{cookie.value}' for cookie in session.cookie_jar]
        
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Cookie': '; '.join(cookie_list),
            'Referer': 'https://transparencia.fortaleza.ce.gov.br/index.php/receita/index',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0' 
        })
        
        payload = {
            'exercicio': ano_exercicio,
            'txtDataIni': data_inicio,
            'txtDataFim': data_fim,
            'opcaoPesquisa': 'porReceita',
            'filtroPorReceita': 'receitaSintetica',
            'filtroPorOrgao': '0',
            'orgaoDesc': '',
            'btnConsultar': 'Consultar'
        }
        
        params = {
            'exercicio': ano_exercicio,
            'txtDataIni': data_inicio,
            'txtDataFim': data_fim,
            'opcaoPesquisa': 'porReceita',
            'filtroPorReceita': 'receitaSintetica',
            'filtroPorOrgao': '0',
            'orgaoDesc': '',
            'btnConsultar': 'Consultar'
        }
        
        url_param = 'https://transparencia.fortaleza.ce.gov.br/index.php/receita/consultar'
        
        full_url = f"{url_param}?{urlencode(params)}"
        
        # Post
        resp = await session.post(full_url, data=payload, ssl=False, allow_redirects=True)
        resp_content = await resp.content.read()
        resp_soup = BeautifulSoup(resp_content, 'html.parser')
        
        if resp.status != 200:
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content={"code": 502, "message": "Bad Gateway", 
                         "datetime": datetime.now().isoformat()}
            )
        else:
            resultado = await process_detalhes(resp_soup)
            
            result = {
                'code': 0,
                'message': 'SUCCESS',
                'datetime': datetime.now().isoformat(),
                'results': resultado
            }
    
    except:
        logger.exception('Error')
        await session.close()      

        return responses.JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'code': 3,
                'message': 'INTERNAL_SERVER_ERROR'
            }
        )

    else:
        
        await session.close()
        
        logger.info(f'Função fetch terminou com sucesso. {len(resultado)} registros encontrados.')

    return result