#!/usr/bin/env python

"""
Tools to manipulate data
"""

from collections import Counter
from functools import partial
from typing import Union
import pandas as pd
import numpy as np

from .logging import get_logger


logger = get_logger('{pkg}.utils.pandas')


def nan_str(x):
    if isinstance(x, float):
        return '' if np.isnan(x) else str(x)
    return str(x)


def str_join(x, sep=''):
    return sep.join((nan_str(_) for _ in x))


def fix_bools(df):
    """
    For some reason, when modifying inplace or adding data to a dataframe, a bool col can become object :/
    This causes lots of issues afterwards => try to fix it here
    """
    for c in list(df):
        k = df[c].dtype.kind
        if k == 'O':
            if not set(df[c].unique()).difference({True, False}):
                df.loc[:, c] = df[c].astype(bool)


dtypes_agg = {
    'f': np.nansum,
    'i': np.nansum,
    'b': np.nanmax,
    'O': str_join
}

dtypes_gb_agg = {
    'f': 'sum',
    'i': 'sum',
    'b': 'max',
    'O': 'unique',
    'M': 'max'
}



def unmelt(df: pd.DataFrame, on, value_cols, id_cols=None, new_cols=None, compress=False, filter_ids=None, agg=None, dtype_agg=None, **kw) -> pd.DataFrame:
    """
    Given a dataframe `df` of the form:
        x   A       B       C
        1   bar     1.2     NaN
        1   foo     2.3     1
        1   baz     45.3    2
        2   bar     8.3     10.3
        2   foo     -3.3    0.4
        3   bar     0.34    -0.53
    "unmelting" `df` on 'A' for 'B' and 'C', id from 'x' will produce the following dataframe:
        x   B_bar   B_foo   B_baz   C_bar   C_foo   C_baz
        1   1.2     2.3     45.3    NaN     1       2
        2   8.3     -3.3    NaN     10.3    0.4     NaN
        3   0.34    NaN     NaN     -0.53   NaN     NaN
    ie. the dataframe values from `value_cols` are pivoted from being row-indexed to col-indexed
    Args:
        df          (DataFrame):                dataframe to unmelt
        on          (str):                      column to be unmelted (to do the pivot on)
        value_cols  (str|list[str]):            list of columns holding values (x) to be unmelted (pivoted)
        id_cols     (str|list[str]=None):       columns used to identify uniquely new row (after aggregation)
                                                if None, do not aggregate
        
        new_cols    (callable|dict|str=None):   mapping to create new pivoted columns ; default to "{col}_{x}"
                                                if a function: new_name = func(col, x)
                                                if a dict: new_name = '{col}_{z}'.format(col=col, z=new_cols.get(x, x))
                                                if a str: new_name = new_col.format(col=col, x=x)
        compress    (bool=False):               if True, remove empty created feature (ie. full of NaN)
        filter_ids  (callable|list|bool=None):  `x` values ("on") to be kept ; if True, keep non-NaN values ;
                                                if callable, takes list of unique values, and return list of kept values
        agg         (str|dict|callable=None):   aggregation (for groupby)
                                                if None + new cols are unique -> agg='max' (ie. one-to-one pivot, no loss of information, nrow reduction)
                                                if None + new cols are overlapping -> agg={u:'max', o:'sum'} (ie. max for unique columns,
                                                    sum aggregation for overlapping)
        dtype_agg   (dict=None):                describe how to aggregate values when `new_cols` mapping has a many-to-one relation (ie. two distinct x values
                                                will produce same new column name, thus needing to aggregate values)
                                                if False -> do not aggregate at all (same number of rows as input)
                                                if None, replace old values by new ones
                                                if 'default', use default aggregation per type (see `dtypes_agg` in this module)
                                                else, should be a dict mapping type kind (f, i, b, O) to a function (eg. np.sum) or None
                                                TODO: this should never be needed! 
        **kw        (dict):                     options
    
    Keyword Arguments:
        na_rep                 :    replacement for NaN values in created new features
        na_rep_all  (bool=True):    if True, replace original NaN too with `na_rep`
        suffix_sep  (str='_')  :    the string to seperate the original column name with its `x` value (default: '_')
        agg_new     (str=sum)  :    the default method to aggregate new columns
        agg_num     (str=sum)  :    the default method to aggregate non-new numerical columns
        agg_other   (str=max)  :    the default method to aggregate other (not new, not num) columns
    """
    xarr = df[on].unique()

    # filter `x` values
    if filter_ids is not None:
        if isinstance(filter_ids, bool):
            if filter_ids:
                xarr = df.loc[df[on].notnull(), on].unique()
        elif callable(filter_ids):
            xarr = filter_ids(xarr)
        elif isinstance(filter_ids, str):
            xarr = [filter_ids]
        else:
            assert isinstance(filter_ids, (list, tuple, np.ndarray))
            xarr = list(filter_ids)

    # new column names generator: from an original column `col` and a value `x`, return new column name
    _sep = kw.get('suffix_sep', '_')
    if new_cols is None:
        get_name = (f'{{col}}{_sep}{{x}}').format
    elif isinstance(new_cols, str):
        def get_name(col, x):
            return new_cols.format(col=col, x=x)
    elif callable(new_cols):
        get_name = new_cols
    else:
        assert isinstance(new_cols, dict)
        def get_name(col, x):
            _ = new_cols.get(x, x)
            return f'{col}{_sep}{_}'

    # NaN management
    na_rep = repl_na = False
    nra = kw.get('na_rep_all', True)
    if 'na_rep' in kw:
        repl_na = True
        na_rep = kw['na_rep']
    keep_ona = repl_na and not nra

    # agg default
    default_agg_new = kw.get('agg_new', 'sum')
    default_agg_other = kw.get('agg_other', 'max')
    default_agg_num = kw.get('agg_num', 'sum')

    # value aggregation
    if dtype_agg == 'default':
        dtype_agg = dtypes_agg
    elif dtype_agg is not None:
        assert isinstance(dtype_agg, dict)

    if isinstance(value_cols, str):
        value_cols = [value_cols]
    else:
        value_cols = list(value_cols)
    ecols = {on}.union(value_cols)
    copy_cols = [_ for _ in df if _ not in ecols]
    res = df.loc[:, copy_cols].copy()
    new = Counter()
    ona = {}
    for x in xarr:
        # locate `xid` in data
        loc = df[on] == x
        # new col names
        names = [get_name(col=col, x=x) for col in value_cols]
        names_map = dict(zip(value_cols, names))
        new.update(names)
        # extract dataframe values
        y = df.loc[loc, value_cols].rename(columns=names_map).copy()
        # add to result
        co = list(set(y).intersection(res))
        if not co:
            # only unique new cols -> merge
            res = res.merge(y, how='outer', left_index=True, right_index=True)
        else:
            # new cols -> merge
            cu = list(set(y).difference(res))
            if cu:
                res = res.merge(y.loc[:, cu], how='outer', left_index=True, right_index=True)
            
            if dtype_agg:
                for c in co:
                    fagg = dtype_agg.get(y[c].dtype.kind, None)
                    if fagg is None:
                        res.loc[loc, c] = y.loc[:, c]
                    else:
                        res.loc[loc, c] = pd.DataFrame([res.loc[loc, c], y.loc[:, c]]).apply(fagg, axis=0)
            else:
                # overlapping cols -> replace values
                res.loc[loc, co] = y.loc[:, co]
        # keep info on original NaN
        if keep_ona:
            ona.update({col: y[col].isnull().index.values for col in names})

    # aggregation check
    if id_cols is None:
        agg = False
    elif isinstance(id_cols, str):
        id_cols = [id_cols]
    else:
        id_cols = list(id_cols)
    if agg is None:
        agg = dict({c: default_agg_new for c, n in new.items() if n > 1})
        agg.update({c: default_agg_other if res[c].dtype.kind not in ('f', 'i') else default_agg_num for c in set(res).difference(agg).difference(id_cols)})
    new = sorted(new)
    if not isinstance(agg, bool) and agg != 'max' and keep_ona:
        logger.warning('partial NaN replacement in `unmelt` is only reliable if `agg="max"`: replacing all NaNs')
        keep_ona = False
        nra = True

    # compress: remove columns full of NaNs
    if compress:
        comp = res.loc[:, new].dropna(axis='columns', how='all')
        res.drop(columns=new, inplace=True)
        res = res.merge(comp, how='outer', left_index=True, right_index=True)
        if isinstance(agg, dict):
            for c in set(new).difference(res).intersection(agg):
                del agg[c]
        new = sorted(set(res).intersection(new))

    # fill NaN
    xnr = xnk = np.nan
    if repl_na:
        xnr = xnk = na_rep
        if agg == 'max':
            # use a trick: replace by numbers that we know are less than minimum value in data
            xn0 = int(np.floor(res[new].min().min()))
            xnr = xn0 - 100     # value for NaN to replace = lowest value
            xnk = xn0 - 50      # value for NaN to keep = 2nd lowest value
        else:
            repl_na = False   # do not do replacement trick afterwards
        res.loc[:, new] = res[new].fillna(xnr).copy()
        if not nra:
            for col, loc in ona.items():
                res.loc[loc, col] = xnk

    # last, create a view grouping by `id_cols`, thus removing uncessary rows
    # res = res.groupby(id_cols).max().reset_index()   # max -> ensure we keep data's value, unless only NaN (ie. lower value replaced for NaN)
    if agg is not False:
        res = res.groupby(id_cols).agg(agg).reset_index()   # max -> ensure we keep data's value, unless only NaN (ie. lower value replaced for NaN)
    if repl_na:
        # now really replace original / created NaN values by their intended values: `na_rep` or NaN if not `na_rep_all`
        for col in new:
            res.loc[res[col] == xnr, col] = na_rep
            if not nra:
                # put back NaN values we wanted to keep
                res.loc[res[col] == xnk, col] = np.nan

    return res


