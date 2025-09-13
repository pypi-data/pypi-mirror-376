import numpy as np
import pandas as pd

def block2token(seq,blocks):
    '''
    Tokenizes a block tuple into element tokens for a given sequence. 
    Tokens are not standardized. Call token2standardtoken after using this.
    Args:
        seq (list): sequence of values
        blocks (set or list): blocks selected by algorithms
    Returns:
        list: list of tokens, ((crop rotation,),pos in crop rotation)
    '''
    blocks = sorted(blocks,key=lambda x: x[0])
    pos_dict = {s:[i for i in range(len(blocks)) if ((blocks[i][0]<=s) and (blocks[i][1]>s)) ] for s in range(len(seq))}
    tokens= []
    for pos in range(len(seq)):
        idx = min(pos_dict[pos])
        s,e,r,l = blocks[idx] 
        tokens.append((tuple(seq[s:s+r]),(pos-s)%r))
    # Calculate transient rotations. 
    for i,t in enumerate(tokens):
        if len(t[0])==1:
            if len(tokens)>(i+1): # only look if not last
                if t[0]==tokens[i+1][0]:
                    continue
            if 0<=(i-1):# only look if not first
                if t[0]==tokens[i-1][0]:
                    continue
            tokens[i] = (t[0],-1)
    return tokens

def token2standardtoken(token): 
    '''
    Takes a token and converts it into a standard token, where the minimal value for the crop rotation is used
    Args:
        Token (tuple): i.e. ((1,0),0)
    Returns:
        Standardized token (tuple): i.e. ((0,1),1)
    '''
    if len(token[0])==1 or (token[1] is None):
        return token
    b = [token[0][i:]+token[0][:i] for i in range(len(token[0]))]
    idx = min(range(len(b)),key=b.__getitem__)
    return (b[idx],(len(token[0])+token[1]-idx)%len(token[0]))
    
def _swap_value(token,seq):
    return (tuple((seq[t] for t in token[0])),token[1])

def normalize2specific(df,grp_seq,grp_norm,grp_tok):
    '''
    Converts general tokens to specific tokens in an efficient manner
    Args:
        df (DataFrame): each row contains the columns below
        grp_seq (list): the origional sequence
        grp_norm (list): the generalized sequence
        grp_tok (list): the tokenized sequence
    Returns:
        DataFrame:  the specific tokens with the same index as the input dataframe.
    '''
    df_a = df.reset_index(drop=True)
    grp = grp_seq
    grp_c = [f'_{i}' for i  in range(len(grp))]
    grp_return = [i for i  in range(len(grp))]
    df_a[grp_c] = pd.DataFrame([np.where(df_a[grp_norm]==c,df_a[grp],-1).max(axis=1) for c in range(len(grp_norm))]).T
    df_1 = df_a[grp_c+grp_tok].drop_duplicates().melt(id_vars=grp_c)
    df_2 = df_1[grp_c+['value']].drop_duplicates()
    results = []
    for g,df_g in df_2.groupby('value'):
        cols = list({f'_{i}' for i in g[0]})
        df_g1 = df_g[cols].drop_duplicates()
        df_g1['tok_val']=df_g1.apply(lambda x: (tuple(x[f'_{i}'] for i in g[0]),g[1]),axis=1)
        df_g1['tok_val'] = df_g1['tok_val'].map(token2standardtoken)
        results.append(pd.merge(df_g,df_g1,on=cols))
    df_3 = pd.concat([pd.merge(df_a[grp_c+[i]],pd.concat(results),left_on=grp_c+[i],right_on=grp_c+['value'],how='left')['tok_val'].rename(j) for i,j in zip(grp_tok,grp_return)],axis=1)
    df_3.index = df.index
    return df_3

def specific2normalize(df,grp):
    '''
    Normalizes a dataframe of sequences, so that the sequence's observed values increment by one. 
    Args:
        df (DataFrame): rows contain sequences and has columns of grp
        grp (list): the columns which corespond to the sequence
    Returns:
        DataFrame: With the index of the orginal dataframe, the columns numerically ascending based on the index of the grp.
    '''
    grp_norm = [f'_{i}' for i in range(len(grp))]
    df_r = df[grp].drop_duplicates()
    df_r[grp_norm] = -1
    df_r['counter']= 0
    for i in range(0,len(grp)):     
        result = []
        for indx,df_g in df_r.groupby([grp[i],grp_norm[i]]):
            if indx[1]==-1:
                df_a = df_g[grp]!=indx[0]
                df_a.columns = grp_norm
                df_g[grp_norm] = df_g[grp_norm].where(df_a,df_g['counter'],axis=0)
                df_g['counter']+=1
            result.append(df_g)
        df_r = pd.concat(result)
    return pd.merge(df,df_r[grp+grp_norm],on=grp,how='left')[grp_norm].rename(columns={j:i for i,j in enumerate(grp_norm)})