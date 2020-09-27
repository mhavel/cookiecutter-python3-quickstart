# coding: utf-8


from .ipynb import is_notebook

try:
    if is_notebook():
        from tqdm.notebook import tqdm
    else:
        from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    tqdm = None
    HAS_TQDM = False

