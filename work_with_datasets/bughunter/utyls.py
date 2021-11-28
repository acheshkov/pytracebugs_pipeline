def get_code_snippet(lines, index):
    opening_brackets = 0
    closing_brackets = 0
    snippet = ''
    while index < len(lines):
        line = lines[index].strip()
        for letter in line:
            if letter == '}':
                closing_brackets += 1
            elif letter == '{':
                opening_brackets += 1

            snippet += letter
            if closing_brackets == opening_brackets and opening_brackets != 0:
                return snippet
        snippet += "\n"
        index += 1
    return snippet


def get_line_code_snippet(lines, index):
    return len(get_code_snippet(lines, index).split("\n"))


# Print iterations progress
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()
