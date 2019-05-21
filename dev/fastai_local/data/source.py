#AUTOGENERATED! DO NOT EDIT! File to edit: dev/03_data_source.ipynb (unless otherwise specified).

__all__ = ['coll_repr', 'ListContainer', 'DataSource', 'TfmList']

def coll_repr(c, max=1000):
    "String repr of up to `max` items of (possibly lazy) collection `c`"
    return f'({len(c)} items) [' + ','.join(itertools.islice(map(str,c), 10)) + ('...'
            if len(c)>10 else '') + ']'

class ListContainer():
    "Behaves like a list of `items` but can also index with list of indices or masks"
    def __init__(self, items): self.items = listify(items)
    def __len__(self): return len(self.items)
    def __iter__(self): return iter(self.items)
    def __setitem__(self, i, o): self.items[i] = o
    def __delitem__(self, i): del(self.items[i])
    def __repr__(self): return f'{self.__class__.__name__} {coll_repr(self)}'
    def __eq__(self,b): return all_equal(b,self)
    def __getitem__(self, idx):
        if is_iter(idx): return [self.items[i] for i in mask2idxs(idx)]
        return self.items[idx]

class DataSource():
    "Applies a `Pipeline` of `tfms` to filtered subsets of `items`"
    def __init__(self, items, tfms=noop, filts=None):
        if filts is None: filts = [range_of(items)]
        ft = mask2idxs if isinstance(filts[0][0], bool) else noop
        self.filts = listify(ListContainer(ft(filt)) for filt in filts)
        self.items,self.tfm = ListContainer(items),Pipeline(tfms)
        self.tfm.setup(self)

    def __len__(self): return len(self.filts)
    def len(self, filt=0): return len(self.filts[filt])
    def __getitem__(self, i): return _DsrcSubset(self, i)
    def decode(self, o, filt=0, **kwargs): return self.tfm.decode(o, filt=filt, **kwargs)
    def decoded(self, idx, filt=0): return self.decode(self.get(idx,filt), filt)
    def __iter__(self): return (self[i] for i in range_of(self))
    def __eq__(self,b): return all_equal(b if isinstance(b,DataSource) else DataSource(b),self)
    def show(self, o, filt=0, **kwargs): return self.tfm.show(self.decode(o, filt), **kwargs)

    def get(self, idx, filt=0):
        "Value(s) at `idx` from filtered subset `filt`"
        it = self.items[self.filts[filt][idx]]
        return [self.tfm(o, filt=filt) for o in it] if is_listy(it) else self.tfm(it, filt=filt)

    def __repr__(self):
        res = f'{self.__class__.__name__}\n'
        return res + '\n'.join(f'{i}: {coll_repr(o)}' for i,o in enumerate(self))

DataSource.train,DataSource.valid = property(lambda x: x[0]),property(lambda x: x[1])

add_docs(
    DataSource,
    __len__="Number of filtered subsets",
    len="`len` of subset `filt`",
    __getitem__="Filtered subset `i`",
    decode="Decode `o` passing `filt`",
    decoded="Decoded version of `get`",
    __iter__="Iterator for each filtered subset",
    show="Call `tfm.show` on decoded `o`"
)

class _DsrcSubset:
    def __init__(self, dsrc, filt): self.dsrc,self.filt = dsrc,filt
    def __getitem__(self,i): return self.dsrc.get(i,self.filt)
    def decode(self, o): return self.dsrc.decode(o, self.filt)
    def __len__(self): return self.dsrc.len(self.filt)
    def __eq__(self,b): return all_equal(b,self)
    def __iter__(self): return (self[i] for i in range_of(self))
    def __repr__(self): return coll_repr(self)
    def show(self, o, **kwargs): return self.dsrc.show(o, self.filt, **kwargs)
    def show_at(self, i, **kwargs): return self.show(self[i], **kwargs)

class TfmList():
    def __init__(self, ttfms, tfm=noop):
        self.activ,self.ttfms = False,[Transforms(tfm) for tfm in listify(ttfms)]

    def __call__(self, o, **kwargs):
        if self.activ: return self.activ(o, **kwargs)
        return [t(o, **kwargs) for t in self.ttfms]

    def decode(self, o, **kwargs): return [t.decode(p, **kwargs) for p,t in zip(o,self.ttfms)]

    def setup(self, o):
        for tfm in self.ttfms:
            self.activ = tfm
            tfm.setup(o)
        self.activ=None

    def show(self, o, **kwargs): return show_xs(o, self.ttfms, **kwargs)
    def __repr__(self): return f'TfmList({self.ttfms})'

    @property
    def xt(self): return self.ttfms[0]
    @property
    def yt(self): return self.ttfms[1]