import requests 


def buscar_cep(cep):
    cep = cep.replace('-', '').strip()
    
    if len(cep) != 8:
        return None
    
    url = f'https://viacep.com.br/ws/{cep}/json/'
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        return None 
    
    data = response.json()
    
    if data.get('erro'):
        return None 
    
    return{
        'logradouro': data.get('logradouro', ''),
        'bairro': data.get('bairro', ''),
        'cidade': data.get('localidade', ''),
        'estado': data.get('uf', ''),
    }