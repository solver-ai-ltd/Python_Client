def get_setup_data(setup_file_path):
    with open(setup_file_path, 'r') as f:
        lines = f.readlines()

    config = {}
    for line in lines:
        key, value = line.strip().split('=')
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
