"""
This module compiles a string expression into a MongoDB query dictionary.
"""

__all__ = ['compile_query', 'exceptions']

from . import exceptions, lexer, tokens


def parse(expression: str) -> tokens.Token:
	"""
	Parse a string expression into a token tree.

	Args:
		expression (str): The expression to parse.

	Returns:
		tokens.Token: The root token of the parsed expression.

	Raises:
		exceptions.SyntaxError: If the expression cannot be parsed.
			See exceptions.py for specific error types.
	"""

	prev_len = -1
	tok = lexer.parse(expression.lower())

	# first pass to condense any globs and strings
	pos = 0
	while pos < len(tok):
		prev_len = len(tok)

		if tok[pos].type in ['Glob', 'String']:
			tok = tok[pos].operate(tok, pos)

		if len(tok) == prev_len:
			pos += 1

	# then operate on all other tokens
	while len(tok) > 1:
		pos = 0
		while pos < len(tok):
			# only operate on tokens that haven't already been operated on
			if len(tok[pos].children) == 0:
				tok = tok[pos].operate(tok, pos)
			if len(tok) != prev_len:
				break
			pos += 1

		# if this round of parsing did not condense the expression,
		# then some other syntax error happened.
		if prev_len == len(tok):
			raise exceptions.SyntaxError

		prev_len = len(tok)

	if len(tok) == 0:
		return tokens.NoneToken()

	result = tok[0].reduce()
	if result.delete_me:
		return tokens.NoneToken()

	return result


def compile_query(expression: str, field: str) -> dict:
	"""
	Compile a string expression into a MongoDB query dictionary.

	Args:
		expression (str): The expression to compile.
		field (str): The field to apply the expression to.

	Returns:
		dict: A dictionary representing the MongoDB query.

	Raises:
		exceptions.ParseError: If the expression cannot be compiled.
			See exceptions.py for specific error types.
	"""
	return parse(expression).output(field)
