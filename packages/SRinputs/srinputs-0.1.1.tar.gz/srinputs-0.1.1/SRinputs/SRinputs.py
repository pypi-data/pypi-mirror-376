from fast_langdetect import detect

emptymsg = {'en' : 'Write something',
            'es' : 'Escribe algo'}

msgs = {'en' : ["That's not funny!", "This is not correct!"],
        'es' : ['No es divertido', 'Esto no es correcto!']}

ermsgs = {'en' : ['is not integer', 'is not float'],
          'es' : ['No es entero', 'No es un número de coma flotante']}

def IntInput(msg: str = 'Write an integer value: ', ermsg: str = None, empty_input: bool = False) -> int:
    """
    Prompts the user for input and validates it as an integer.

    The function repeatedly asks for input until a valid integer is provided.
    It does not allow empty inputs by default.

    Args:
        msg (str, optional): The message to display to the user.
        ermsg (str, optional): The error message to display on invalid input.
        empty-input (bool, optional): If True, allows empty inputs. Defaults to False.
    Returns:
        int: The integer value of the valid input.
    """
    if not ermsg:
        try:
            empmsg = emptymsg[detect(msg)['lang']]
            ermsg = ermsgs[detect(msg)['lang']][0]
            exmsg1 = msgs[detect(msg)['lang']][0]
            exmsg2 = msgs[detect(msg)['lang']][1]
        except KeyError:
            print(f'{detect(msg)} language not supported yet, using english as default.')
            empmsg = emptymsg['en']
            ermsg = ermsgs['en'][0]
            exmsg1 = msgs['en'][0]
            exmsg2 = msgs['en'][1]

    while True:
        try:
            text = input(msg)
            if not empty_input and not text:
                print(empmsg)
                continue
            if not text:
                break  
            text = int(text)
            break
        except ValueError:
            print(f'{text} {ermsg}')
            continue
        except KeyboardInterrupt:
            print(exmsg1)
            continue
        except EOFError:
            print(exmsg2)  
            continue       
    return text

def StrInput(msg: str = 'Write any string: ', empty_input: bool = False) -> str:
    """
    Prompts the user for input and validates it as a non-empty string.

    The function repeats the prompt until a non-empty string is provided.
    It does not allow empty inputs by default.

    Args:
        msg (str): The message to display to the user.
        empty-input (bool): If True, allows empty inputs. Defaults to False.
    Returns:
        str: The validated non-empty input string.
    """
    try:
        empmsg = emptymsg[detect(msg)['lang']]
        exmsg1 = msgs[detect(msg)['lang']][0]
        exmsg2 = msgs[detect(msg)['lang']][1]
    except KeyError:
        print(f'{detect(msg)} language not supported yet, using english as default.')
        empmsg = emptymsg['en']
        exmsg1 = msgs['en'][0]
        exmsg2 = msgs['en'][1]
    while True:
        try:
            text = input(msg)
            if not empty_input and not text:
                print(empmsg)
                continue
            if not text:
                break  
            break
        except KeyboardInterrupt:
            print(exmsg1)
            continue
        except EOFError:
            print(exmsg2)  
            continue       
    return text

def FloatInput(msg: str = 'Write a float value: ', ermsg: str = None, empty_input: bool = False) -> float:
    """
    Prompts the user for input and validates it as a float.

    The function repeatedly asks for input until a valid float is provided.
    It does not allow empty inputs by default.

    Args:
        msg (str): The message to display to the user.
        ermsg (str): The error message to display on invalid input.
        empty-input (bool): If True, allows empty inputs. Defaults to False.
    Returns:
        float: the float value of the input.
    """
    if not ermsg:
        try:
            empmsg = emptymsg[detect(msg)['lang']]
            ermsg = ermsgs[detect(msg)['lang']][1]
            exmsg1 = msgs[detect(msg)['lang']][0]
            exmsg2 = msgs[detect(msg)['lang']][1]
        except KeyError:
            print(f'{detect(msg)} language not supported yet, using english as default.')
            empmsg = emptymsg['en']
            ermsg = ermsgs['en'][1]
            exmsg1 = msgs['en'][0]
            exmsg2 = msgs['en'][1]
    while True:
        try:
            text = input(msg)
            if not empty_input and not text:
                print(empmsg)
                continue
            if not text:
                break  
            text = float(text)
            break
        except ValueError:
            print(f'{text} {ermsg}')
            continue
        except KeyboardInterrupt:
            print(exmsg1)
            continue
        except EOFError:
            print(exmsg2)  
            continue       
    return text

def multiInput(num: int, msg: str = 'Write any string: ', empty_input: bool = False) -> list:
    """
    Prompts the user for a specified number of inputs and returns them as a list.

    This function asks for 'n' inputs and collects them into a list.
    It does not allow empty inputs by default.

    Args:
        num (int): the number of inputs
        msg (str): the message display for each input prompt.
        empty-input (bool): If True, allows empty inputs. Defaults to False.
    Returns:
        list[str]: A list containing all the input strings.
    """
    try:
        empmsg = emptymsg[detect(msg)['lang']]
        exmsg1 = msgs[detect(msg)['lang']][0]
        exmsg2 = msgs[detect(msg)['lang']][1]
    except KeyError:
        print(f'{detect(msg)} language not supported yet, using english as default.')
        empmsg = emptymsg['en']
        exmsg1 = msgs['en'][0]
        exmsg2 = msgs['en'][1]

    inputs: list[str] = []
    aux : int = 0
    while True:
        try:
            while aux < num:
                text = input(msg)
                if not empty_input and not text:
                    print(empmsg)
                    continue
                if not text:
                    inputs.append('')
                    aux += 1
                    continue  
                inputs.append(text)
                aux += 1
        except KeyboardInterrupt:
            print(exmsg1)
            continue
        except EOFError:
            print(exmsg2)
            continue
        return inputs