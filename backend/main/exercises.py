import ast
import inspect
import random
import string
import traceback

from littleutils import only

from main.utils import returns_stdout


class ExerciseError(Exception):
    pass


class InvalidInitialCode(Exception):
    pass


def make_function(program, function_template):
    arg_names = inspect.signature(function_template).parameters
    tree = ast.parse(program)
    try:
        for node, arg_name in zip(tree.body, arg_names):
            assert isinstance(node, ast.Assign)
            target = only(node.targets)
            assert isinstance(target, ast.Name)
            assert target.id == arg_name
    except AssertionError:
        raise ExerciseError(f"""\
Your code should start like this:

{inputs_string(dict.fromkeys(arg_names, "..."))}
""")

    assignments = tree.body[:len(arg_names)]
    exercise = tree.body[len(arg_names):]
    tree.body = assignments
    code = compile(tree, "<string>", "exec", dont_inherit=True)
    initial_names = {}
    try:
        exec(code, initial_names)
    except Exception as e:
        raise InvalidInitialCode from e
    del initial_names["__builtins__"]

    tree.body = exercise
    code = compile(tree, "<string>", "exec", dont_inherit=True)

    def func(**kwargs):
        exec(code, kwargs)

    if getattr(function_template, "returns_stdout", False):
        func = returns_stdout(func)

    return initial_names, func


def check_exercise(func, solution, test, generate_inputs, functionise=False):
    test(solution)
    inputs = [generate_inputs() for _ in range(10)]
    expected_generated_results = [solution(**inp) for inp in inputs]

    if functionise:
        try:
            initial_names, func = make_function(func, solution)
        except InvalidInitialCode:
            # There should be an exception in the usual output
            return False
        except ExerciseError as e:
            return dict(message=str(e))

        try:
            expected_result = solution(**initial_names)
        except Exception:
            traceback.print_exc()
            return dict(message="The values of your input variables are invalid, "
                                "try using values like the example.")

        try:
            check_result(func, initial_names, expected_result)
        except:
            traceback.print_exc()
            # Assume that the user can tell that the output is wrong
            return False

    try:
        test(func)
        for inp, result in zip(inputs, expected_generated_results):
            check_result(func, inp, result)
    except ExerciseError as e:
        return dict(message=str(e))

    return True


def clean_result(result):
    if not isinstance(result, str):
        result = repr(result)
    return result.rstrip() or '<nothing>'


def inputs_string(inputs):
    return '\n'.join(f'{name} = {value!r}' for name, value in inputs.items())


def check_result(func, inputs, expected_result):
    try:
        result = func(**inputs)
    except Exception as e:
        result = traceback.format_exception_only(type(e), e)

    result = clean_result(result)
    expected_result = clean_result(expected_result)

    if result != expected_result:
        raise ExerciseError(f"""\
Your code gives the right output for the example,
but for these inputs:

{inputs_string(inputs)}

your code outputs:

{result.rstrip()}

when it should output:

{expected_result.rstrip()}
""")


def generate_short_string():
    length = random.randrange(3, 8)
    return "".join(random.sample(string.ascii_lowercase, length))


def main():
    program = """
name = 'World'
print('Hello ' + name)
    """

    @returns_stdout
    def solution(name):
        print('Hello ' + name)

    def test(func):
        check_result(func, {"name": "World"}, "Hello World\n")
        check_result(func, {"name": "Bob"}, "Hello Bob\n")

    def generate_inputs():
        return {"name": generate_short_string()}

    print(check_exercise(program, solution, test, generate_inputs, functionise=True))


if __name__ == '__main__':
    main()