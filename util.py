def split_bytes_to_tokens(lst):
    ''' 
    Takes Bytes object, and returns a list
    of Bytes objects, each corresponding to
    the value of a Token.
    '''
    result = []
    for i in range(len(lst)//2):
        index = i * 2
        byte = lst[index:index+2]
        result.append(byte)
    return result
