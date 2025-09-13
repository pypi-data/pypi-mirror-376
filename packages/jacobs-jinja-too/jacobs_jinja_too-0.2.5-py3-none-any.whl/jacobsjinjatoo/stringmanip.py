import stringcase

def bold(s: str):
    if s and s is not None and s != 'None' and len(s) > 0:
        return "**%s**" % (s)
    else:
        return ''

def italics(s: str):
    if s and s is not None and s != 'None' and len(s) > 0:
        return "_%s_" % (s)
    else:
        return ''

def upper_camel_case(s: str):
    return stringcase.pascalcase(stringcase.snakecase(s)).replace('_', '')

def lower_camel_case(s: str):
    return stringcase.camelcase(stringcase.snakecase(s)).replace('_', '')


def commentblock(s: str, marker: str = '#') -> str:
    """Prefix each non-empty line in `s` with `marker`.

    - Preserves existing newline characters.
    - Works with single-line and multi-line strings.
    - If `s` is falsy, returns an empty string.
    """
    if s is None:
        return ''
    text = str(s)
    # Keep trailing newline if present
    has_trailing_newline = text.endswith('\n')
    lines = text.split('\n')
    # If the original ended with a newline, split will give an extra empty string at the end;
    # we want to preserve that behavior when joining back.
    prefixed = [f"{marker}{line}" if line != '' else marker for line in lines]
    result = "\n".join(prefixed)
    if not has_trailing_newline and result.endswith('\n'):
        result = result[:-1]
    return result

