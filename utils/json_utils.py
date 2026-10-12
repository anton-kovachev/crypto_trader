import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class DateTimeDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    @staticmethod
    def _try_parse(value):
        if not isinstance(value, str):
            return value
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return value

    def object_hook(self, obj: dict):
        for k, v in list(obj.items()):
            if isinstance(v, str):
                obj[k] = self._try_parse(v)
            elif isinstance(v, list):
                new_list = []
                for item in v:
                    if isinstance(item, str):
                        new_list.append(self._try_parse(item))
                    else:
                        new_list.append(item)
                obj[k] = new_list
            # nested dicts are handled by the decoder recursion
        return obj
