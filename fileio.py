import os
import yaml
import subprocess
import tempfile

EDITOR = os.environ.get('EDITOR', 'vim')

def editor_create_entry(previous_contents:str="", title:str="", tags:str="") -> str:
    if previous_contents:
        initial_message = bytes(previous_contents.encode('utf-8'))
    else:
        if tags:
            tags = ' '.join(['@@{0}'.format(t.strip()) for t in tags.split(',')])

        if not (title or tags):
            initial_message = b""
        elif title and tags:
            initial_message = bytes('{0}\n\n{1}'.format(title, tags), 'utf-8')
        elif title:
            initial_message = bytes(title, 'utf-8')
        elif tags:
            initial_message = bytes(tags, 'utf-8')

    with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
        tf.write(initial_message)
        tf.flush()

        # if vim, start at EOF
        if 'vim' in EDITOR:
            cmd = [EDITOR, '+', tf.name]
        else:
            cmd = [EDITOR, tf.name]

        subprocess.call(cmd)

        # do the parsing with `tf` using regular File operations.
        # for instance:
        tf.seek(0)
        edited_message = tf.read()
        return edited_message.decode("utf-8")

def write_config(cfg_file, new_cfg):
    with open(cfg_file, 'w') as fp:
        yaml.safe_dump(new_cfg, fp)


def read_config(cfg_file):
    if os.path.exists(cfg_file):
        with open(cfg_file) as fp:
            return yaml.safe_load(fp)
    else:
        return {'daybooks': {}}
