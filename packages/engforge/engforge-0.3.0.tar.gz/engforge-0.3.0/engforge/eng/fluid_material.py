from engforge.configuration import Configuration, forge
from engforge.components import Component, system_property, forge


import matplotlib
import random
import attr, attrs
import numpy
import inspect
import sys

import CoolProp
from CoolProp.CoolProp import PropsSI
import fluids
import abc


# TODO: add a exact fluid state (T,P) / (Q,P) in the concept of processes for each thermodynamic operation (isothermal,isobaric,heating...ect)

STD_PRESSURE = 1e5  # pa
STD_TEMP = 273 + 15


@forge
class FluidMaterial(Component):
    """Placeholder for pressure dependent material, defaults to ideal water"""

    P = attrs.field(default=STD_PRESSURE, type=float)
    T = attrs.field(default=STD_TEMP, type=float)

    @abc.abstractproperty
    def density(self):
        """default functionality, assumed gas with eq-state= gas constant"""
        return 1000.0

    @abc.abstractproperty
    def viscosity(self):
        """ideal fluid has no viscosity"""
        return 1e-10

    @abc.abstractproperty
    def surface_tension(self):
        return 1e-10

    # TODO: enthalpy


@forge
class IdealGas(FluidMaterial):
    """Material Defaults To Gas Properties, so eq_of_state is just Rgas, no viscosity, defaults to air"""

    gas_constant = attrs.field(default=287.0, type=float)

    @system_property
    def density(self) -> float:
        """default functionality, assumed gas with eq-state= gas constant"""
        return self.P / (self.gas_constant * self.T)

    @system_property
    def viscosity(self) -> float:
        """ideal fluid has no viscosity"""
        return 1e-10

    # @system_property
    # def surface_tension(self):
    #     return 0.0


IdealAir = type("IdealAir", (IdealGas,), {"gas_constant": 287.0})
IdealH2 = type("IdealH2", (IdealGas,), {"gas_constant": 4124.2})
IdealOxygen = type("IdealOxygen", (IdealGas,), {"gas_constant": 259.8})
IdealSteam = type("IdealSteam", (IdealGas,), {"gas_constant": 461.5})

# @forge
# class PerfectGas(FluidMaterial):
#     '''A Calorically Perfect gas with viscosity'''
#     eq_of_state = attrs.field()
#     P = attrs.field(default=STD_PRESSURE, type=float)

#     @system_property
#     def density(self):
#             '''default functionality, assumed gas with eq-state= gas constant'''
#         return self.eq_of_state.density(T=self.T,P=self.P)

#     @system_property
#     def viscosity(self):
#         '''ideal fluid has no viscosity'''
#         return self.eq_of_state.viscosity(T=self.T,P=self.P)


@forge
class CoolPropMaterial(FluidMaterial):
    """Uses coolprop equation of state"""

    material: str

    # TODO: handle phase changes with internal _quality that you can add heat to
    _surf_tension_K = None
    _surf_tension_Nm = None
    _state = None

    @property
    def state(self):
        if hasattr(self, "_force_state"):
            return self._force_state
        if self._state and not self.anything_changed:
            return self._state
        else:
            tsat = self.Tsat
            if abs(self.T - tsat) < 1e-4:
                self._state = ("Q", 0, "P", self.P, self.material)
            elif self.T > tsat:
                self._state = ("T|gas", self.T, "P", self.P, self.material)
            else:
                self._state = ("T|liquid", self.T, "P", self.P, self.material)

        return self._state

    @system_property
    def density(self) -> float:
        """default functionality, assumed gas with eq-state= gas constant"""
        return PropsSI("D", *self.state)

    @system_property
    def enthalpy(self) -> float:
        return PropsSI("H", *self.state)

    @system_property
    def viscosity(self) -> float:
        return PropsSI("V", *self.state)

    @system_property
    def surface_tension(self) -> float:
        """returns liquid surface tension"""
        if self._surf_tension_K and self._surf_tension_Nm:
            X = self._surf_tension_K
            Y = self._surf_tension_Nm
            l = Y[0]
            r = Y[-1]
            return numpy.interp(self.T, xp=X, fp=Y, left=l, right=r)

        self.debug("no surface tension model! returning 0")
        return 0.0

    @system_property
    def thermal_conductivity(self) -> float:
        """returns liquid thermal conductivity"""
        return PropsSI("CONDUCTIVITY", *self.state)

    @system_property
    def specific_heat(self) -> float:
        """returns liquid thermal conductivity"""
        return PropsSI("C", *self.state)

    @system_property
    def Tsat(self) -> float:
        return PropsSI("T", "Q", 0, "P", self.P, self.material)

    @system_property
    def Psat(self) -> float:
        try:
            return PropsSI("P", "Q", 0, "T", self.T, self.material)
        except:
            return numpy.nan

    def __call__(self, *args, **kwargs):
        """calls coolprop module with args adding the material"""
        args = (*args, self.material)
        return PropsSI(*args)


