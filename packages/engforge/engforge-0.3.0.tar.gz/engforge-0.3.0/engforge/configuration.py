import attr, attrs

from engforge.engforge_attributes import AttributedBaseMixin
from engforge.logging import LoggingMixin, log, change_all_log_levels
from engforge.properties import *
from engforge.env_var import EnvVariable
import randomname
import datetime
import copy


# make a module logger
class ConfigLog(LoggingMixin):
    pass


log = ConfigLog()

conv_nms = lambda v: v.split(",") if isinstance(v, str) else v
NAME_ADJ = EnvVariable(
    "FORGE_NAME_ADJ",
    default=(
        "geometry",
        "size",
        "algorithms",
        "complexity",
        "colors",
        "materials",
    ),
    type_conv=conv_nms,
)
NAME_NOUN = EnvVariable(
    "FORGE_NAME_NOUN",
    default=(
        "chemistry",
        "astronomy",
        "linear_algebra",
        "geometry",
        "coding",
        "corporate_job",
        "design",
        "car_parts",
        "machine_learning",
        "physics_units",
    ),
    type_conv=conv_nms,
)
FORGE_DEBUG = EnvVariable(
    "FORGE_LOG_LEVEL",
    default=20,
    type_conv=int,
)


def name_generator(instance):
    """a name generator for the instance"""
    base = str(instance.__class__.__name__).lower() + "-"
    if instance.__class__._use_random_name:
        out = base + randomname.get_name(adj=NAME_ADJ.secret, noun=NAME_NOUN.secret)
    else:
        out = base
    log.debug(f"generated name: {out}")
    return out


PROTECTED_NAMES = [
    "solver",
    "dataframe",
    "_anything_changed",
    "time",
    "run_id",
    "converged",
]


# Wraps Configuration with a decorator, similar to @attrs.define(**options)
def forge(cls=None, **kwargs):
    """Wrap all Configurations with this decorator with the following behavior
    1) we use the callback when any property changes
    2) repr is default
    3) hash is by object identity"""

    # Define defaults and handle conflicts
    dflts = dict(repr=False, eq=False, slots=False, kw_only=True, hash=False)
    for k, v in kwargs.items():
        if k in dflts:
            dflts.pop(k)

    if cls is not None:
        # we can't import system here since cls might be system, so look for any system subclasses
        if "System" in [c.__name__ for c in cls.mro()]:
            log.info(f"Configuring System: {cls.__name__}")
            acls = attr.s(
                cls,
                on_setattr=property_changed,
                field_transformer=signals_slots_handler,
                **dflts,
                **kwargs,
            )

            # must be here since can't inspect till after fields corrected
            acls.pre_compile()  # custom class compiler
            acls.validate_class()
            if acls.__name__ != "Configuration":  # prevent configuration lookup
                acls.compile_classes()  # compile subclasses
            return acls

        # Component/Config Flow
        log.msg(f"Configuring: {cls.__name__}")
        acls = attr.s(
            cls,
            on_setattr=property_changed,
            field_transformer=comp_transform,
            **dflts,
            **kwargs,
        )
        if FORGE_DEBUG.in_env:
            change_all_log_levels(inst=acls, new_log_level=FORGE_DEBUG.secret)
        # must be here since can't inspect till after fields corrected
        acls.pre_compile()  # custom class compiler
        acls.validate_class()
        if acls.__name__ != "Configuration":  # prevent configuration lookup
            acls.compile_classes()  # compile subclasses
        return acls

    else:

        def f(cls, *args):
            return forge(cls, **kwargs)

        f.__name__ == "forge_wrapper"

        return f


def meta(title, desc=None, **kwargs):
    """a convienience wrapper to add metadata to attr.ib
    :param title: a title that gets formatted for column headers
    :param desc: a description of the property"""
    out = {
        "label": title.replace(".", "_").replace("-", "_").title(),
        "desc": None,
        **kwargs,
    }
    return out


