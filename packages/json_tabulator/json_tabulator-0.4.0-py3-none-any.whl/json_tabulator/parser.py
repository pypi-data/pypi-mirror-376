
from .expression import Expression, STAR, KEY, PATH

from parsy import string, regex, eof, alt, seq, ParseError


dot = string('.').then(eof.should_fail('expression to continue'))
star = alt(string('*'), string('[*]')).result(STAR)
root = string('$').result([])
forbidden = ''.join(['"', "'", '\\.', '\\$', '\\*', '\\[\\]', '\\(\\)'])
end_of_segment = eof | dot
lparen = string('(')
rparen = string(')')
lbracket = string('[')
rbracket = string(']')


def make_quoted_member(q: str):
    def unquote(s: str) -> str: return s.replace('\\' + q, q)
    return string(q) >> regex(f'(\\\\{q}|[^{q}])+').map(unquote) << string(q)


unquoted_member = regex(f'[^{forbidden}0-9][^{forbidden}]*')
quoted_member = (make_quoted_member('"') | make_quoted_member("'"))
number = regex(r'\d+').map(int)
func_key =  lparen >> string('key').result(KEY) << rparen
func_path = lparen >> string('path').result(PATH) << rparen
function = alt(func_key, func_path)

subscript = lbracket >> alt(number, quoted_member, star) << rbracket

initial_segment = alt(
    root,
    unquoted_member,
    quoted_member,
    subscript,
    star,
)
inner_segment = alt(
    dot >> unquoted_member,
    dot >> quoted_member,
    dot >> star,
    dot >> function,
    subscript
)


def concat_list(*args):
    res = []
    for a in args:
        if isinstance(a, list):
            res += a
        else:
            res.append(a)
    return res


expression = seq(initial_segment, inner_segment.many()).combine(concat_list)


class InvalidExpression(ValueError):
    pass


def parse_expression(string: str) -> Expression:
    try:
        res = Expression(expression.parse(string))
    except ParseError:
        raise InvalidExpression(string)

    for i, part in enumerate(res):
        if part in (KEY, PATH):
            if i == 0 or res[i - 1] != STAR:
                raise InvalidExpression(string)
            if i < len(res) - 1:
                raise InvalidExpression(string)

    return res
