import re

def print_tree(tree, depth=0):
    print(" " * depth, end='')        
    # test token level
    if (tree.child and 
        not tree.child[0].child):
        print(f"{tree.value}-{tree.child[0].value}")                
    else:
        print(tree.value)
        for child in tree.child:
            print_tree(child, depth+1)       

def get_leaves(tree):
    if not tree.child:
        return [tree]
    else:
        return sum((
            get_leaves(x)
            for x in tree.child), [])

def get_nodes(tree, pred_func):
    if pred_func(tree):
        return [tree]
    else:
        return sum((
            get_nodes(x, pred_func)
            for x in tree.child), [])
    
def has_single_token(tree):
    return len(get_leaves(tree)) == 1

def is_token_level(tree):
    return (
        tree.child and 
        not tree.child[0].child
    )

def get_tokens(tree):
    return get_nodes(
            tree, 
            is_token_level)

def no_fullwidth_alphanum(tree):
    tokens = get_tokens(tree)
    tokens = filter(lambda x: x.child, tokens)    
    
    return all(
        not re.findall(r"[\uff10-\uff5a]+", x.child[0].value)
            for x in tokens)

def is_np_compound(tree):
    is_NP = tree.value == "NP"
    has_two_child = len(tree.child) == 2
    if not is_NP or not has_two_child:         
        return False    
    
    child_are_tokens = all(
        has_single_token(x)
        for x in tree.child)
    not_all_mono = not_all_mono_syllabic(tree)
    if not child_are_tokens or not not_all_mono:         
        return False    
    
    no_stop_token = (all(x.value!="PU" for x in get_tokens(tree))
                     and no_fullwidth_alphanum(tree))
    
    return is_NP and has_two_child and \
           child_are_tokens and not_all_mono and \
           no_stop_token

def not_all_mono_syllabic(tree):
    leaves = get_leaves(tree)
    return any(len(x.value)>1
              for x in leaves)

def has_all_bisyll_tokens(tree):
    leaves = get_leaves(tree)
    return all(len(x.value)==2
              for x in leaves)

def flatten_compound(tree):
    ret = []
    for x in tree.child:
        token = get_tokens(x)[0]
        ret.append((
            token.child[0].value,
            token.value
        ))
    ret = list(zip(*ret))
    return ret

def is_two_bisyll_np(tree):
    return is_np_compound(tree) and has_all_bisyll_tokens(tree)

def to_linear(tree):
    if (tree.child and 
        not tree.child[0].child):
        return (tree.value, tree.child[0].value)
    else:
        child_string = [to_linear(x) 
                       for x in tree.child]
        return (tree.value, *child_string)
