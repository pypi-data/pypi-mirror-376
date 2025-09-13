from cyclic_crop_rotation import *

# Crop Sequence
seq = (1,  5,  1,  5,  5,  1,  5,  1)

# Valid blocks
blocks = get_valid_blocks(seq,repeat=False,max_rot_size=3)

# Select out of the valid blocks the ones to use
gr = post_selection(greedy_set_cover(blocks)) 
fo = post_selection(first_observed_cover(blocks)) 
lr = post_selection(longest_repetition_cover(blocks)) 

# Get rotation tokens
gr_tok = block2token(seq,gr)
fo_tok = block2token(seq,fo)
lr_tok = block2token(seq,lr)

print(seq)
# Print reordered tokens
print(f'Greedy:{[token2standardtoken(i) for i in gr_tok]}')
print(f'1st Obs:{[token2standardtoken(i) for i in fo_tok]}')
print(f'Long Rep:{[token2standardtoken(i) for i in lr_tok]}')
