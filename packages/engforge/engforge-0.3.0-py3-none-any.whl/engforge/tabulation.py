"""Tabulation Module:

Incrementally records attrs input values and system_properties per save_data() call.

save_data() is called after item.eval() is called.
"""

from contextlib import contextmanager
import attr

from engforge.common import inst_vectorize, chunks

# from engforge.configuration import Configuration, forge
from engforge.solveable import SolveableMixin
from engforge.logging import LoggingMixin
from engforge.dataframe import DataframeMixin
from engforge.typing import *
from engforge.properties import *
from typing import Callable

import numpy
import pandas
import os
import collections
import uuid


class TableLog(LoggingMixin):
    pass


log = TableLog()

# SKIP_REF = ["run_id", "converged", "name", "index"]
SKIP_REF = ["name", "index"]


class TabulationMixin(SolveableMixin, DataframeMixin):
    """In which we define a class that can enable tabulation"""

    # Super Special Tabulating Index
    # index = 0  # Not an attr on purpose, we want pandas to provide the index

    # override per class:
    _skip_table_vars: list = None
    _skip_plot_vars: list

    # Cached and private
    # _table: dict = None
    _anything_changed: bool = True
    _always_save_data = False

    def __getstate__(self):
        """remove references and storage of properties, be sure to call super if overwriting this function in your subclass"""
        vs = super().__getstate__()
        pir = vs.pop("_prv_internal_references", None)
        pir = vs.pop("_system_properties_def", None)
        pir = vs.pop("parent", None)

        return vs

    @property
    def anything_changed(self):
        """use the on_setattr method to determine if anything changed,
        also assume that stat_tab could change without input changes"""
        if not hasattr(self, "_anything_changed"):
            self._anything_changed = True

        if self._anything_changed or self.always_save_data:
            if self.log_level <= 5:
                self.msg(
                    f"change: {self._anything_changed}| always: {self.always_save_data}"
                )
            return True
        return False

    @property
    def last_context(self):
        """Returns the last context"""
        raise NotImplemented("this should be implemented in the solvable class")

    # TODO: create an intelligent graph informed anything_changed alerting system (pyee?) and trigger solver_cache expirations appropriately
    # @solver_cached #FIXME: not caching correctly
    @property  # FIXME: this is slow
    def dataframe(self):
        """
        Returns a pandas DataFrame based on the current context.

        This method checks for the presence of `last_context` and its `dataframe` attribute.
        If they exist, it returns the `dataframe` from `last_context`.
        If not, it checks for the `_patch_dataframe` attribute and returns it if it exists.
        If neither condition is met, it returns an empty DataFrame.

        :return: A pandas DataFrame based on the current context or an empty DataFrame if no context is available.
        :rtype: pandas.DataFrame
        """
        """"""
        if hasattr(self, "last_context") and hasattr(self.last_context, "dataframe"):
            return self.last_context.dataframe
        if hasattr(self, "_patch_dataframe") and self._patch_dataframe is not None:
            return self._patch_dataframe
        return pandas.DataFrame([])

    @dataframe.setter
    def dataframe(self, input_dataframe):
        if hasattr(self, "last_context") and hasattr(self.last_context, "dataframe"):
            raise Exception(f"may not set dataframe on run component")
        self._patch_dataframe = input_dataframe

    @property
    def plotable_variables(self):
        """Checks columns for ones that only contain numeric types or haven't been explicitly skipped"""
        if self.dataframe is not None:
            check_type = lambda key: all(
                [isinstance(v, NUMERIC_TYPES) for v in self.dataframe[key]]
            )
            check_non_mono = lambda key: len(set(self.dataframe[key])) > 1

            return [
                var
                for var in self.dataframe.columns
                if var.lower() not in self.skip_plot_vars
                and check_type(var)
                and check_non_mono(var)
            ]
        return []

    # Properties & Attribues
    def print_info(self):
        print(f"INFO: {self.name} | {self.identity}")
        print("#" * 80)
        for key, value in sorted(self.data_dict.items(), key=lambda kv: kv[0]):
            print(f"{key:>40} | {value}")

    @property
    def data_dict(self):
        """this is what is captured and used in each row of the dataframe / table"""
        # NOTE: Solver class overrides this with full system references
        out = collections.OrderedDict()
        sref = self.internal_references()
        for k, v in sref["attributes"].items():
            if k in self.attr_raw_keys:
                out[k] = v.value()
        for k, v in sref["properties"].items():
            out[k] = v.value()
        return out

    @instance_cached
    def attr_raw_keys(self) -> list:
        good = set(self.table_fields())
        return [k for k in attr.fields_dict(self.__class__).keys() if k in good]

    def set_attr(self, **kwargs):
        assert set(kwargs).issubset(set(self.attr_raw_keys))
        # TODO: support subcomponents via slots lookup
        for k, v in kwargs.items():
            setattr(self, k, v)

    @instance_cached
    def always_save_data(self):
        """Checks if any properties are stochastic (random)"""
        return self._always_save_data

    @solver_cached
    def table_dict(self):
        # We use __get__ to emulate the property, we could call regularly from self but this is more straightforward
        return {
            k.lower(): obj.__get__(self)
            for k, obj in self.system_properties_def.items()
        }

    @solver_cached
    def system_properties(self):
        # We use __get__ to emulate the property, we could call regularly from self but this is more straightforward
        tabulated_properties = [
            obj.__get__(self) for k, obj in self.system_properties_def.items()
        ]
        return tabulated_properties

    @instance_cached
    def system_properties_labels(self) -> list:
        """Returns the labels from table properties"""
        class_dict = self.__class__.__dict__
        tabulated_properties = [
            obj.label.lower() for k, obj in self.system_properties_def.items()
        ]
        return tabulated_properties

    @instance_cached
    def system_properties_types(self) -> list:
        """Returns the types from table properties"""
        class_dict = self.__class__.__dict__
        tabulated_properties = [
            obj.return_type for k, obj in self.system_properties_def.items()
        ]
        return tabulated_properties

    @instance_cached
    def system_properties_keys(self) -> list:
        """Returns the table property keys"""
        tabulated_properties = [k for k, obj in self.system_properties_def.items()]
        return tabulated_properties

    @instance_cached
    def system_properties_description(self) -> list:
        """returns system_property descriptions if they exist"""
        class_dict = self.__class__.__dict__
        tabulated_properties = [
            obj.desc for k, obj in self.system_properties_def.items()
        ]
        return tabulated_properties

    @classmethod
    def cls_all_property_labels(cls):
        return [obj.label for k, obj in cls.system_properties_classdef().items()]

    @classmethod
    def cls_all_property_keys(cls):
        return [k for k, obj in cls.system_properties_classdef().items()]

    @classmethod
    def cls_all_attrs_fields(cls):
        return attr.fields_dict(cls)

    @solver_cached
    def system_properties_def(self):
        """Combine other classes table properties into this one, in the case of subclassed system_properties as a property that is cached"""
        return self.__class__.system_properties_classdef()

    @classmethod
    def system_properties_classdef(cls, recache=False):
        """Combine other parent-classes table properties into this one, in the case of subclassed system_properties"""
        from engforge.tabulation import TabulationMixin

        cls_key = f"_{cls.__name__}_system_properties"
        # Use a cache for deep recursion
        if not recache and hasattr(cls, cls_key):
            res = getattr(cls, cls_key)
            if res is not None:
                return res

        # otherwise make the cache
        __system_properties = {}
        for k, obj in cls.__dict__.items():
            if isinstance(obj, system_property):
                __system_properties[k] = obj

        #
        mrl = cls.mro()
        inx_comp = mrl.index(TabulationMixin)

        # Ensures everything is includes Tabulation Functionality
        mrvs = mrl[1:inx_comp]

        for mrv in mrvs:
            # Remove anything not in the user code
            log.msg(f"adding system properties from {mrv.__name__}")
            if (
                issubclass(mrv, TabulationMixin)
                # and "engforge" not in mrv.__module__
            ):
                for k, obj in mrv.__dict__.items():
                    if k not in __system_properties and isinstance(
                        obj, system_property
                    ):  # Precedent
                        # Assumes our instance has assumed this table property
                        prop = getattr(cls, k, None)
                        if prop and isinstance(prop, system_property):
                            __system_properties[k] = prop
                            if log.log_level <= 3:
                                log.msg(f"adding system property {mrv.__name__}.{k}")

        setattr(cls, cls_key, __system_properties)

        return __system_properties

    @classmethod
    def pre_compile(cls):
        cls._anything_changed = True  # set default on class
        if any([v.stochastic for k, v in cls.system_properties_classdef(True).items()]):
            log.info(f"setting always save on {cls.__name__}")
            cls._always_save_data = True

    @property
    def system_id(self) -> str:
        """returns an instance unique id based on id(self)"""
        idd = id(self)
        return f"{self.classname}.{idd}"