def partial_merge(df_left: pd.DataFrame, df_right: pd.DataFrame, on=None, left_on=None, right_on=None, **name_mapping):
    """
    Merge `df_right` with `df_left`, but add only new cols from `df_right`
    """
    kw = {'how': 'outer'}
    if all((_ is None for _ in (on, left_on, right_on))):
        kw.update(left_index=True, right_index=True)
    else:
        kw.update(on=on, left_on=left_on, right_on=right_on)

    cols = set(df_left).difference({on, right_on})
    cols.discard(None)
    y = df_right.loc[:, [_ for _ in df_right if _ not in cols]]
    if name_mapping:
        y = y.rename(columns=name_mapping)
    return df_left.merge(y, **kw)


def merge_update(df_left: pd.DataFrame, df_right: pd.DataFrame, on=None, left_on=None, right_on=None,
                 left_index=False, right_index=False, prefer='right', adjust_dtypes=True):
    """
    Merge `df_right` with `df_left` in an update method:
        - distinct left/right columns are combined into the new dataframe
        - for common columns, a `combine_first` is performed (left to right if `prefer='left'`, right to left otherwise)
            this update replace NaN values with non-NaNs values where possible
        
    If `prefer` is 'left', right values are ignored if left ones are not NaNs.
    """
    if all((_ is None for _ in (on, left_on, right_on))):
        # based on index values
        if prefer == 'left':
            m = df_left.combine_first(df_right)
        else:
            m = df_right.combine_first(df_left)
    else:
        # use provided id columns
        if left_index:
            ml = df_left
        else:
            ml = df_left.set_index(left_on or on)
        if right_index:
            mr = df_right
        else:
            mr = df_right.set_index(right_on or on)
        if prefer == 'left':
            m = ml.combine_first(mr).reset_index()
        else:
            m = mr.combine_first(ml).reset_index()

    if adjust_dtypes:
        m = m.infer_objects()

    return m