# TODO: add water suface tenstion
T_K = [
    273.15,
    278.15,
    283.15,
    293.15,
    303.15,
    313.15,
    323.15,
    333.15,
    343.15,
    353.15,
    363.15,
    373.15,
    423.15,
    473.15,
    523.15,
    573.15,
    623.15,
    647.25,
]
ST_NM = [
    0.0756,
    0.0749,
    0.0742,
    0.0728,
    0.0712,
    0.0696,
    0.0679,
    0.0662,
    0.0644,
    0.0626,
    0.0608,
    0.0589,
    0.0482,
    0.0376,
    0.0264,
    0.0147,
    0.0037,
    0.0,
]


Water = type(
    "Water",
    (CoolPropMaterial,),
    {"material": "Water", "_surf_tension_K": T_K, "_surf_tension_Nm": ST_NM},
)
Air = type("Air", (CoolPropMaterial,), {"material": "Air"})
Oxygen = type("Oxygen", (CoolPropMaterial,), {"material": "Oxygen"})
Hydrogen = type("Hydrogen", (CoolPropMaterial,), {"material": "Hydrogen"})
Steam = type(
    "Steam",
    (CoolPropMaterial,),
    {
        "material": "IF97:Water",
        "_surf_tension_K": T_K,
        "_surf_tension_Nm": ST_NM,
    },
)
SeaWater = type(
    "SeaWater",
    (CoolPropMaterial,),
    {"material": "MITSW", "_surf_tension_K": T_K, "_surf_tension_Nm": ST_NM},
)

# Create some useful mixed models


@forge
class CoolPropMixture(CoolPropMaterial):
    """coolprop mixture of two elements... can only use T/Q, P/Q, T/P calls to coolprop"""

    material1 = "Air"
    materail2 = "Water"
    _X = 1.0  # 1.0 > mole fraction of material > 0

    @system_property
    def material(self) -> str:
        Xm = self._X
        return f"{self.material1}[{Xm}]&{self.materail2}[{1.0-Xm}]"

    @classmethod
    def setup(cls):
        try:
            CoolProp.apply_simple_mixing_rule(cls.material, cls.material2, "linear")
        except Exception as e:
            pass
            # self.error(e,'issue setting mixing rule, but continuting.')

    @system_property
    def Mmass1(self) -> float:
        return PropsSI("M", "T", self.T, "P", self.P, self.material1)

    @system_property
    def Mmass2(self) -> float:
        return PropsSI("M", "T", self.T, "P", self.P, self.material2)

    def update_mass_ratios(self, m1, m2):
        """add masses or massrates and molar ratio will be updated"""
        x1 = m1 / self.Mmass1
        x2 = m2 / self.Mmass2
        xtot = x1 + x2
        self._X = x1 / xtot


AirWaterMix = type("AirWaterMix", (CoolPropMixture,), {})
AirWaterMix.setup()
