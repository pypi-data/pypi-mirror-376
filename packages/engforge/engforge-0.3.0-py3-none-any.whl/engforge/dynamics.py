"""Combines the tabulation and component mixins to create a mixin for systems and components that have dynamics, such as state space models, while allowing nonlinear dynamics via matrix modification

This module is intended to work alongside the solver module and the Time integrating attributes, and will raise an error if a conflict is detected.

The DynamicsMixin works by establishing a state matricies A, B, C, and D, which are used to define the dynamics of the system. The state matrix A is the primary matrix, and is used to define the state dynamics of the system. The input matrix B is used to define the input dynamics of the system. The output matrix C is used to define the output dynamics of the system. The feedthrough matrix D is used to define the feedthrough dynamics of the system.

As opposed to the Time attribute, which modifies the state of the system, the DynamicsMixin copies the initial values of the state and input which then are integrated over time. At predefined intervals the control and output will stored in the tabulation.

#TODO: The top level system will collect the underlying dynamical systems and combine them to an index and overall state space model. This will allow for the creation of a system of systems, and the ability to create a system of systems with a single state space model.

#TODO: integration is done by the solver, where DynamicSystems have individual solver control, solver control is set for a smart default scipy
"""

from engforge.configuration import Configuration, forge
from engforge.tabulation import TabulationMixin
from engforge import properties as prop
from engforge.attributes import ATTR_BASE
from engforge.properties import instance_cached, solver_cached
from engforge.system_reference import Ref
from engforge.problem_context import ProblemExec
from engforge.solveable import (
    SolveableMixin,
    refmin_solve,
    refset_get,
    refset_input,
)


from collections import OrderedDict
import numpy as np
import pandas
import attr, attrs


# Index maps are used to translate between different indexes (local & global)


def valid_mtx(arr):
    if arr is None:
        return False
    elif arr.size == 0:
        return 0
    return True


##TODO: compile problems using index_map
# TODO: move to problem module
class INDEX_MAP:
    oppo = {str: int, int: str}

    def __init__(self, datas: list):
        self.data = [data if not data.startswith(".") else data[1:] for data in datas]
        self.index = {}

    def get(self, key):
        if key.startswith("."):
            key = key[1:]
        if key not in self.index:
            self.index[key] = self.data.index(key)
        return self.index[key]

    def __getitem__(self, key):
        if key.startswith("."):
            key = key[1:]
        return self.get(key)

    def __call__(self, key):
        if key.startswith("."):
            key = key[1:]
        return self.get(key)

    @staticmethod
    def indify(arr, *args):
        return [arr[arg] if isinstance(arg, int) else arr.index(arg) for arg in args]

    def remap_indexes_to(self, new_index, *args, invert=False, old_data=None):
        if old_data is None:
            old_data = self.data
        opt1 = {arg: self.indify(old_data, arg)[0] for arg in args}
        opt2 = {
            arg: (self.indify(old_data, val)[0] if (not isinstance(val, str)) else val)
            for arg, val in opt1.items()
        }
        oop1 = {arg: self.indify(new_index, val)[0] for arg, val in opt2.items()}
        oop2 = {
            arg: (
                self.indify(new_index, val)[0]
                if (invert != isinstance(val, self.oppo[arg.__class__]))
                else val
            )
            for arg, val in oop1.items()
        }
        return oop2


