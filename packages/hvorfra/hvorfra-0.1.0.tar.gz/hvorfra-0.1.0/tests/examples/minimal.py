from hvorfra import assignment_name


def f() -> int:
    target = assignment_name()
    print(f"The result of this function is going to be assigned to: '{target}'.")
    return 42


some_variable_name = f()
some_other_variable_name = f()
