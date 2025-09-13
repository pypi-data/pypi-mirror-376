

def get_valid_blocks(seq,repeat=False,max_rot_size=3):
    '''
    For a given sequence, produces all of the valid blocks
    Valid blocks are constrained by:
    1. Having a single repeating crop rotation under the designated maximum
    2. Having a block size greater than the crop rotation length (or at least twice the crop rotation length if repeat is True)
    3. Not being contained within another block with a smaller crop rotation size
    Args:
        seq (list): list of values
        repeat (bool): crop rotations are required to repeat in their entirety
        max_rot_size (int): the maximum length of a crop rotation
    Returns:
        list: A list of all valid blocks, as indicated by their starting, ending, crop rotation length, and block length.
    '''
    blocks = []
    for rot_size in range(1,max_rot_size+1):
        rot_threshold = rot_size*2-1 if repeat else rot_size
        p_gen = iter(range(0,len(seq)-rot_size+1))
        while True:
            try:
                p_min = next(p_gen)
            except StopIteration:
                break
            for p in range(p_min,len(seq)):
                # If the positions are less than the crop rotation size, continue adding
                # Or if the block is still growing 
                if ((p-p_min<rot_size) and rot_size>1) or (seq[p]==seq[p_min+(p-p_min)%rot_size]):
                    p = p+1
                    continue
                # If the block is longer than the threshold length keep
                elif p-p_min>rot_threshold:
                    blocks.append((p_min,p,rot_size,p-p_min))
                break
            if (p==len(seq)) and ((p-p_min)>rot_threshold):
                blocks.append((p_min,p,rot_size,p-p_min))
    # Eliminate blocks with longer crop rotations which are contained within blocks with smaller crop rotations
    removes = set()
    for i in range(len(blocks)):
        # The block list is ordered in such a way that we don't have to check previous values.
        for j in range(i,len(blocks)):
            s1,e1,r1,l1 = blocks[i]    
            s2,e2,r2,l2 = blocks[j]
            if i!=j and r1<=r2 and s1<=s2 and e1>=e2:
                removes.add(j)
    blocks = [blocks[i] for i in set(range(0,len(blocks)))-removes]
    # Check to make sure that all positions are covered.
    pos_abs = set(range(len(seq)))-set(i for s,e,r,l in blocks for i in range(s,e))
    return blocks+[(p,p+1,1,1) for p in pos_abs]

def _idx_pos_dict(blocks):
    '''
    Helper function for set coverage algorithms.
    Args:
        blocks (list): list of valid blocks
    Returns:
        idx_dict (dict): {index of df: set of time positions}
        pos_dict (dict): {time position: index}
        S (set): {time positions}
    '''
    idx_dict = {
        idx:set(range(val[0],val[1])) for idx,val in enumerate(blocks)
    }
    S = {j for i in idx_dict.values() for j in i}
    pos_dict = {s:[i for i in range(len(blocks)) if ((blocks[i][0]<=s) and (blocks[i][1]>s)) ] for s in S}
    return idx_dict,pos_dict,S

def _idxs_selector(idxs,blocks,start_pos=False):
    '''
    Args:
        idxs (list): list of indexes which to look at in the dataframe
        blocks (list): list of blocks to consider
        start_pos (int): if the start position is used as the first tiebraker and then the smallest window size. 
    Returns:
        int: the index value of the row of the data frame which is:
            1. is in idxs
            2. and has the smallest window size
            3. breaks ties using starting position.
    '''
    if start_pos:
        min_sp = min(blocks[i][0] for i in idxs)
        idxs = [i for i in idxs if blocks[i][0]==min_sp]
        if len(idxs)==1:
            return idxs[0]    
    min_rot_size = min(blocks[i][2] for i in idxs)
    idxs = [i for i in idxs if blocks[i][2]==min_rot_size]
    if len(idxs)==1:
        return idxs[0]
    # if that isn't sufficient, get the one with smallest start position
    min_sp = min(blocks[i][0] for i in idxs)
    idxs = [i for i in idxs if blocks[i][0]==min_sp]
    if len(idxs)==1:
        return idxs[0]    
    # This shouldn't ever happen if the blocks are generated through valid blocks. 
    raise NameError('Set Cover Indeterminant. Need Additional Condition')

