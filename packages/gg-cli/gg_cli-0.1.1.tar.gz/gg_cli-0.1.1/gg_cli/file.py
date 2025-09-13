import traceback
from appdirs import user_config_dir
import json
import os

app_name="gg-cli"
author="gg-cli"

def read_config()->dict:
    config_dir = user_config_dir(app_name, author)
    os.makedirs(config_dir, exist_ok=True)
    config_file = os.path.join(config_dir, "config.enc")
    if os.path.exists(config_file):
        try:
            with open(config_file,'r',encoding='utf-8') as f:
                content=f.read()
            ret=json.loads(content)
            assert(ret.get('llms'))
            assert(isinstance(ret['llms'],list))
            for i in ret['llms']:
                assert(isinstance(i,dict))
                assert(set(i.keys())=={'name','base_url','api_key','model','temperature'})
            assert(ret.get('default_llm'))
            assert(isinstance(ret['default_llm'], str))
            return ret
        except Exception as e:
            traceback.print_exc()
            try:
                os.remove(config_file)
            except:
                pass
    
    return {}

def save_config(config:dict):
    config_dir = user_config_dir(app_name, author)
    os.makedirs(config_dir, exist_ok=True)
    config_file = os.path.join(config_dir, "config.enc")
    json_data = json.dumps(config, indent=2)

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(json_data)
    
    print(f'config file saved to {config_file}')
    
        