# Class Definition Wrapper Methods
def property_changed(instance, variable, value):
    """a callback for when a property changes, this will set the _anything_changed flag to True, and change value when appropriate"""
    from engforge.tabulation import TabulationMixin
    from engforge.problem_context import ProblemExec

    # TODO: determine when, in an active problem if components change, and update refs accordingly!

    if not isinstance(instance, (TabulationMixin)):
        return value

    # Establish Active Session
    session = None
    if hasattr(ProblemExec.class_cache, "session"):
        session = ProblemExec.class_cache.session

    if not session and instance._anything_changed:
        # Bypass Check since we've already flagged for an update
        if log.log_level <= 2:
            log.debug(f"already property changed {instance}{variable.name} {value}")
        return value

    # elif session:
    # notify session that this variable has changed
    # log.info(f'property changed {variable.name} {value}')

    # TODO: notify change input system here, perhaps with & without a session
    # session.change_sys_var(variable,value,doset=False)
    attrs = attr.fields(instance.__class__)  # check identity of variable
    cur = getattr(instance, variable.name)
    is_different = value != cur if isinstance(value, (int, float, str)) else True
    is_var = variable in attrs
    chgnw = instance._anything_changed

    if log.log_level <= 6:
        log.debug(
            f"checking property changed {instance}{variable.name} {value}|invar: {is_var}| nteqval: {is_different}"
        )
        print(
            f"checking property changed {instance}{variable.name} {value}|invar: {is_var}| nteqval: {is_different}"
        )

    # Check if should be updated
    if not chgnw and is_var and is_different:
        if log.log_level < 5:
            log.debug(f"changing variables: {variable.name} {value}")
        instance._anything_changed = True

    elif log.log_level < 4 and is_var and not is_different:
        log.warning(f"variables same {variable.name}| {value} == {cur}")

    # If active session in dynamic mode and the component is dynamic, flag for matrix update
    # TODO: determine if dynamic matricies affected by this.
    if session and session.dynamic_solve and instance.is_dynamic:
        # log.info(f'dynamics changed')
        session.dynamics_updated = True  # flag for update

    elif session:
        # log.info(f'static change')
        session.dynamics_updated = False

    return value