def object_nan_rep(x: pd.Series):
    u = x.loc[x.notnull()].unique()
    k = list({type(_).__name__.replace('tuple', 'list') for _ in u})
    if len(k) == 1:
        return {'str': '', 'list': [], 'dict': {}}.get(k[0], np.nan)
    return np.nan


na_rep_mapping = {
    'f': 0.,
    'i': 0,
    'b': False,
    'O': object_nan_rep
}


def smart_fillna(df: pd.DataFrame, na_reps: dict=None, inplace=False, downcast=None):
    """
    Replace NaN values according to the type of each column. You can specify each NaN replacement by dtype kind:
        f: float
        i: int
        b: bool
        O: str (object)
    Default on object (O): check the type of other values and decide:
        - if only strings, NaN -> ''
        - if only list / tuple, NaN -> []
        - else no replacement
    """
    nr = na_rep_mapping.copy()
    if na_reps is not None:
        nr.update(na_reps)
    
    dt = df.dtypes.apply(lambda _: nr.get(_.kind, None)).to_dict()
    values = {c: x if not callable(x) else x(df[c]) for c, x in dt.items() if x is not None}

    return df.fillna(values, inplace=inplace, downcast=downcast)


def auto_adjust_dtypes(df: pd.DataFrame, inplace=False):
    if not inplace:
        df = df.copy()
    for c in list(df):
        df.loc[:, c] = pd.Series(df[c].tolist(), index=df.index, name=c)
    return df


