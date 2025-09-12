"""tests airfilter system operation by solving for airflow between filter and and fan"""

import unittest

from engforge.configuration import forge
from engforge.system import System
from engforge.components import Component
from engforge.attr_dynamics import Time
from engforge.attr_solver import Solver
from engforge.attr_signals import Signal
from engforge.attr_slots import Slot
from engforge.properties import *
from engforge.attr_plotting import *
from engforge.analysis import Analysis

from engforge._testing_components import *

from scipy.optimize import curve_fit, least_squares
import numpy as np
from matplotlib.pyplot import *

import attrs


class TestFilterSystem(unittest.TestCase):
    def setUp(self):
        self.af = Airfilter()

    def test_plot(self):
        N = 10
        self.af.run(throttle=np.linspace(0, 1, N), combos="*", slv_vars="*")
        fig = self.af.flow_curve()
        self.assertIsNotNone(fig)

        df = self.af.dataframe
        self.assertEqual(df.shape[0], N)

        dfv = self.af.dataframe_variants
        self.assertEqual(dfv.shape[0], N)
        self.assertIn("w", dfv.columns)
        self.assertIn("throttle", dfv.columns)

        dfc = self.af.dataframe_constants
        self.assertIsInstance(dfc, dict)

        self.assertEqual(df.shape[1], len(dfc) + dfv.shape[1])


class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.af = AirFilterAnalysis()

    def test_plot(self):
        self.af.run(throttle=np.linspace(0, 1, 10), combos="*", slv_vars="*")
        fig = self.af.system.flow_curve()
        ofig = self.af._stored_plots["airfilteranalysis.airfilter.flow_curve"]
        print(fig)
        print(ofig)

        self.assertIsNotNone(fig)
        self.assertIsNotNone(ofig)


# #Run the system
# from matplotlib.pylab import *
#
#
#
# fan = Fan()
# filt = Filter()
# af = Airfilter(fan=fan,filt=filt)
#
# change_all_log_levels(af,20) #info
#
# af.run(throttle=list(np.arange(0.1,1.1,0.1)),combos='*')
#
# df = af.dataframe
#
# fig,(ax,ax2) = subplots(2,1)
# ax.plot(df.throttle*100,df.w,'k--',label='flow')
# ax2.plot(df.throttle*100,df.filt_dp_filter,label='filter')
# ax2.plot(df.throttle*100,df.dp_parasitic,label='parasitic')
# ax2.plot(df.throttle*100,df.fan_dp_fan,label='fan')
# ax.legend(loc='upper right')
# ax.set_title('flow')
# ax.grid()
# ax2.legend()
# ax2.grid()
# ax2.set_title(f'pressure')
# ax2.set_xlabel(f'throttle%')        dfv = self.af.dataframe_variants
# self.assertEqual(dfv.shape[0],N)
