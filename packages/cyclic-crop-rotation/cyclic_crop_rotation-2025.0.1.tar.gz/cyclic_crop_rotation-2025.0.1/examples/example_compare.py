import pandas as pd
from itertools import combinations
from cyclic_crop_rotation import all_seqs,get_valid_blocks,greedy_set_cover,first_observed_cover,longest_repetition_cover,post_selection,block2token,token2standardtoken,get_window_tokens

seq_len=8
grp_norm = [f'N{i:02}' for i in range(0,seq_len)]
# Gets a list of all possible general sequences
seq_ls = all_seqs(seq_len)
results = []
for i,seq in enumerate(seq_ls):
    dt = {}
    for max_rot_size in range(2,5):
        for repeat in [False,True]:
            # Get the valid blocks for the maximum crop rotation length and if repeats are required
            blocks = get_valid_blocks(seq,repeat=repeat,max_rot_size=max_rot_size)
            # Use those blocks as the basis for selecting based on one of the three algorithms
            # Then use the post selectiong process to eliminate blocks which are covered by other blocks, mostly a concern with the greedy and longest repetition algorithm
            # Then convert the blocks to a token representation.
            dt[('GR',max_rot_size,repeat)] = block2token(seq,post_selection(greedy_set_cover(blocks)))
            dt[('RP',max_rot_size,repeat)] = block2token(seq,post_selection(longest_repetition_cover(blocks)))
            dt[('FO',max_rot_size,repeat)] = block2token(seq,post_selection(first_observed_cover(blocks)))
            if repeat==False:
                # Windows don't have as complicated of a process. It is just one call.
                dt[('WI',max_rot_size,repeat)] = get_window_tokens(seq,max_rot_size)
    df = pd.DataFrame(dt).T
    df['idx'] = i
    df = df.set_index('idx',append=True)
    results.append(df)
# Run the token standardization on the entire collection
# Element handling in pandas makes this more efficient to do here
df = pd.concat(results).applymap(token2standardtoken)
# Comparing results of algorithms.
df_1 = df.unstack(level=[0,1,2])
for rot in range(2,5):
    for rep in [True,False]:
        same = pd.concat([
            (df_1.xs((a1,rot,rep),axiss=1,level=[1,2,3])==df_1.xs((a2,rot,rep),axis=1,level=[1,2,3])).all(axis=1)
            for a1,a2 in combinations(['FO','GR','RP'],2)],axis=1).all(axis=1).sum()
        print(f'{rot},{rep}: {same}')