def post_selection(blocks):
    '''
    Takes the set of selected blocks and processes them into the blocks which are used, eliminating blocks which are completely covered by two other blocks. 
    This will raise an error if there are indeterminate choices. 
    Args:
        blocks (list): list of blocks
    Returns:
        list: blocks, a subset of the blocks in input list.
    '''
    idx_dict,pos_dict,S = _idx_pos_dict(blocks)
    idxs_final = []
    while S:
        s = min(S)
        idxs = pos_dict[s]
        if len(idxs)==1:
            idx = idxs[0]
        else:
            max_y = max(j for i in idxs for j in idx_dict[i]) 
            idxs = [i for i in idxs if max_y in idx_dict[i]]
            if len(idxs)==1:
                idx = idxs[0]
            else:
                raise NameError('Indeterminant block Selection')
        S= S-idx_dict[idx]
        idxs_final.append(idx)
    return [blocks[i] for i in idxs_final]

def greedy_set_cover(blocks):
    '''
    Greedy set algorithm, selects the largest blocks first and continues till all positions are covered  
    Args:
        blocks (list): list of valid blocks
    Returns:
        list: blocks, subset of the input
    '''
    idx_dict,pos_dict,S = _idx_pos_dict(blocks)
    chosen_blocks = []
    while S:
        max_len = max(len(S & v) for v in idx_dict.values())
        idxs = [i for i,v in idx_dict.items() if len(S & v)==max_len]
        if len(idxs)==1:
            idx = idxs[0]
        else:
            idx= _idxs_selector(idxs,blocks)            
        S = S-idx_dict[idx]
        chosen_blocks.append(idx)
    return [blocks[i] for i in chosen_blocks]

def first_observed_cover(blocks,last=False):
    '''
    First observed takes the first (or last) observered value and selects the largest covering block and repeats
    Args:
        blocks (list): list of valid blocks
        last (bool): if we use last observed value rather than the first observed values
    Returns:
        list: blocks, subset of the input
    '''
    idx_dict,pos_dict,S = _idx_pos_dict(blocks)
    chosen_blocks = []
    while S:
        e = max(S) if last else min(S)
        dt = {idx:len(S & idx_dict[idx]) for idx in pos_dict[e]}
        max_len = max(dt.values())
        idxs = [i for i,v in dt.items() if v==max_len]
        if len(idxs)==1:
            idx=idxs[0] 
        else:
            idx = _idxs_selector(idxs,blocks)            
        S = S - idx_dict[idx]
        chosen_blocks.append(idx)
    return [blocks[i] for i in chosen_blocks]

def longest_repetition_cover(blocks):
    '''
    Selects blocks based on the largest ratio of block to crop rotation length.
    Args:
        blocks (list): list of valid blocks
    Returns:
        list: blocks, subset of the input
    '''
    idx_dict,pos_dict,S = _idx_pos_dict(blocks)
    chosen_blocks = []
    while S:
        max_rep = max((len(S & v))/(blocks[k][2]) for k,v in idx_dict.items())
        idxs = [k for k,v in idx_dict.items() if len(S & v)/blocks[k][2]==max_rep]
        # If there is only one choice select that choice
        if len(idxs)==1:
            idx=idxs[0] 
        else:
            # If there is a tie, select the rotation with the largest element overall
            # get coverage for each idxs
            max_cov = max([blocks[i][3] for i in idxs])
            idxs = [i for i in idxs if blocks[i][3]==max_cov]
            if len(idxs)==1:
                idx = idxs[0]
            else:
                # default to the element that is the shortest rotation and first observed.
                idx = _idxs_selector(idxs,blocks)            
        S = S - idx_dict[idx]
        chosen_blocks.append(idx)
    return [blocks[i] for i in chosen_blocks]
