import requests


def get_setup_data(setup_file_path):
    with open(setup_file_path, 'r') as f:
        lines = f.readlines()

    config = {}
    for line in lines:
        sitrp_line = line.strip()
        if not sitrp_line or sitrp_line.startswith('#'):
            continue
        key, value = sitrp_line.split('=')
        config[key] = value

    token = config.get('token', '')
    datamanagerUrl = config.get('datamanagerUrl', '')
    computerUrl = config.get('computerUrl', '')

    errors = []
    if not token:
        errors.append('"token" parameter not found in setup')
    if not datamanagerUrl:
        errors.append('"datamanagerUrl" parameter not found in setup')
    if not computerUrl:
        errors.append('"computerUrl" parameter not found in setup')

    if errors:
        raise Exception('/n'.join(errors))

    return token, datamanagerUrl, computerUrl


def validate_token(datamanagerUrl, token):
    url = f'{datamanagerUrl}/api/data/validate-token/'
    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200:
            return True
        return False
    except Exception:
        raise Exception('Failed verifying token.')