# Class Definition Wrapper Methods
def signals_slots_handler(
    cls, fields, slots=True, signals=True, solvers=True, sys=True, plots=True
):
    """
    creates attributes as per the attrs.define field_transformer use case.

    Customize initalization with slots,signals,solvers and sys flags.
    """
    from engforge.problem_context import ProblemExec

    log.debug(f"transforming signals and slots for {cls.__name__}")

    # add attrs attributes from mro parent class
    # TODO: work on this to allow attrs from non attrs classes
    # fd = {f.name:f for f in fields}
    # has_fields = set(list(fd.keys()))
    #
    # if cls._inherit_parent_attributres:
    #     non_dec_attrs = {} #get all attrs variables from non-decorated mixins
    #     for icls in cls.mro():
    #         if attrs.has(icls):
    #             print(icls,str(list(attrs.fields_dict(icls).keys()))[:100])
    #         atr_dict = {k:v.evolve(icls) for k,v in icls.__dict__.items() if isinstance(v,attrs.Attribute)}
    #         non_dec_attrs.update({k:v for k,v in atr_dict.items() if k not in non_dec_attrs and k not in has_fields})
    #     if non_dec_attrs:
    #         log.info(f'adding non decorated attrs: {list(non_dec_attrs.keys())}')
    #         fields = fields + list(non_dec_attrs.values())

    # Fields
    for t in fields:
        if t.name in PROTECTED_NAMES:
            raise Exception(f"cannot use {t.name} as a field name, its protected")
        if t.type is None:
            log.warning(f"{cls.__name__}.{t.name} has no type")

    out = []
    field_names = set([o.name for o in fields])
    log.debug(f"fields: {field_names}")

    # Add Fields (no underscored fields)
    in_fields = {f.name: f for f in fields if not f.name.startswith("_")}
    if "name" in in_fields:
        name = in_fields.pop("name")
        out.append(name)

    else:
        log.warning(f"{cls.__name__} does not have a name!")
        name = attrs.Attribute(
            name="name",
            default=attrs.Factory(name_generator, True),
            validator=None,
            repr=True,
            cmp=None,
            eq=True,
            eq_key=None,
            order=True,
            order_key=None,
            hash=None,
            init=True,
            metadata=None,
            type=str,
            converter=None,
            kw_only=True,
            inherited=True,
            on_setattr=None,
            alias="name",
        )
        out.append(name)

    # Add Slots
    if slots:
        for slot_name, slot in cls.slots_attributes().items():
            at = slot.make_attribute(slot_name, cls)
            out.append(at)

    # Add Signals
    if signals:
        for signal_name, signal in cls.signals_attributes().items():
            at = signal.make_attribute(signal_name, cls)
            out.append(at)

    # Add SOLVERS
    if solvers:
        for solver_name, solver in cls.solvers_attributes().items():
            at = solver.make_attribute(solver_name, cls)
            out.append(at)

        # Add Time
        for solver_name, solver in cls.transients_attributes().items():
            # add from cls since not accessible from attrs
            at = solver.make_attribute(solver_name, cls)
            out.append(at)

    if plots:
        for pltname, plot in cls.plot_attributes().items():
            at = plot.make_attribute(pltname, cls)
            out.append(at)

        for pltname, plot in cls.trace_attributes().items():
            at = plot.make_attribute(pltname, cls)
            out.append(at)

    created_fields = set([o.name for o in out])

    # Merge Fields Checking if we are overriding an attribute with system_property
    # hack since TabulationMixin isn't available yet
    if "TabulationMixin" in str(cls.mro()):
        cls_properties = cls.system_properties_classdef(True)
    else:
        cls_properties = {}

    cls_dict = cls.__dict__.copy()
    cls.__anony_store = {}
    # print(f'tab found!! {cls_properties.keys()}')
    for k, o in in_fields.items():
        if k not in created_fields:
            if k in cls_properties and o.inherited:
                log.warning(
                    f"{cls.__name__} overriding inherited attr: {o.name} as a system property overriding it"
                )
            elif o.inherited and k in cls_dict:
                log.warning(
                    f"{cls.__name__} overriding inherited attr: {o.name} as {cls_dict[k]} in cls"
                )
                # FIXME: should we deepcopy?
                val = copy.copy(cls_dict[k])
                cls.__anony_store[k] = sscb = lambda: val
                out.append(o.evolve(default=attrs.Factory(sscb)))
            else:
                log.msg(f"{cls.__name__} adding attr: {o.name}")
                out.append(o)
        else:
            log.warning(
                f"{cls.__name__} skipping inherited attr: {o.name} as a custom type overriding it"
            )

    # Enforce Property Changing
    # FIXME: is this more reliable than a class wide callback?
    # real_out = []
    # for fld in out:
    #     if fld.type in (int,float,str):
    #         #log.warning(f"setting property changed on {fld}")
    #         fld = fld.evolve(on_setattr = property_changed)
    #         real_out.append(fld)
    #     else:
    #         real_out.append(fld)
    # #return real_out
    return out


# alternate initalisers
comp_transform = lambda c, f: signals_slots_handler(
    c, f, slots=True, signals=True, solvers=True, sys=False, plots=False
)


