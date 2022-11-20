# utils.py
# Pretty much just the Misc box
# By Thomas Albertine

def intInput(prompt="", minValue=None, maxValue=None):
    result = None
    while result is None:
        try:
            result = int(input(prompt))
        except ValueError:
            print("Please enter an integer")
            result = None
            continue
        if not minValue is None and result < minValue:
            print("Please enter an integer larger than " + str(minValue - 1))
            result = None
        elif not maxValue is None and result > maxValue:
            print("Please enter an integer smaller than " + str(maxValue + 1))
            result = None
    return result

def choiceInput(choices, prompt=""):
    options = "\t" + "\n\t".join(map(lambda x: str(x[0]) + ": " + x[1], tuple(enumerate(choices)))) + "\n"
    return intInput(options + prompt, 0, len(choices) - 1)

