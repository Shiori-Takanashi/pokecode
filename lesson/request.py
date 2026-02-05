def type_check(something) -> None:
    if not isinstance(something, str):
        raise TypeError("something is not str: %s" % type(something))
    return
