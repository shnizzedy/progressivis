from progressive.core.common import ProgressiveError
from progressive.core.dataframe import DataFrameModule
from progressive.core.slot import SlotDescriptor

import numpy as np
import pandas as pd

import logging
logger = logging.getLogger(__name__)

class Histogram2d(DataFrameModule):
    parameters = [('xbins',  np.dtype(int),   1024),
                  ('ybins',  np.dtype(int),   1024),
                  ('xmin',   np.dtype(float), 0),
                  ('xmax',   np.dtype(float), 1),
                  ('ymin',   np.dtype(float), 0),
                  ('ymax',   np.dtype(float), 1),
                  ('xdelta', np.dtype(float), 0),
                  ('ydelta', np.dtype(float), 0),
                  ('history',np.dtype(int),   3) ]

    schema = [('array', np.dtype(object), None),
              ('cmin', np.dtype(float), np.nan),
              ('cmax', np.dtype(float), np.nan),
              DataFrameModule.UPDATE_COLUMN_DESC]

    def __init__(self, x_column, y_column, **kwds):
        self._add_slots(kwds,'input_descriptors',
                        [SlotDescriptor('df', type=pd.DataFrame)])
        super(Histogram2d, self).__init__(dataframe_slot='histogram2d', **kwds)
        self.x_column = x_column
        self.y_column = y_column
        self.default_step_size = 10000
        self.total_read = 0
        self._df = self.create_dataframe(Histogram2d.schema)

    def is_ready(self):
        if not self.get_input_slot('df').is_buffer_empty():
            return True
        return super(Histogram2d, self).is_ready()

    def run_step(self,run_number,step_size,howlong):
        dfslot = self.get_input_slot('df')
        input_df = dfslot.data()
        df = self._df
        old_histo = df.at[df.index[-1], 'array']
        dfslot.update(run_number, input_df)
        if len(dfslot.deleted) or len(dfslot.updated) > len(dfslot.created):
            dfslot.reset()
            old_histo = None
            self.total_read = 0
            logger.info('Reseting history because of changes in the input')
            #raise ProgressiveError('%s module does not manage updates or deletes', self.__class__.__name__)

        dfslot.buffer_created()

        indices = dfslot.next_buffered(step_size)
        steps = len(indices)
        if steps == 0:
            logger.info('Index buffer empty')
            return self._return_run_step(self.state_blocked, steps_run=steps)
        else:
            self.total_read += steps
        x = input_df.loc[indices, self.x_column]
        y = input_df.loc[indices, self.y_column]
        p = self.params
        histo, xedges, yedges = np.histogram2d(y, x,
                                               bins=[p.xbins, p.ybins],
                                               range=[[p.xmin, p.xmax],[p.ymin, p.ymax]],
                                               normed=False)
        if old_histo is None:
            old_histo = histo
        else:
            old_histo += histo
        cmax = old_histo.max()
        values = [old_histo, 0, cmax, run_number]
        df.loc[run_number] = values
        if len(df) > p.history:
            self._df = df.loc[df.index[-p.history:]]
        return self._return_run_step(dfslot.next_state(),
                                     steps_run=steps, reads=steps, updates=len(self._df))