# Quickly create a state space model
# TODO: How to add delay, and feedback?
# TODO: How to add control and limits in general?
# TODO: add time as a state variable
@forge
class DynamicsMixin(Configuration, SolveableMixin):
    """dynamic mixin for components and systems that have dynamics, such as state space models, while allowing nonlinear dynamics via matrix modification. This mixin is intended to work alongside the solver module and the Time integrating attributes, and will raise an error if a conflict is detected #TODO."""

    # time: float = attrs.field(default=0.0)

    dynamic_state_vars: list = []  # attrs.field(factory=list)
    dynamic_input_vars: list = []  # attrs.field(factory=list)
    dynamic_output_vars: list = []  # attrs.field(factory=list)

    # state variables
    dynamic_A = None
    dynamic_B = None
    dynamic_C = None
    dynamic_D = None
    dynamic_F = None
    dynamic_K = None

    # Static linear state
    static_A = None
    static_B = None
    static_C = None
    static_D = None
    static_F = None
    static_K = None

    # TODO:
    # dynamic_control_module = None
    # control_interval:float = 0.0 ##TODO: how often to update the control
    # TODO: how often to update the physics, 0 is everytime
    update_interval: float = 0
    # delay_ms: float = attrs.field(default=None)
    nonlinear: bool = False

    # TODO: add integration state dynamic cache to handle relative time steps
    # TODO: add control module with PID control and pole placement design

    #### State Space Model
    def __pre_init__(self, **kwargs):
        """override this method to define the class"""
        # fields =
        fields = attrs.fields_dict(self.__class__)
        system_property = self.system_properties_def
        for p in self.dynamic_state_vars:
            assert p in fields, f"state var {p} not in attr: {fields}"
        for p in self.dynamic_output_vars:
            assert p in fields, f"output var {p} not in attr: {fields}"
        for p in self.dynamic_input_vars:
            assert p in fields, f"input var {p} not in attr: {fields}"

    @property
    def time(self):
        # convience function
        ctx = getattr(self, "last_context", None)
        if ctx:
            time = getattr(ctx, "_time", 0)
        else:
            time = 0
        return time

    @instance_cached
    def is_dynamic(self):
        if self.dynamic_state_vars:
            return True
        return False

    @instance_cached
    def dynamic_state_size(self):
        return len(self.dynamic_state_vars)

    @instance_cached
    def dynamic_input_size(self):
        return len(self.dynamic_input_vars)

    @instance_cached
    def dynamic_output_size(self):
        return len(self.dynamic_output_vars)

    @property
    def dynamic_state(self) -> np.array:
        return np.array([getattr(self, var, np.nan) for var in self.dynamic_state_vars])

    @property
    def dynamic_input(self) -> np.array:
        return np.array([getattr(self, var, np.nan) for var in self.dynamic_input_vars])

    @property
    def dynamic_output(self) -> np.array:
        return np.array(
            [getattr(self, var, np.nan) for var in self.dynamic_output_vars]
        )

    def create_state_matrix(self, **kwargs) -> np.ndarray:
        """creates the state matrix for the system"""
        return np.zeros((self.dynamic_state_size, self.dynamic_state_size))

    def create_input_matrix(self, **kwargs) -> np.ndarray:
        """creates the input matrix for the system, called B"""
        return np.zeros((self.dynamic_state_size, max(self.dynamic_input_size, 1)))

    def create_output_matrix(self, **kwargs) -> np.ndarray:
        """creates the input matrix for the system, called C"""
        return np.zeros((max(self.dynamic_output_size, 1), self.dynamic_state_size))

    def create_feedthrough_matrix(self, **kwargs) -> np.ndarray:
        """creates the input matrix for the system, called D"""
        return np.zeros(
            (max(self.dynamic_output_size, 1), max(self.dynamic_input_size, 1))
        )

    def create_state_constants(self, **kwargs) -> np.ndarray:
        """creates the input matrix for the system, called F"""
        return np.zeros(self.dynamic_state_size)

    def create_output_constants(self, **kwargs) -> np.ndarray:
        """creates the input matrix for the system, called O"""
        return np.zeros(self.dynamic_output_size)

    def create_dynamic_matricies(self, **kw):
        """creates a dynamics object for the system"""
        # State + Control
        self.static_A = self.create_state_matrix(**kw)
        self.static_B = self.create_input_matrix(**kw)
        # Output
        self.static_C = self.create_output_matrix(**kw)
        self.static_D = self.create_feedthrough_matrix(**kw)
        # Constants
        self.static_F = self.create_state_constants(**kw)
        self.static_K = self.create_output_constants(**kw)

        if self.nonlinear:
            self.update_dynamics(0, self.dynamic_state, self.dynamic_input)

    # Nonlinear Support
    # Override these callbacks to modify the state space model
    def update_state(self, t, A, X) -> np.ndarray:
        """override"""
        return A

    def update_input(self, t, B, X, U) -> np.ndarray:
        """override"""
        return B

    def update_output_matrix(self, t, C, X) -> np.ndarray:
        """override"""
        return C

    def update_feedthrough(self, t, D, X, U) -> np.ndarray:
        """override"""
        return D

    def update_state_constants(self, t, F, X) -> np.ndarray:
        """override"""
        return F

    def update_output_constants(self, t, O, X) -> np.ndarray:
        """override"""
        return O

    def update_dynamics(self, t, X, U):
        """Updates dynamics when nonlinear is enabled, otherwise it will do nothing"""
        if not self.nonlinear:
            return

        # try: #NOTE: try catch adds a lot of overhead
        # State + Control
        self.dynamic_A = self.update_state(t, self.static_A, X)
        self.dynamic_B = self.update_input(t, self.static_B, X, U)

        # Output
        self.dynamic_C = self.update_output_matrix(t, self.static_C, X)
        self.dynamic_D = self.update_feedthrough(t, self.static_D, X, U)

        # Constants
        self.dynamic_F = self.update_state_constants(t, self.static_F, X)
        self.dynamic_K = self.update_output_constants(t, self.static_K, X)

        if self.log_level <= 4:
            self.info(
                f"update_dynamics A:{self.dynamic_A} B:{self.dynamic_B} C:{self.dynamic_C} D:{self.dynamic_D} F:{self.dynamic_F} K:{self.dynamic_K}| time:{t} X:{X} U:{U}"
            )

        # except Exception as e:
        #     self.warning(f'update dynamics failed! A:{self.dynamic_A} B:{self.dynamic_B} C:{self.dynamic_C} D:{self.dynamic_D} F:{self.dynamic_F} K:{self.dynamic_K}| time:{t} X:{X} U:{U}')
        #     raise e

    # linear and nonlinear system level IO

    def rate(self, t, dt, X, U, *args, **kwargs):
        """simulate the system over the course of time.

        Args:
            dt (float): interval to integrate over in time
            X (np.ndarray): state input
            U (np.ndarray): control input
            subsystems (bool, optional): simulate subsystems. Defaults to True.

        Returns:
            dataframe: tabulated data
        """
        if self.nonlinear:
            return self.rate_nonlinear(t, dt, X, U, *args, **kwargs)
        else:
            return self.rate_linear(t, dt, X, U, *args, **kwargs)

    def rate_linear(self, t, dt, X, U=None):
        """simulate the system over the course of time. Return time differential of the state."""

        O = 0
        if valid_mtx(self.static_A) and valid_mtx(X):
            O = self.static_A @ X

        if valid_mtx(U) and valid_mtx(self.static_B):
            O += self.static_B @ U

        if valid_mtx(self.static_F):
            O += self.static_F

        return O

    def linear_output(self, t, dt, X, U=None):
        """simulate the system over the course of time. Return time differential of the state.

        Args:
            dt (float): interval to integrate over in time
            X (np.ndarray): state input
            U (np.ndarray): control input

        Returns:
            np.array: time differential of the state
        """
        O = 0
        if valid_mtx(self.static_C) and valid_mtx(X):
            O = self.static_C @ X

        if valid_mtx(U) and valid_mtx(self.static_D):
            O += self.static_D @ U

        if valid_mtx(self.static_K):
            O += self.static_K
        return O

    def rate_nonlinear(self, t, dt, X, U=None, update=True):
        """simulate the system over the course of time. Return time differential of the state.

        Args:
            t (float): time
            dt (float): interval to integrate over in time
            X (np.ndarray): state input
            U (np.ndarray): control input

        Returns:
            np.array: time differential of the state
        """
        if update:
            self.update_dynamics(t, X, U)

        O = 0
        if valid_mtx(self.dynamic_A) and valid_mtx(X):
            O = O + self.dynamic_A @ X

        if valid_mtx(U) and valid_mtx(self.dynamic_B):
            O = O + self.dynamic_B @ U

        if valid_mtx(self.dynamic_F):
            O = O + self.dynamic_F
        return O

    def nonlinear_output(self, t, dt, X, U=None, update=True):
        """simulate the system over the course of time. Return time differential of the state.

        Args:
            dt (float): interval to integrate over in time
            X (np.ndarray): state input
            U (np.ndarray): control input

        Returns:
            np.array: time differential of the state
        """
        if update:
            self.update_dynamics(t, X, U)

        O = 0
        if valid_mtx(self.dynamic_C) and valid_mtx(X):
            O = O + self.dynamic_C @ X

        if valid_mtx(U) and valid_mtx(self.dynamic_D):
            O = O + self.dynamic_D @ U

        if valid_mtx(self.dynamic_K):
            O = O + self.dynamic_K
        return O

    def set_time(self, t, system=True, subcomponents=True):
        """sets the time of the system and context"""
        pass
        # set components
        # if subcomponents:
        #    for cdyn_name, comp in self.comp_times.items():
        #        comp.set_value(t)

        # if system: #set system time only
        #     self.time = t

        # @instance_cached #TODO: cache on solver due to changes of components
        # def comp_times(self) -> dict:
        """returns a dictionary of time references to components which will be set to the current time"""
        # return {k: Ref(comp,'time',False,True) for k,l,comp in self.go_through_configurations() if isinstance(comp,DynamicsMixin)}

    # optimized convience funcitons
    def nonlinear_step(self, t, dt, X, U=None, set_Y=False):
        """Optimal nonlinear steps"""
        # self.time = t #important for simulation, moved to context.integrate
        self.update_dynamics(t, X, U)

        dXdt = self.rate_nonlinear(t, dt, X, U, update=False)
        out = self.nonlinear_output(t, dt, X, U, update=False)

        if set_Y:
            for i, p in enumerate(self.dynamic_output_vars):
                self.Yt_ref[p].set_value(out[p])

        return dXdt

    def linear_step(self, t, dt, X, U=None, set_Y=False):
        """Optimal nonlinear steps"""
        # self.time = t #important for simulation, moved to context.integrate
        self.update_dynamics(t, X, U)
        dXdt = self.rate_linear(t, dt, X, U)
        out = self.linear_output(t, dt, X, U)

        if set_Y:
            for i, p in enumerate(self.dynamic_output_vars):
                self.Yt_ref[p].set_value(out[p])

        return dXdt

    def step(self, t, dt, X, U=None, set_Y=False):
        try:
            if self.nonlinear:
                return self.nonlinear_step(t, dt, X, U, set_Y=set_Y)
            else:
                return self.linear_step(t, dt, X, U, set_Y=set_Y)

        except Exception as e:
            self.warning(
                f"update dynamics failed {e}! A:{self.dynamic_A} B:{self.dynamic_B} C:{self.dynamic_C} D:{self.dynamic_D} F:{self.dynamic_F} K:{self.dynamic_K}| time:{t} X:{X} U:{U} setY:{set_Y}"
            )
            raise e

    # Solver Refs
    # TODO: move to problem context
    @property
    def Xt_ref(self):
        """alias for state values"""
        d = [(var, Ref(self, var)) for var in self.dynamic_state_vars]
        return OrderedDict(d)

    @property
    def Yt_ref(self):
        """alias for output values"""
        d = [(var, Ref(self, var)) for var in self.dynamic_output_vars]
        return OrderedDict(d)

    @property
    def Ut_ref(self):
        """alias for input values"""
        d = [(var, Ref(self, var)) for var in self.dynamic_input_vars]
        return OrderedDict(d)

    @property
    def dXtdt_ref(self):
        """a dictionary of state var rates"""
        d = [(var, self.ref_dXdt(var)) for var in self.dynamic_state_vars]
        return OrderedDict(d)

    @solver_cached
    def cache_dXdt(self):
        """caches the time differential of the state,
        uses current state of X and U to determine the dXdt
        """

        # we need to check the active session to determine if we should refresh the problem matrix
        if hasattr(ProblemExec.class_cache, "session"):
            session = ProblemExec.class_cache.session
            if session and session.dynamic_solve and self.is_dynamic:
                if (
                    session.dxdt != True
                ):  # integration update is handeled, all others are some kind of SS.
                    self.create_dynamic_matricies()

        ctx = getattr(self, "last_context", None)

        if ctx:
            time = getattr(ctx, "_time", 0)
            lt = getattr(ctx, "_last_time", 0)
        else:
            time = 0
            lt = 0

        dt = max(time - lt, 0)
        step = self.step(time, dt, self.dynamic_state, self.dynamic_input)
        if self.log_level <= 10:
            self.debug(f"cache dXdt {time} {lt} {dt}| {step}")
        return step

    def ref_dXdt(self, name: str):
        """returns the reference to the time differential of the state"""
        vars = self.dynamic_state_vars
        assert name in vars, f"name {name} not in state vars"
        inx = vars.index(name)
        accss = lambda sys, prob: self.cache_dXdt[inx]
        accss.__name__ = f"ref_dXdt_{name}"
        return Ref(self, accss)

    def determine_nearest_stationary_state(self, t=0, X=None, U=None) -> np.ndarray:
        """determine the nearest stationary state"""

        if X is None:
            X = self.dynamic_state
        if U is None:
            U = self.dynamic_input

        if self.nonlinear:
            self.update_dynamics(t, X, U)
            Mb = self.dynamic_B @ U if self.dynamic_input_size > 0 else 0
            Mx = self.dynamic_F + Mb
            return np.linalg.solve(self.dynamic_A, -Mx)

        # static state
        Mb = self.static_B @ U if self.dynamic_input_size > 0 else 0
        Mx = Mb + self.static_F
        return np.linalg.solve(self.static_A, -Mx)

    def __hash__(self):
        return hash(id(self))


