from progressivis.core.utils import ProgressiveError, indices_len, create_dataframe, fix_loc
from progressivis.core.dataframe import DataFrameModule
from progressivis.core.slot import SlotDescriptor

import numpy as np
import pandas as pd

class LinearRegression(DataFrameModule):
    schema = [('coef',      np.dtype(float), np.nan),
              ('intercept', np.dtype(float), np.nan),
              ('sum_x',     np.dtype(float), np.nan),
              ('sum_x_sqr', np.dtype(float), np.nan),
              ('sum_y',     np.dtype(float), np.nan),
              ('sum_xy',    np.dtype(float), np.nan),
              DataFrameModule.UPDATE_COLUMN_DESC]
    def __init__(self, x_column, y_column, **kwds):
        self._x = x_column
        self._y = y_column
        self._add_slots(kwds,'input_descriptors',
                        [SlotDescriptor('inp', type=pd.DataFrame)])
        super(LinearRegression, self).__init__(dataframe_slot='inp', **kwds)
        self.default_step_size = 10000

        self._df = create_dataframe(LinearRegression.schema)

    def is_ready(self):
        if self.get_input_slot('df').has_created():
            return True
        return super(LinearRegression, self).is_ready()

    def run_step(self,run_number,step_size,howlong):
        dfslot = self.get_input_slot('df')
        input_df = dfslot.data()
        dfslot.update(run_number)
        if dfslot.has_updated() or dfslot.has_deleted():
            raise ProgressiveError('%s module does not manage updates or deletes', self.__class__.__name__)

        indices = dfslot.next_created(step_size)
        steps = indices_len(indices)
        if steps == 0:
            return self._return_run_step(self.state_blocked, steps_run=steps)

        (x, y) = input_df.loc[fix_loc(indices),[self._x, self._y]]
        df = self._df
        sum_x     = df.at[0, 'sum_x']     + x.sum() 
        sum_x_sqr = df.at[0, 'sum_x_sqr'] + (x*x).sum()
        sum_y     = df.at[0, 'sum_y']     + y.sum()
        sum_xy    = df.at[0, 'sum_xy']    + (x*y).sum()
        denom = len(x) * sum_x_sqr - sum_x*sum_x
        coef = (sum_y*sum_x_sqr - sum_x*sum_xy) / denom
        intercept = (len(x)*sum_xy - sum_x*sum_y) / denom
        df.loc[0] = [coef, intercept, sum_x, sum_x_sqr, sum_y, sum_xy, run_number]
        return self._return_run_step(dfslot.next_state(),
                                     steps_run=steps, reads=steps, updates=1)
        
