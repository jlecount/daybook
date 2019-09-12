import yaml


class Entry(object):
    """
    A diary entry.  May include encrypted text (title, body and tags.)
    You may have some entries encrypted and others not,
    but all fields within a single entry must be one way or another
    """
    def __init__(self, title, body, tag_list=None, is_encrypted=False):
        """

        :param title:  the title of the journal entry
        :param body: the full journal entry
        :param tag_list: the list of tags.  May be None
        :param is_encrypted: whether this entry is encrypted.
        """
        self.title = title
        self.body = body
        if tag_list and type(tag_list) != list:
            raise Exception("tag_list must be a list")
        else:
            self.tag_list = tag_list or []
        self.is_encrypted = is_encrypted

    def to_yaml(self):
        return yaml.dump(
            {'title': self.title,
             'body': self.body,
             'is_encrypted': self.is_encrypted,
             'tag_list': self.tag_list}
        )