def map_values(s: pd.Series, mapping: dict, warn=True):
    u = s.unique()
    m = set(u).difference(mapping)
    if m:
        if warn:
            logger.warning(f'missing values in your mapping ; in the series but not in mapping: {m}')
        mapping = mapping.copy()
        mapping.update({_: _ for _ in m})
    return s.map(mapping)


def constant_reducer(x0):
    def reducer(x):
        return x0
    return reducer


class ForbiddenAggError(Exception):
    pass


def forbidden_reducer(col=None, dtype=None):
    if col is None:
        assert dtype is not None
        def reducer(x):
            raise ForbiddenAggError(f'cannot aggregate this data type: {dtype}')
    else:
        def reducer(x):
            raise ForbiddenAggError(f'cannot aggregate this column: {col}')
    return reducer


def most_common_reducer(s=None, warn=False):
    if s is None:
        def reducer(x: pd.Series):
            y = x.loc[x.notnull()]
            v = y.mode().values[0]
            if warn:
                u = y.unique()
                if not len(u) == 1:
                    logger.warning(f'there are more than one non-NaNs unique values for column "{x.name}" ; using: {v}')
            return v
    else:
        y = s.loc[s.notnull()]
        v = y.mode().values[0]
        if warn:
            u = y.unique()
            if not len(u) == 1:
                logger.warning(f'there are more than one non-NaNs unique values for column "{s.name}" ; using: {v}')
        reducer = constant_reducer(v)
    return reducer


def unique_reducer(s=None):
    if s is None:
        def reducer(x: pd.Series):
            u = x.loc[x.notnull()].unique()
            if not len(u) == 1 :
                print(x.name)
                print(u)
                print(x.unique())
                print(x.index)
            assert len(u) == 1, f'{len(u)} non-NaNs unique values for column "{x.name}": expected 1'
            return u[0]
    else:
        u = s.loc[s.notnull()].unique()
        assert len(u) == 1, f'{len(u)} non-NaNs unique values for column "{s.name}": expected 1'
        reducer = constant_reducer(u[0])
    return reducer


def unique_na_reducer(s=None):
    if s is None:
        def reducer(x: pd.Series):
            u = x.unique()
            n = u.size
            if n == 1:
                return u[0]
            print(x.name)
            print(u)
            print(x.unique())
            print(x.index)
            assert False, f'{n} unique values for column "{x.name}": expected 1'
    else:
        u = s.unique()
        n = u.size
        if n == 1:
            reducer = constant_reducer(u[0])
        else:
            assert False, f'{n} unique values for column "{s.name}": expected 1'
    return reducer



def preferred_or_most_common_reducer(preferred: list, s=None, warn=False):
    if s is None:
        def reducer(x: pd.Series):
            y = x.loc[x.notnull()]
            u = set(y.unique())
            try:
                # find the first preferred value, it in unique (else raise StopIteration)
                v = next((x for x in preferred if x in u))
            except StopIteration:
                v = y.mode().values[0]
                if warn and len(u) > 1:
                    logger.warning(f'there are more than one non-NaNs unique values for column "{x.name}" ; using: {v}')
            return v
    else:
        y = s.loc[s.notnull()]
        u = set(y.unique())
        try:
            # find the first preferred value, it in unique (else raise StopIteration)
            v = next((x for x in preferred if x in u))
        except StopIteration:
            v = y.mode().values[0]
            if warn and len(u) > 1:
                logger.warning(f'there are more than one non-NaNs unique values for column "{s.name}" ; using: {v}')
        reducer = constant_reducer(v)
    return reducer