@forge
class GlobalDynamics(DynamicsMixin):
    """This object is inherited by configurations that collect other dynamicMixins and orchestrates their simulation, and steady state analysis

    #TODO: establish bounds in solver
    """

    def setup_global_dynamics(self, **kwargs):
        """recursively creates numeric matricies for the simulation"""
        for skey, lvl, conf in self.go_through_configurations():
            if isinstance(conf, DynamicsMixin) and conf.is_dynamic:
                conf.create_dynamic_matricies(**kwargs)

    def sim_matrix(self, eval_kw=None, sys_kw=None, **kwargs):
        """simulate the system over the course of time.
        return a dictionary of dataframes
        """
        #
        # from engforge.solver import SolveableMixin

        dt = kwargs.pop("dt", 0.001)
        endtime = kwargs.pop("endtime", 10)

        with ProblemExec(
            self, kwargs, level_name="simmtx", dxdt=True, copy_system=True
        ) as pbx:
            if isinstance(self, SolveableMixin):
                # adapt simulate to use the solver
                sim = lambda Xo, *args, **kw: self.simulate(
                    dt, endtime, Xo, eval_kw=eval_kw, sys_kw=sys_kw, **kw
                )
                out = self._iterate_input_matrix(
                    sim,
                    eval_kw=eval_kw,
                    sys_kw=sys_kw,
                    return_results=True,
                    **kwargs,
                )
            else:
                out = self.simulate(dt, endtime, eval_kw=eval_kw, sys_kw=sys_kw)
        return out

    # TODO: swap between vars and constraints depending on dxdt=True
    def simulate(
        self,
        dt,
        endtime,
        X0=None,
        cb=None,
        eval_kw=None,
        sys_kw=None,
        min_kw=None,
        run_solver=False,
        return_system=False,
        return_data=False,
        return_all=False,
        debug_fail=False,
        **kwargs,
    ) -> pandas.DataFrame:
        """runs a simulation over the course of time, and returns a dataframe of the results.

        A copy of this system is made, and the simulation is run on the copy, so as to not affect the state of the original system.

        #TODO:
        """
        min_kw_dflt = {"method": "SLSQP"}
        #'tol':1e-6,'options':{'maxiter':100}}
        # min_kw_dflt = {'doset':True,'reset':False,'fail':True}
        if min_kw is None:
            min_kw = min_kw_dflt.copy()
        else:
            min_kw_dflt.update(min_kw)
        mkw = min_kw_dflt

        # force transient
        kwargs["dxdt"] = True

        # variables if failed
        pbx, system = None, self
        try:
            # Time Iteration Context
            data = []
            with ProblemExec(
                system,
                kwargs,
                level_name="sim",
                dxdt=True,
                copy_system=True,
                run_solver=run_solver,
                post_callback=cb,
            ) as pbx:
                self._sim_ans = pbx.integrate(
                    endtime=endtime,
                    dt=dt,
                    X0=X0,
                    eval_kw=eval_kw,
                    sys_kw=sys_kw,
                    **kwargs,
                )
                system = pbx.system  # hello copy

                # data = [{"time": k, **v} for k, v in  pbx.data.items()]

                # this will affect the context copy, not self
                pbx.exit_to_level("sim", False)

            # convert to list with time
            # df = pandas.DataFrame(data)
            # self.format_columns(df)
            df = pbx.dataframe

            # TODO: move to context
            if return_all:
                return system, (data if return_data else df)
            if return_system:
                return system
            if return_data:
                return data
            return df

        except Exception as e:
            self.error(e, f"simulation failed, return (sys,prob)")
            if debug_fail:
                return system, pbx
            raise e
