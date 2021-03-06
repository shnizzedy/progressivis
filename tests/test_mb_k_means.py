import unittest

from progressivis import Scheduler, Print, log_level, Every
from progressivis.cluster import MBKMeans
from progressivis.io import CSVLoader
from progressivis.datasets import get_dataset


from sklearn.cluster import MiniBatchKMeans
from sklearn.utils.extmath import squared_norm

import numpy as np
import pandas as pd

# times = 0

# def stop_if_done(s, n):
#     global times
#     if s.run_queue_length()==3:
#         if times==2:
#             s.stop()
#         times += 1


class TestMBKmeans(unittest.TestCase):
    def test_mb_k_means(self):
        #log_level()
        s=Scheduler()
        n_clusters = 3
        csv = CSVLoader(get_dataset('cluster:s3'),sep=' ',skipinitialspace=True,header=None,index_col=False,scheduler=s)
        km = MBKMeans(n_clusters=n_clusters, random_state=42, is_input=False, scheduler=s)
        km.input.df = csv.output.df
        pr = Print(scheduler=s)
        pr.input.df = km.output.df
        e = Every(scheduler=s)
        e.input.df = km.output.labels
        s.start()
        self.assertEquals(len(csv.df()), len(km.labels()))
        #mbk = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, verbose=True)
        #X = csv.df()[km.columns]
        #mbk.partial_fit(X)
        #print mbk.cluster_centers_
        #print km.mbk.cluster_centers_
        #self.assertTrue(np.allclose(mbk.cluster_centers_, km.mbk.cluster_centers_))


if __name__ == '__main__':
    unittest.main()

