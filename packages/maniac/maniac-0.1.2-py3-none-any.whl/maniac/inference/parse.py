# This file surfaces the CapturedInference class, which is constructed via calls to
# parse.capture(). This object contains details of inference calls, and can be extended
# to parse through specific function attributed to determine things like inference provider,
# model name, etc. for custom routing logic.

import inspect
import ast
import types

# Parse python code.

def _extract_func_name(func_node):
	if isinstance(func_node, ast.Name):
		return func_node.id
	elif isinstance(func_node, ast.Attribute):
		base = _extract_func_name(func_node.value)
		return f"{base}.{func_node.attr}"
	else:
		return "unknown_function"

def capture(lambda_expr, caller_frame):
	"""
	Captures a function call expression without executing it.
	Example usage:
		`captured = capture(lambda: client.responses.create(model="gpt-4", input="Hello"), inspect.currentframe())`
	Args:
		*lambda_expr*: A lambda function containing the expression to capture.
		*caller_frame*: The frame where the lambda expression's variables are defined.
	Returns:
		A CapturedInference object, containing the details, arguments, and function to execute.
	"""
	if not callable(lambda_expr):
		raise RuntimeError("capture() reuquires a lambda or callable object")

	try:
		source = inspect.getsource(lambda_expr)
		tree = ast.parse(source.strip())

		lambda_node = None
		for node in ast.walk(tree):
			if isinstance(node, ast.Lambda):
				lambda_node = node
				break
		
		if not lambda_node:
			raise RuntimeError("Could not find lambda expression in source")

		call_node = lambda_node.body
		if not isinstance(call_node, ast.Call):
			raise RuntimeError("Lambda body must be a function call")

		func_name = _extract_func_name(call_node.func)

		closure_vars = {}
		if lambda_expr.__closure__:
			closure_names = lambda_expr.__code__.co_freevars
			for i, name in enumerate(closure_names):
				closure_vars[name] = lambda_expr.__closure__[i].cell_contents

		local_vars = caller_frame.f_locals
		global_vars = caller_frame.f_globals

		context = {**global_vars, **local_vars, **closure_vars}

		args = []
		kwargs = {}

		for arg in call_node.args:
			args.append(eval(compile(ast.Expression(arg), '<string>', 'eval'), context))

		for keyword in call_node.keywords:
			if keyword.arg is None:  # Handle **kwargs expansion
				expanded = eval(compile(ast.Expression(keyword.value), '<string>', 'eval'), context)
				kwargs.update(expanded)
			else:
				kwargs[keyword.arg] = eval(compile(ast.Expression(keyword.value), '<string>', 'eval'), context)

		original_func = eval(compile(ast.Expression(call_node.func), '<string>', 'eval'), context)

		return CapturedInference(func_name, args, kwargs, original_func, closure_vars)

	except Exception as e:
		raise RuntimeError("Could not parse lambda inference expression")

def get_args():
	frame = inspect.currentframe().f_back
	params = frame.f_locals.copy()
	params.pop('self', None)
	kwargs = params.pop('kwargs', {})
	params.update(kwargs)
	return {k: v for k, v in params.items() if v is not None}

class CapturedInference:
	"""
	Represents a captured inference call, for interpretation and for delayed execution.
	"""
	def __init__(self, func_name, args, kwargs, original_func, closure_vars=None):
		self.func_name = func_name
		self.args = args
		self.kwargs = kwargs
		self.original_func = original_func
		self.closure_vars = closure_vars or {}

	def do(self):
		return self.original_func(*self.args, **self.kwargs)

	async def ado(self):
		"""Async version of do() for async inference calls."""
		return await self.original_func(*self.args, **self.kwargs)

	def model_input(self):
		"""Extract the messages field from OpenAI-compatible inference calls."""
		if 'messages' in self.kwargs:
			return self.kwargs['messages']
		
		# If not in kwargs, check if it's a positional argument
		# For OpenAI API, messages is typically the second argument after model
		if len(self.args) >= 2:
			return self.args[1]
		
		# Return empty list if no messages found
		return []
	
	def model_name(self):
		"""Extract the model name from OpenAI-compatible inference calls."""
		if 'model' in self.kwargs:
			return self.kwargs['model']
		
		# If not in kwargs, check if it's the first positional argument
		if len(self.args) >= 1:
			return self.args[0]
		
		# Return generic fallback if no model found
		return "unknown"

	def __repr__(self):
		args_str = ', '.join(repr(arg) for arg in self.args)
		kwargs_str = ', '.join(f'{k}={repr(v)}' for k, v in self.kwargs.items())
		all_args = ', '.join(filter(None, [args_str, kwargs_str]))
		return f"{self.func_name}({all_args})"

