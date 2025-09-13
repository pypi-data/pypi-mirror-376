
def get_window_tokens(seq,win_size=2,pad=False):
    '''
    Returns window tokens for a sequence (not standardized)
    Args:
        seq (list): sequence of interest
        win_size (int): size of window
        pad (bool): if return list is padded or not
    Returns:
        list: list of tokens
        If pad==True:
            the start of the list will be padded with win_size-1 tokens so that the return list is the same size as the sequence
            the padded values will be ((None,)*win_size,None)
        If pad==False:
            the list will be of length len(seq)-win_size+1
    '''
    return [((None,)*win_size,None) for _ in range(win_size-1)]+[(tuple(seq[i:i+win_size]),0) for i in range(len(seq)-win_size+1)]