def gb_agg_dtypes(df: pd.DataFrame, on: (str, list), dtype_agg: dict=None, default_agg=None, agg: (dict, list)=None, preferred=None) -> pd.DataFrame:
    """
    Groupby `df` on `on`, and then aggregate the results and reset the index.
    This function is intended to aggregate easily based on data types. Four special agg strings can be used:
        - 'raise'               -> forbid to aggregate on this type / column (expect one value only)
        - 'unique'              -> force the array to have one unique non-NaN value, used as the aggregation value
        - 'most_common'         -> use the most common value (excluding NaNs)
        - 'most_common_warn'    -> same as above, but show warning when there is more than 1 unique values (excluding NaNs)
        - 'preferred_or_most_common'  -> given a list preferred value, pick the first one in data, otherwise the most common
        - 'preferred_or_most_common_warn'  -> given a list preferred value, pick the first one in data, otherwise the most common (with a warning if not unique)
    Args:
        df                          : the dataframe
        on                          : the column to groupby on
        dtype_agg   (dict)          : the mapping of dtypes (f, i, b, O) to agg function (str, callable) ; a default mapping is used
        default_agg (str|callable)  : the default aggregation function used if a column:
                                      - type is not in `dtype_agg`
                                      - AND not in `agg` (if provided)
        agg         (dict|list)     : explicit column aggregation function ; if a list, `default_agg` must be given
        preferred   (dict|list)     : preferred values, when `dtype_agg` = 'preferred_or_most_common'
    """
    if isinstance(on, str):
        on = [on]
    else:
        on = list(on)

    if preferred is None:
        preferred = {}
    else:
        if isinstance(preferred, (str, int, float, bool)):
            preferred = [preferred]
        if isinstance(preferred, list):
            # same list for all types...
            preferred = {t: preferred for t in 'fbiOM'}
        else:
            assert isinstance(preferred, dict)

    if isinstance(dtype_agg, str):
        if dtype_agg == 'default':
            dtype_agg = dtypes_gb_agg.copy()
        elif dtype_agg.startswith('preferred_or_most_common'):
            dtype_agg = {t: dtype_agg for t in 'fbiOM'}
        else:
            dtype_agg = {t: dtype_agg for t in 'fibOM'}
    elif callable(dtype_agg):
        dtype_agg = {t: dtype_agg for t in 'fibOM'}
    elif dtype_agg is None:
        if default_agg is None:
            dtype_agg = dtypes_gb_agg.copy()
        else:
            dtype_agg = {t: default_agg for t in 'fibOM'}
    else:
        assert isinstance(dtype_agg, dict)
        if default_agg is not None:
            dtype_agg = dict(dtypes_gb_agg, **{k: default_agg for k in set(dtypes_gb_agg).difference(dtype_agg)})
        else:
            dtype_agg = dict(dtypes_gb_agg, **dtype_agg)

    for t in list(dtype_agg):
        v = dtype_agg[t]
        if v == 'unique':
            dtype_agg[t] = unique_reducer()
        elif v == 'unique_na':
            dtype_agg[t] = unique_na_reducer()
        elif v == 'raise':
            dtype_agg[t] = forbidden_reducer(dtype=t)
        elif v == 'default':
            dtype_agg[t] = dtypes_gb_agg[t]
        elif v == 'most_common':
            dtype_agg[t] = most_common_reducer()
        elif v == 'most_common_warn':
            dtype_agg[t] = most_common_reducer(warn=True)
        elif v == 'preferred_or_most_common':
            dtype_agg[t] = preferred_or_most_common_reducer(preferred.get(t, ()))
        elif v == 'preferred_or_most_common_warn':
            dtype_agg[t] = preferred_or_most_common_reducer(preferred.get(t, ()), warn=True)

    if agg is None:
        agg = {}
    elif not isinstance(agg, dict):
        assert default_agg is not None, '`default_agg` must be provided when `agg` is not a dict'
        agg = {k: default_agg for k in agg}
    else:
        for c in list(agg):
            v = agg[c]
            if v == 'unique':
                agg[c] = unique_reducer(df[c])
            elif v == 'unique_na':
                agg[c] = unique_na_reducer(df[c])
            elif v == 'raise':
                agg[c] = forbidden_reducer(col=c)
            elif v == 'most_common':
                agg[c] = most_common_reducer(df[c])
            elif v == 'most_common_warn':
                agg[c] = most_common_reducer(df[c], warn=True)
            elif v == 'preferred_or_most_common':
                agg[c] = preferred_or_most_common_reducer(preferred.get(c, ()), df[c])
            elif v == 'preferred_or_most_common_warn':
                agg[c] = preferred_or_most_common_reducer(preferred.get(c, ()), df[c], warn=True)

    for c in set(df).difference(on).difference(agg):
        k = df[c].dtype.kind
        agg[c] = dtype_agg[k]

    return df.groupby(on).agg(agg).reset_index()



