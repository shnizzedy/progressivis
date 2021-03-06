from progressivis.core.utils import indices_len, last_row, fix_loc
from progressivis.core.dataframe import DataFrameModule
from progressivis.core.slot import SlotDescriptor
from progressivis.core.synchronized import synchronized

import numpy as np
import pandas as pd

import logging
logger = logging.getLogger(__name__)


class IdxMax(DataFrameModule):
    parameters = [('history', np.dtype(int), 3)]

    def __init__(self, **kwds):
        self._add_slots(kwds,'input_descriptors',
                        [SlotDescriptor('df', type=pd.DataFrame, required=True)])
        self._add_slots(kwds,'output_descriptors',
                        [SlotDescriptor('max', type=pd.DataFrame, required=False)])
        super(IdxMax, self).__init__(**kwds)
        self._max = None
        self.default_step_size = 10000

    def max(self):
        return self._max

    def get_data(self, name):
        if name=='max':
            return self.max()
        return super(IdxMax,self).get_data(name)

    def is_ready(self):
        if self.get_input_slot('df').has_created():
            return True
        return super(IdxMax, self).is_ready()

    @synchronized
    def run_step(self,run_number,step_size,howlong):
        dfslot = self.get_input_slot('df')
        dfslot.update(run_number)
        if dfslot.has_updated() or dfslot.has_deleted():        
            dfslot.reset()
            self._df = None
            dfslot.update(run_number)
        indices = dfslot.next_created(step_size) # returns a slice
        steps = indices_len(indices)
        if steps==0:
            return self._return_run_step(self.state_blocked, steps_run=0)
        input_df = dfslot.data()
        op = self.filter_columns(input_df, fix_loc(indices)).idxmax()

        op[self.UPDATE_COLUMN] = run_number
        if self._max is None:
            max = pd.Series([np.nan], index=op.index) # the UPDATE_COLUMN is included
            max[self.UPDATE_COLUMN] = run_number
            for col in op.index:
                if col==self.UPDATE_COLUMN: continue
                max[col] = input_df.loc[op[col], col] # lookup value, is there a better way?
            self._max = pd.DataFrame([max], columns=op.index)
            self._df = pd.DataFrame([op], columns=op.index)
        else:
            prev_max = last_row(self._max)
            prev_idx = last_row(self._df)
            max = pd.Series(prev_max)
            max[self.UPDATE_COLUMN] = run_number
            for col in op.index:
                if col==self.UPDATE_COLUMN: continue
                val = input_df.loc[op[col], col]
                if np.isnan(val):
                    pass
                elif np.isnan(max[col]) or val > max[col]:
                    op[col] = prev_idx[col]
                    max[col] = val
            op[self.UPDATE_COLUMN] = run_number
            with self.lock:
                self._df = self._df.append(op, ignore_index=True)
                self._max = self._max.append(max, ignore_index=True)
                if len(self._df) > self.params.history:
                    self._df = self._df.loc[self._df.index[-self.params.history:]]
                    self._max = self._max.loc[self._max.index[-self.params.history:]]

        return self._return_run_step(dfslot.next_state(), steps_run=steps)
