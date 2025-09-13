def armstrong(number_to_check) -> bool:
    
    if isinstance(number_to_check, int):
        number_str = str(number_to_check)
    elif isinstance(number_to_check, str) and number_to_check.isdigit():
        number_str = number_to_check
    else:
        raise ValueError("The input must be an integer (str or int).")

    length = len(number_str)
    total = sum(int(digit) ** length for digit in number_str)

    return total == int(number_str)


