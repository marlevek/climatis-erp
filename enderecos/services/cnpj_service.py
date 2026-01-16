import requests


def buscar_cnpj(cnpj):
    cnpj = ''.join(filter(str.isdigit, cnpj))
    print('CNPJ RECEBIDO:', cnpj)

    if len(cnpj) != 14:
        print('CNPJ COM TAMANHO INVALIDO')
        return None

    url = f'https://brasilapi.com.br/api/cnpj/v1/{cnpj}'
    print('URL:', url)

    try:
        resp = requests.get(url, timeout=10)
    except Exception as e:
        print('ERRO REQUEST:', e)
        return None

    print('STATUS CODE:', resp.status_code)
    print('HEADERS:', resp.headers)
    print('BODY RAW:', resp.text[:500])  # primeiros 500 chars

    if resp.status_code != 200:
        return None

    data = resp.json()
    print('JSON OK')

    municipio = data.get('municipio', '')
    if isinstance(municipio, dict):
        municipio = municipio.get('nome', '')

    return {
        'razao_social': data.get('razao_social', ''),
        'nome_fantasia': data.get('nome_fantasia', ''),
        'email': data.get('email', ''),
        'telefone': data.get('ddd_telefone_1', ''),
        'endereco': {
            'cep': data.get('cep', ''),
            'logradouro': data.get('logradouro', ''),
            'numero': data.get('numero', ''),
            'complemento': data.get('complemento', ''),
            'bairro': data.get('bairro', ''),
            'cidade': municipio,
            'estado': data.get('uf', ''),
        }
    }