# TODO: Make A MetaClass for Configuration, and provide forge interface there. Problem with replaceing metaclass later, as in the case of a singleton.
@forge
class Configuration(AttributedBaseMixin):
    """Configuration is a pattern for storing attributes that might change frequently, and proivdes the core functionality for a host of different applications.

    Configuration is able to go through itself and its objects and map all included Configurations, just to a specific level.

    Common functionality includes an __on_init__ wrapper for attrs post-init method
    """

    _temp_vars = None

    _use_random_name: bool = True
    name: str = attr.ib(
        default=attrs.Factory(name_generator, True),
        validator=attr.validators.instance_of(str),
        kw_only=True,
    )

    _inherit_parent_attributres = True
    log_fmt = "[%(name)-24s]%(message)s"
    log_silo = True

    _created_datetime = None
    _subclass_init: bool = True

    # Configuration Information
    def internal_configurations(
        self, check_config=True, use_dict=True, none_ok=False
    ) -> dict:
        """go through all attributes determining which are configuration objects
        additionally this skip any configuration that start with an underscore (private variable)
        """
        from engforge.configuration import Configuration

        slots = self.slots_attributes()

        if check_config:
            chk = lambda k, v: isinstance(v, Configuration)
        else:
            chk = lambda k, v: k in slots and (none_ok or v is not None)

        obj = self.__dict__
        if not use_dict:  # slots
            obj = {k: obj.get(k, None) for k in slots}

        return {k: v for k, v in obj.items() if chk(k, v) and not k.startswith("_")}

    def copy_config_at_state(
        self, level=None, levels_deep: int = -1, changed: dict = None, **kw
    ):
        """copy the system at the current state recrusively to a certain level, by default copying everything
        :param levels_deep: how many levels deep to copy, -1 is all
        :param level: the current level, defaults to 0 if not set
        """
        from engforge.configuration import Configuration
        from engforge.components import SolveableInterface

        if changed is None:
            # top!
            changed = {}

        if self in changed:
            self.debug(f"already changed {self}")
            return changed[self]

        if level is None:
            level = 0
            # at top level add parent to changed to prevent infinte parent recursion
            changed[self] = None

        # exit early if below the level
        if level >= levels_deep and levels_deep > 0:
            self.debug(f"below level {level} {levels_deep} {self}")
            new_sys = attrs.evolve(self)  # copy as is
            changed[self] = new_sys
            return new_sys

        # copy the internal configurations
        kwcomps = {}
        for key, config in self.internal_configurations().items():
            self.debug(f"copying {key} {config} {level} {changed}")
            # copy the system
            if config in changed:
                ccomp = changed[config]
            else:
                ccomp = config.copy_config_at_state(level + 1, levels_deep, changed)
            kwcomps[key] = ccomp

        # Finally make the new system with changed internals
        self.debug(f"changing with changes {self} {kwcomps} {kw}")
        new_sys = attrs.evolve(self, **kwcomps, **kw)
        changed[self] = new_sys

        # Finally change references!
        if isinstance(new_sys, SolveableInterface):
            new_sys.system_references(recache=True)

        # update the parents
        # TODO: use pyee to broadcast change
        if hasattr(self, "parent"):
            if self.parent in changed:
                new_sys.parent = changed[self.parent]

        return new_sys

    def go_through_configurations(
        self,
        level=0,
        levels_to_descend=-1,
        parent_level=0,
        only_inst=True,
        **kw,
    ):
        """A generator that will go through all internal configurations up to a certain level
        if levels_to_descend is less than 0 ie(-1) it will go down, if it 0, None, or False it will
        only go through this configuration

        :return: level,config"""
        from engforge.configuration import Configuration

        # TODO: instead of a recursive loop a global map per problem context should be used, with a static map of slots, updating with every change per note in system_references. This function could be a part of that but each system shouldn't be responsible for it.

        should_yield_level = lambda level: all(
            [
                level >= parent_level,
                any([levels_to_descend < 0, level <= levels_to_descend]),
            ]
        )

        if should_yield_level(level):
            yield "", level, self

        level += 1
        if "check_config" not in kw:
            kw["check_config"] = False

        for key, config in self.internal_configurations(**kw).items():
            if isinstance(config, Configuration):
                for skey, level, iconf in config.go_through_configurations(
                    level, levels_to_descend, parent_level
                ):
                    if not only_inst or iconf is not None:
                        yield f"{key}.{skey}" if skey else key, level, iconf
            else:
                if not only_inst or config is not None:
                    yield key, level, config

    # Our Special Init Methodology
    def __on_init__(self):
        """Override this when creating your special init functionality, you must use attrs for input variables, this is called after parents are assigned. subclasses are always called after"""
        pass

    def __pre_init__(self):
        """Override this when creating your special init functionality, you must use attrs for input variables, this is called before parents are assigned"""
        pass

    def __attrs_post_init__(self):
        """This is called after __init__ by attr's functionality, we expose __oninit__ for you to use!"""
        # Store abs path On Creation, in case we change

        from engforge.components import Component

        self._log = None
        self._anything_changed = True  # save by default first go!
        self._created_datetime = datetime.datetime.utcnow()

        # subclass instance instance init causes conflicts in structures ect
        self.__pre_init__()
        if self._subclass_init:
            try:
                for comp in self.__class__.mro():
                    if (
                        hasattr(comp, "__pre_init__")
                        and comp.__pre_init__ != Configuration.__pre_init__
                    ):
                        comp.__pre_init__(self)
            except Exception as e:
                self.error(e, f"error in __pre_init__ {e}")

        # Assign Parents, ensure single componsition
        # TODO: allow multi-parent, w/wo keeping state, state swap on update()?
        # TODO: replace parent concept with problem context
        for compnm, comp in self.internal_configurations(False).items():
            if isinstance(comp, Component):
                # TODO: allow multiple parents
                if (hasattr(comp, "parent")) and (comp.parent is not None):
                    self.warning(
                        f"Component {compnm} already has a parent {comp.parent} #copying, and assigning to {self}"
                    )
                    # setattr(self, compnm, attrs.evolve(comp, parent=self))
                else:
                    comp.parent = self

        self.debug(f"created {self.identity}")

        # subclass instance instance init causes conflicts in structures
        self.__on_init__()
        runs = set((self.__class__.__on_init__,))  # keep track of unique functions
        if self._subclass_init:
            try:
                for comp in self.__class__.mro():
                    if (
                        hasattr(comp, "__on_init__")
                        and comp.__on_init__ != Configuration.__on_init__
                        and comp.__on_init__ not in runs
                    ):
                        comp.__on_init__(self)
                        runs.add(comp.__on_init__)

            except Exception as e:
                self.error(e, f"error in __on_init__")

    @classmethod
    def validate_class(cls):
        """A customizeable validator at the end of class creation in forge"""
        return

    @classmethod
    def pre_compile(cls):
        """an overrideable classmethod that executes when compiled, however will not execute as a subclass"""
        pass

    @classmethod
    def compile_classes(cls):
        """compiles all subclass functionality"""
        cls.cls_compile()
        for subcls in cls.parent_configurations_cls():
            if subcls.subcls_compile is not Configuration:
                log.debug(f"{cls.__name__} compiling {subcls.__name__}")
            subcls.subcls_compile()

    @classmethod
    def cls_compile(cls):
        """compiles this class, override this to compile functionality for this class"""
        pass

    @classmethod
    def subcls_compile(cls):
        """reliably compiles this method even for subclasses, override this to compile functionality for subclass interfaces & mixins"""
        pass

    @classmethod
    def parent_configurations_cls(cls) -> list:
        """returns all subclasses that are a Configuration"""
        return [c for c in cls.mro() if issubclass(c, Configuration)]

    # Identity & location Methods
    @property
    def filename(self):
        """A nice to have, good to override"""
        fil = (
            self.identity.replace(" ", "_")
            .replace("-", "_")
            .replace(":", "")
            .replace("|", "_")
            .title()
        )
        filename = "".join(
            [c for c in fil if c.isalpha() or c.isdigit() or c == "_" or c == "-"]
        ).rstrip()
        return filename

    @property
    def displayname(self):
        dn = (
            self.identity.replace("_", " ")
            .replace("|", " ")
            .replace("-", " ")
            .replace("  ", " ")
            .title()
        )
        # dispname = "".join([c for c in dn if c.isalpha() or c.isdigit() or c=='_' or c=='-']).rstrip()
        return dn

    @property
    def identity(self):
        """A customizeable property that will be in the log by default"""
        if not self.name or self.name == "default":
            return self.classname.lower()
        if self.classname in self.name:
            return self.name.lower()
        return f"{self.classname}-{self.name}".lower()

    @property
    def classname(self):
        """Shorthand for the classname"""
        return str(type(self).__name__).lower()

    # Structural Orchestration Through Subclassing
    @classmethod
    def subclasses(cls, out=None):
        """return all subclasses of components, including their subclasses
        :param out: out is to pass when the middle of a recursive operation, do not use it!
        """

        # init the set by default
        if out is None:
            out = set()

        for cls in cls.__subclasses__():
            out.add(cls)
            cls.subclasses(out)

        return out
