import urllib.parse
import base64
import uuid

def unicode_slug(instr: str) -> str:
    from slugify import slugify
    return slugify(instr, lowercase=False, allow_unicode=True)


def url_encode(url: str) -> str:
    return urllib.parse.quote(url)


def do_base_64(input: str) -> str:
    resp = base64.b64encode(f'{input}'.encode("utf-8"))
    return resp.decode()


def is_valid_uuid(val: str, version: int | None = None) -> bool:
    try:
        uuid.UUID(val, version=version)
    except BaseException:
        return False

    return True


def convert_dict_to_url(dict):
    return '&' + '&'.join([f'{k}={v}' for k, v in dict.items()]) if len(dict) else ''

# not used
# def is_assci_alphanumeric(str):
#     for c in str:
#         if c not in string.ascii_letters + string.digits:
#             return False
#     return True
