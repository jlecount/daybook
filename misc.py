import os
import yaml

DAYBOOK_CFG = os.path.join(os.getenv("HOME"), ".daybook.yml")

def get_daybook_config():
    if os.path.exists(DAYBOOK_CFG):
        with open(DAYBOOK_CFG) as fp:
            return yaml.safe_load(fp)
    else:
        return {'daybooks': {}}
