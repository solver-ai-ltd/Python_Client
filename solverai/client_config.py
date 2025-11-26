from os import path


data_file_folder_path = path.join(path.dirname(path.abspath(__file__)),
                                  '..', 'example_files')
setupFolder = path.join(path.dirname(path.abspath(__file__)),
                        '..', 'setup')
setupFilePath = path.join(setupFolder, 'setup.txt')

with open(setupFilePath, 'r') as f:
    lines = f.readlines()

config = {}
for line in lines:
    key, value = line.strip().split('=')
    config[key] = value

token = config.get('token', '')
datamanagerUrl = config.get('datamanagerUrl', '')
computerUrl = config.get('computerUrl', '')