def add_transformed_cols(x: pd.DataFrame, on: Union[str, list], data: Union[dict, list], transform: Union[str, dict], adjust_dtype: bool=True):
    """
    Transform new data (but same index as x) and add the result to a dataframe
    """
    if isinstance(on, str):
        on = [on]
    y = x[on].copy()
    if not isinstance(data, dict):
        data = {c: x[c].values for c in data}
    assert not set(data).intersection(y)
    for col, values in data.items():
        y.loc[:, col] = values
    y = y.groupby(on).transform(transform)
    if adjust_dtype:
        for col in y:
            x.loc[:, col] = pd.Series(y[col].tolist(), index=x.index, name=col)
    else:
        x = merge_update(x, y, on=on, prefer='right')
    return x



def count_unique(x: pd.Series):
    return x.loc[x.notnull()].unique().size


def has_more_than_one_unique(x: pd.Series):
    return x.loc[x.notnull()].unique().size > 1


def flag_non_unique_agg_values(df: pd.DataFrame, ids, cols, suffix=''):

    if isinstance(cols, str):
        cols = [cols]

    if isinstance(ids, str):
        ids = [ids]
    else:
        ids = list(ids)

    gbc = df.groupby(ids)[cols].transform(has_more_than_one_unique)
    new_cols = {c: f'{c}{suffix}' for c in cols}
    gbc.rename(columns=new_cols, inplace=True)
    drops = [_ for _ in new_cols.values() if gbc[_].sum() == 0]
    if len(drops) == len(new_cols):
        # all dropped -> no flags
        return None
    gbc.drop(columns=drops, inplace=True)
    return gbc


def _identity(x):
    return x


class Round:
    def __init__(self, rounding=None, round_before_agg=False, agg='sum', **kw):
        fround = _identity
        if rounding is None:
            round_before_agg = False
        elif isinstance(rounding, bool):
            if not rounding:
                round_before_agg = False
            else:
                fround = np.round
        else:
            if isinstance(rounding, str):
                if rounding == 'down':
                    fround = np.floor
                elif rounding == 'up':
                    fround = np.ceil
                else:
                    fround = np.round
            elif isinstance(rounding, int):
                fround = partial(np.round, decimals=rounding)
            else:
                assert callable(rounding)
                fround = rounding
        self._func = fround
        self._before = round_before_agg
        self._agg = agg
        self._kw = kw.copy()
        self.round_before(round_before_agg)

    def round_before(self, yes):
        if yes:
            self._before = True
        else:
            self._before = False

    def get_round_func(self):
        return self._func

    def default_agg(self, agg, **kw):
        self._agg = agg
        self._kw = kw.copy()

    def round_and_agg(self, df: pd.DataFrame=None, cols=None, agg=None, **kw):
        if cols is not None:
            df = df.loc[:, cols]
        return getattr(df.apply(self._func), agg or self._agg)(**(kw or self._kw))
    
    def agg_and_round(self, df: pd.DataFrame=None, cols=None, agg=None, **kw):
        if cols is not None:
            df = df.loc[:, cols]
        return getattr(df, agg or self._agg)(**(kw or self._kw)).apply(self._func)

    def __call__(self, df: pd.DataFrame=None, cols=None, agg=None, **kw):
        if self._before:
            return self.round_and_agg(df, cols=cols, agg=agg, **kw)
        else:
            return self.agg_and_round(df, cols=cols, agg=agg, **kw)

    def get_round_agg_func(self):
        if self._before:
            return self.round_and_agg
        else:
            return self.agg_and_round
