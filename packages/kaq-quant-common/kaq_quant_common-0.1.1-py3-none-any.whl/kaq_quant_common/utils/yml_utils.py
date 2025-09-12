import os
import yaml
import pkgutil
from loguru import logger


def read_config(project_dir=os.getcwd()):
    config_path = f'{project_dir}{os.sep}kaq_quant_common{os.sep}kaq_quant_common{os.sep}config{os.sep}config.yaml'
    if os.path.exists(config_path):
        with open(config_path, "r", encoding='utf-8') as file:
            data = yaml.safe_load(file)
    else:
        config_path = pkgutil.get_data('kaq_quant_common', f'config{os.sep}config.yaml')
        # print(f'get package file : {config_path}')
        data = yaml.load(config_path, Loader=yaml.FullLoader)

    return data



def get_mysql_script(project_dir=os.getcwd(), file_name: str='mysql_script.sql'):
    '''
    读取mysql脚本
    '''
    config_path = f'{project_dir}{os.sep}kaq_quant_common{os.sep}kaq_quant_common{os.sep}config{os.sep}mysql_script{os.sep}{file_name}'
    try:
        if os.path.exists(config_path) is False:
            config_path = pkgutil.get_importer('kaq_quant_common').path + f'{os.sep}config{os.sep}mysql_script{os.sep}{file_name}'
        if os.path.exists(config_path):
            return config_path
        return None
    except Exception as e:
        logger.error(f'yml_utils.get_mysql_script is error {str(e)}, {config_path} is not exits!')
    return None
    
def get_dos_script(project_dir=os.getcwd(), file_name='ddb_script.dos'):
    '''
    读取ddb脚本
    '''
    config_path = f'{project_dir}{os.sep}kaq_quant_common{os.sep}kaq_quant_common{os.sep}config{os.sep}ddb_script{os.sep}{file_name}'
    if os.path.exists(config_path) is False:
        config_path = pkgutil.get_importer('kaq_quant_common').path + f'{os.sep}config{os.sep}ddb_script{os.sep}{file_name}'
    if os.path.exists(config_path):
        return config_path
    return None

def get_spot_list(project_dir=os.getcwd()):
    '''
    获取合约对应的现货列表
    '''
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'spot_list' not in data:
        return None
    return data["spot_list"]

def get_future_list(project_dir=os.getcwd()):
    '''
    获取合约的symbol列表
    '''
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'future_list' not in data:
        return None
    return data["future_list"]

def get_api_key_secret(project_dir=os.getcwd()):
    '''
    获取bianace的api_key
    '''
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'api_key' not in data or 'api_secret' not in data:
        return None
    return data["api_key"], data["api_secret"]

def get_proxies(project_dir=os.getcwd()):
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'proxies' not in data:
        return None
    return data["proxies"]

def get_mysql_info(project_dir=os.getcwd()):
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'mysql' not in data:
        return None
    data = data['mysql']
    return data["host"], data["port"], data["user"], data["passwd"], data["database"], data["charset"]

def get_redis_info(project_dir=os.getcwd()):
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'redis' not in data:
        return None
    data = data['redis']
    return data["host"], data["port"], data["passwd"]

def get_posgresql_info(project_dir=os.getcwd()):
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'posgresql' not in data:
        return None
    data = data['posgresql']
    return data["host"], data["port"], data["user"], data["passwd"], data["database"], data["charset"]

def get_mysql_table_prefix(project_dir=os.getcwd()):
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'mysql_table_prefix' not in data:
        return None
    data = data['mysql_table_prefix']
    return data

def get_ddb_info(project_dir=os.getcwd()):
    data = read_config(project_dir)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']
    if 'ddb' not in data:
        return None
    data = data['ddb']
    return data["host"], data["port"], data["user"], data["passwd"]

 
if __name__ == '__main__':
    kv = get_ddb_info()
    print(kv)

