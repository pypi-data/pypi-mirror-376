#===============================================================================
# PSCAD Project
#===============================================================================
# pylint: disable=too-many-lines

"""
The PSCAD Project Proxy Object
"""

#===============================================================================
# Imports
#===============================================================================

from __future__ import annotations

import collections.abc
import logging
import os
import re

from typing import (overload, DefaultDict, Dict, List, Optional, Set, Tuple,
                    Union, TYPE_CHECKING)
from warnings import warn
from xml.etree import ElementTree as ET

import mhi.common.path
from mhi.common.cache import cached_property
from mhi.common.collection import LingeringCache

from .remote import Remotable, rmi, rmi_property, deprecated, requires
from .types import Message, Parameters, LookIn
from .types import BUILTIN_COMPONENTS as _BUILTIN_COMPONENTS
from .types import BUILTIN_COMPONENT_ALIAS as _BUILTIN_COMPONENT_ALIAS
from .form import FormCodec

if TYPE_CHECKING:
    from .component import Component
    from .canvas import Canvas
    from .definition import Definition


#===============================================================================
# Logging
#===============================================================================

LOG = logging.getLogger(__name__)


#===============================================================================
# PSCAD Project
#===============================================================================

class Project(Remotable):
    """
    PSCAD Project
    """


    #===========================================================================
    # Project Cache
    #   - Definitions
    #   - Canvases
    #===========================================================================

    _definition_cache: LingeringCache[str, Definition]
    _canvas_cache: LingeringCache[str, Canvas]


    #===========================================================================
    # Cache
    #===========================================================================

    def _post_init(self):

        self._definition_cache = LingeringCache()
        self._canvas_cache = LingeringCache()


    def _forget(self):

        del self._pscad._project_cache[self.name]
        super()._forget()


    #===========================================================================
    # Properties
    #===========================================================================

    @property
    def name(self) -> str:
        """
        The name of the project (read-only)

        .. versionadded:: 2.0
        """

        return self._identity['name']


    @rmi_property
    def filename(self) -> str:
        """
        The project's file name (read-only)

        .. versionadded:: 2.0
        """


    @rmi_property
    def temp_folder(self) -> str:
        """
        The project's compiler-dependent temporary folder (read-only).

        .. versionadded:: 2.1
        """


    @rmi_property
    def dirty(self) -> bool:
        """
        Has the project been modified since it was last saved (read-only)

        .. versionadded:: 2.0
        """


    #===========================================================================
    # Debugging
    #===========================================================================

    def __str__(self):
        return f"Project({self.name!r})"

    def __repr__(self):
        return str(self)


    #===========================================================================
    # Validate Project Name
    #===========================================================================

    @staticmethod
    def validate_name(name) -> None:
        """
        The ``name`` must conform to PSCAD naming convensions:

        * it must start with a letter,
        * remaining characters must be alphanumeric or the underscore ``_``,
        * cannot exceed 30 characters.

        Raises a ``ValueError`` is an invalid name is given.
        """

        if not name  or  not re.fullmatch("[a-zA-Z][a-zA-Z0-9_]{0,29}", name):
            LOG.error("Invalid project name: %r", name)
            raise ValueError("Name must start with a letter, "
                             "may only contain letters, numbers & underscores, "
                             "and may be at most 30 characters long")


    #===========================================================================
    # Save/Save As/Reload/Unload
    #===========================================================================

    #---------------------------------------------------------------------------
    # Save / Save As ...
    #---------------------------------------------------------------------------

    @rmi
    def _save(self, filename=None, ver46=False):
        pass

    def save(self) -> None:
        """
        Save changes made to this project
        """

        LOG.info("%s: Save ", self)

        return self._save()


    def save_as(self, filename: str, ver46: bool = False,
                folder: Optional[str] = None) -> Project:
        """
        Save this project under a new name.

        The project will be saved using the appropriate extension depending
        on whether the project is a case (``.pscx``) or library (``.pslx``).

        The filename must conform to PSCAD naming convensions:

        * it must start with a letter,
        * remaining characters must be alphanumeric or the underscore ``_``,
        * cannot exceed 30 characters.

        Parameters:
            filename (str): The name or filename to store project to.
            ver46 (bool): Set to true to store as a version 4.6 file. (optional)
            folder (str): If provided, the path to the filename is resolved
                relative to this folder. (optional)

        Notes:
            When the project name is changed, all existing Python handles to
            the project and anything within it become invalid and must not be
            used.

        .. versionchanged:: 2.0
            Added ``ver46`` parameter.
        .. versionchanged:: 2.7.2
            Added ``folder`` parameter; returns the new project object.
        """

        ver502 = self._pscad.minimum_version("5.0.2")

        if ver502 or folder or not filename.isidentifier():
            filename = mhi.common.path.expand_path(filename, abspath=True,
                                                   folder=folder)
        dest_folder, basename = os.path.split(filename)
        name, _ = os.path.splitext(basename)

        if ver502:
            while "." in name[1:]:
                name, _ = os.path.splitext(name)

        self.validate_name(name)

        if not ver502:
            if dest_folder and os.path.dirname(self.filename) != dest_folder:
                msg = "Project.save_as with a path requires PSCAD 5.0.2+"
                raise NotImplementedError(msg)
            filename = name

        LOG.info("%s: Save as '%s'", self, filename)
        self._save(filename, ver46)

        self._forget()

        return self._pscad.project(name)


    #---------------------------------------------------------------------------
    # Consolidate
    #---------------------------------------------------------------------------

    @rmi
    def _consolidate(self, folder):
        pass

    def consolidate(self, folder: str) -> None:
        """
        Moves all files need for this project to the folder, renaming paths
        as needed.

        .. versionadded:: 2.0
        """
        if os.path.exists(folder) and not os.path.isdir(folder):
            raise FileExistsError("Not a folder")

        try:
            os.makedirs(folder)
        except OSError as err:
            raise ValueError("Unable to create folder") from err

        return self._consolidate(folder)


    #---------------------------------------------------------------------------
    # Reload
    #---------------------------------------------------------------------------

    def reload(self) -> None:
        """
        Reload this project.

        The project is unloaded, without saving any unsaved modifications,
        and then immediately reloaded.
        This returns the project to the state it was in when it was last
        saved.

        .. versionadded:: 2.0
        """

        # But first, forget everything I knew ...
        self._clear_cache()

        self._rmi('reload')


    #---------------------------------------------------------------------------
    # Unload
    #---------------------------------------------------------------------------

    def unload(self) -> None:
        """
        Unload this project.

        The project is unloaded.
        All unsaved changes are lost.

        .. versionadded:: 2.0
        """

        # Forget I even existed
        self._forget()

        self._rmi('unload')


    #---------------------------------------------------------------------------
    # Is Dirty
    #---------------------------------------------------------------------------

    def is_dirty(self) -> bool:
        """
        Check if the project contains unsaved changes

        Returns:
            `True`, if unsaved changes exist, `False` otherwise.
        """

        return self.dirty



    #===========================================================================
    # Parameters
    #===========================================================================

    @rmi
    def _parameters(self, scope, parameters):
        pass


    @cached_property
    def _parameters_codec(self) -> FormCodec:
        return FormCodec.project(self)


    _PARAM_FLAGS = {
        'Advanced': {
            0: 'detect_chatter',
            1: 'remove_chatter',
            2: 'interpolate_switching',
            4: 'optimize_nodes',
            5: 'remove_time_offset',
            7: 'use_ideal_branch',
            8: 'network_splitting',
            9: 'move_switching',
            10: 'send_output_ch',
            11: 'start_sim_debug',
            13: 'sparse_algorithm',
            14: 'live_output',
            },
        'Build': {
            0: 'runtime_debugging',
            1: 'feed_forward',
            2: 'signal_flow',
            3: 'bus_matching',
            },
        'Check': {
            0: 'array_bounds',
            1: 'floating_underflow',
            2: 'integer_overflow',
            },
        'Debug': {
            0: 'echo_network',
            1: 'echo_runtime',
            2: 'echo_input',
            },
        'Options': {
            3: 'link_matlab',
            4: 'enable_animation',
            5: 'preprocessor_enable',
            },
        'Warn': {
            0: 'argument_mismatch',
            1: 'uncalled_routines',
            2: 'uninitialized_variable',
            },
         }
    _PARAM_ENCODE_FLAGS = {flag: (field, bit)
                           for field, flags in _PARAM_FLAGS.items()
                           for bit, flag in flags.items()}


    @classmethod
    def _param_flag_decode(cls, parameters) -> None:
        for field, flags in cls._PARAM_FLAGS.items():
            if field in parameters:
                bits = parameters.pop(field)
                for bit, flag in flags.items():
                    parameters[flag] = bool((1 << bit) & bits)


    @classmethod
    def _param_flag_encode(cls, parameters) -> Dict[str,List[int]]:
        set_clr: Dict[str,List[int]] = DefaultDict(lambda: [0, 0])
        for flag, (field, bit) in cls._PARAM_ENCODE_FLAGS.items():
            if flag in parameters:
                if field in parameters:
                    raise ValueError(f"Cannot specify '{flag}' and "
                                     f"'{field}' simultaneously.")
                value = parameters.pop(flag, None)
                if value:
                    set_clr[field][0] |= 1 << bit
                else:
                    set_clr[field][1] |= 1 << bit

        return set_clr


    @overload
    def parameters(self) -> Parameters: ...

    @overload
    def parameters(self, parameters: Optional[Parameters] = None,
                   **kwargs) -> None: ...

    def parameters(self, parameters: Optional[Parameters] = None,
                   **kwargs) -> Optional[Parameters]:

        """
        Get or set project parameters

        Parameters:
            parameters (dict): A dictionary of name=value parameters
            **kwargs: Zero or more name=value keyword parameters

        Returns:
            A dictionary of current parameters, if no parameters were given.


        .. table:: Project Parameters

            ================= ====== ===========================================
            Param Name        Type   Description
            ================= ====== ===========================================
            description       str    Description
            time_step         float  Solution time step
            time_duration     float  Duration of run
            sample_step       float  Channel plot step
            PlotType          choice Save to: `"NONE"`, `"OUT"`, `"PSOUT"`
            output_filename   str    Name of data file, with .out extension
            StartType         int    Start simulation: 0=Standard,\
                                     1=From Snapshot File
            startup_filename  str    Start up snapshot file name
            SnapType          int    Timed Snapshot: 0=None, 1=Single,\
                                     2=Incremental (same file),\
                                     3=Incremental (multiple file)
            SnapTime          float  Snapshot time as a real number
            snapshot_filename str    Save snapshot as text
            MrunType          int    Run config 0=Standalone, 1=Master, 2=Slave
            Mruns             int    Number of multiple runs
            ================= ====== ===========================================
        """

        def unsettable(kind, *keys):
            params = ", ".join(key for key in keys
                               if parameters.pop(key, None) is not None)
            if params:
                warn("Unable to set " + kind + " parameter(s): " + params,
                     stacklevel=3)

        codec = self._parameters_codec

        # Combined **kwargs in parameters dictionary
        parameters = dict(parameters, **kwargs) if parameters else kwargs

        unsettable("save-only", 'creator', 'revisor')
        unsettable("obsolete", 'architecture', 'latency_count',
                   'multirun_filename', 'Source',)
        if 'Scenario' in parameters:
            scenario = parameters.pop('Scenario', None)
            warn(("Cannot set parameter 'Scenario'; "
                  f"use project.scenario({scenario or ''!r})"),
                 stacklevel=2)

        if parameters:
            set_clr = self._param_flag_encode(parameters)
            if set_clr:
                curr = self._parameters('Settings', {})
                for field, (set_mask, clr_mask) in set_clr.items():
                    parameters[field] = int(curr[field]) & ~clr_mask | set_mask

        parameters = codec.encode(parameters)
        parameters = self._parameters('Settings', parameters)
        parameters = codec.decode(parameters)
        if parameters:
            self._param_flag_decode(parameters)

        return parameters


    @deprecated("Use Project.parameters(...)")
    def set_parameters(self, parameters=None, **kwargs): # pylint: disable=missing-function-docstring
        self.parameters(parameters, **kwargs)


    def parameter_range(self, parameter: str):
        """
        Get legal values for a parameter

        Example::

            >>> vdiv.parameter_range('SnapType')
            frozenset({'ONLY_ONCE', 'NONE', 'INCREMENTAL_SAME_FILE', 'INCREMENTAL_MANY_FILES'})

        .. versionadded:: 2.0
        """

        codec = self._parameters_codec

        try:
            return codec.range(parameter)
        except KeyError:
            raise ValueError("No such parameter") from None
        except AttributeError:
            raise ValueError("No defined range for parameter") from None


    #===========================================================================
    # Focus
    #===========================================================================

    @rmi
    def focus(self) -> None:
        """
        Switch PSCAD's focus to this project.
        """


    #===========================================================================
    # Navigate
    #===========================================================================

    @rmi
    def _navigate_to(self, *components):
        pass


    def navigate_to(self, *components: Component):
        """
        Navigate to a particular instance of component in a call stack
        """

        return self._navigate_to(*components)


    #===========================================================================
    # Bookmarks
    #===========================================================================

    @rmi
    def _bookmark(self, name, mouse_x, mouse_y, callstack):
        pass


    def bookmark(self, name: str, mouse_x: int, mouse_y: int,
                 *callstack: Component) -> int:
        """
        Create a bookmark to a particular location of particular instance of
        a component in a call stack.
        """

        return self._bookmark(name, mouse_x, mouse_y, callstack)


    #===========================================================================
    # Search
    #===========================================================================

    @rmi
    def _branch_search(self, subsys, node_id):
        pass


    @requires('5.1')
    def branch_search(self, subsystem_id: int = 0, node_id: int = 0):
        """
        Perform a 'Branch Search' in this project

        Project must be compiled for the search to return useful results.

        .. versionadded:: 2.9.6
        """

        self._branch_search(subsystem_id, node_id)

        return self._pscad.search_results()


    @rmi
    def _node_search(self, subsys, node_id, look_in, global_flag):
        pass


    @requires('5.1')
    def node_search(self, subsystem_id: int, node_id: int,
                    look_in: LookIn, global_flag: bool):
        """
        Perform a 'Node Search' with this project

        Project must be compiled for the search to return useful results.

        .. versionadded:: 2.9.6
        """

        if look_in not in {LookIn.MODULE, LookIn.PROJECT}:
            raise ValueError("Expected LookIn MODULE or PROJECT")

        self.focus()
        self._node_search(subsystem_id, node_id, look_in.value, global_flag)

        return self._pscad.search_results()


    #===========================================================================
    # Build / Run / Pause / Stop
    #===========================================================================

    #---------------------------------------------------------------------------
    # Build
    #---------------------------------------------------------------------------

    @rmi
    def _build(self, clean):
        pass

    def build(self) -> None:
        """
        Clean & Build this project, and any dependencies
        """

        LOG.info("%s: Clean & Build", self)

        return self._build(True)


    def build_modified(self) -> None:
        """
        Build this project, and any dependencies
        """

        LOG.info("%s: Build (if modified)", self)

        return self._build(False)


    @requires('5.0.2')
    @rmi
    def compile_library(self):
        """
        Compile all resources linked in this library into a single compiled
        ``*.lib`` file.

        .. versionadded:: 2.8
        """


    #---------------------------------------------------------------------------
    # Run
    #---------------------------------------------------------------------------

    @rmi
    def _run(self):
        pass


    def run(self, consumer=None) -> None:
        """
        Build and run this project.

        Parameters:
            consumer: handler for events generated by the build/run (optional).

        Note:
            A library cannot be run; only a case can be run.
        """

        with self._pscad.subscription('build-events', consumer):
            self._run()


    #---------------------------------------------------------------------------
    # Run Status
    #---------------------------------------------------------------------------

    @rmi
    def run_status(self) -> Tuple[Optional[str], Optional[int]]:
        """
        Get the run status of the project

        Returns:
            Returns `("Build", None)` if building, `("Run", percent)` if running,
            or `(None, None)` otherwise.

        .. versionchanged:: 2.0
            Was ``ProjectCommands.get_run_status()``
        """


    @deprecated
    def get_run_status(self):       # pylint: disable=missing-function-docstring
        return self.run_status()


    #---------------------------------------------------------------------------
    # Start
    #---------------------------------------------------------------------------

    def start(self) -> None:
        """
        Start the current project running.

        Note:
            Returns immediately.
        """

        self.focus()
        return self._pscad.start_run()


    #---------------------------------------------------------------------------
    # Pause
    #---------------------------------------------------------------------------

    def pause(self) -> None:
        """
        Pause the currently running projects.

        Note:
            All projects being run will be paused, not just this project.
        """

        return self._pscad.pause_run()


    #---------------------------------------------------------------------------
    # Stop
    #---------------------------------------------------------------------------

    @rmi
    def stop(self) -> None:
        """
        Terminate a running execution of this project.
        """


    #===========================================================================
    # Build & Run Messages
    #===========================================================================

    #---------------------------------------------------------------------------
    # Load / Build messages
    #---------------------------------------------------------------------------

    @rmi
    def _messages(self):
        pass

    def messages(self) -> List[Message]:
        """
        Retrieve the load/build messages

        Returns:
            List[Message]: A list of messages associated with the project.

        Each message is a named tuple composed of:

        ====== ====================================================
        text   The message text
        label  Kind of message, such as build or load
        status Type of messages, such as normal, warning, or error.
        scope  Project to which the message applies
        name   Component which caused the message
        link   Id of the component which caused the message
        group  Group id of the message
        ====== ====================================================

        Example::

            pscad.load('tutorial/vdiv.pscx', folder=pscad.examples_folder)
            vdiv = pscad.project('vdiv')
            vdiv.build()
            for msg in vdiv.messages():
                print(msg.text)
        """

        return [Message._make(msg) for msg in self._messages()]

    @deprecated
    def list_messages(self):        # pylint: disable=missing-function-docstring
        raise NotImplementedError("Use Project.messages()")


    #---------------------------------------------------------------------------
    # Run messages
    #---------------------------------------------------------------------------

    @rmi
    def output(self) -> str:
        """
        Retrieve the output (run messages) for the project

        Returns:
            str: The output messages

        Example::

            pscad.load('tutorial/vdiv.pscx', folder=pscad.examples_folder)
            vdiv = pscad.project('vdiv')
            vdiv.run()
            print(vdiv.output())

        .. versionchanged:: 2.0
            Was ``ProjectCommands.get_output_text()``
        """


    @deprecated("Use Project.output()")
    def get_output_text(self):      # pylint: disable=missing-function-docstring
        return self.output()


    @deprecated
    def get_output(self):           # pylint: disable=missing-function-docstring
        raise NotImplementedError("Use Project.output()")


    #===========================================================================
    # Clean
    #===========================================================================

    @rmi
    def clean(self) -> None:

        """
        Clean the project
        """

        # Probably not necessary, but possible not a terrible idea.
        self._clear_cache()


    #===========================================================================
    # Definitions
    #===========================================================================

    @rmi
    def definitions(self) -> List[str]:

        """
        Retrieve a list of all definitions contained in the project.

        Returns:
            List[str]: A list of all of the :class:`.Definition` names.

        .. versionchanged:: 2.0
            Was ``ProjectCommands.list_definitions()``
        """


    @deprecated("Use Project.definitions()")
    def list_definitions(self):     # pylint: disable=missing-function-docstring
        return self.definitions()


    @rmi
    def _definition(self, *args, **kwargs):
        pass


    def definition(self, name: str) -> Definition:
        """
        Retrieve the given named definition from the project.

        Parameters:
            name (str): The name of the definition.

        Returns:
            The named :class:`.Definition`.

        .. versionchanged:: 2.0
            Was ``ProjectCommands.get_definition()``
        """

        defn = self._definition_cache.get(name)
        if defn is None:
            defn = self._definition(name)
            self._definition_cache[name] = defn

        return defn


    @deprecated("Use Project.definition(name)")
    def get_definition(self, name): # pylint: disable=missing-function-docstring
        return self.definition(name)


    def create_definition(self, xml: Union[str, ET.Element]) -> Definition:
        """
        Add a new definition to the project

        Parameters:
            xml (Union[str, ET.Element]): The definition XML

        Returns:
            The newly created :class:`.Definition`
        """

        if isinstance(xml, ET.ElementTree):
            xml = xml.getroot()

        if isinstance(xml, ET.Element):
            xml = ET.tostring(xml, 'unicode')

        defn = self._definition(create=xml)

        self._definition_cache[defn.name] = defn

        return defn


    def delete_definition(self, name: str) -> None:
        """
        Delete the given named :class:`.Definition`.

        Parameters:
            name (str): The name of the definition to delete.
        """

        # Forget the definition in the caches (if present)
        del self._definition_cache[name]
        del self._canvas_cache[name]

        return self._definition(name, action='delete')


    def delete_definition_instances(self, name: str) -> None:
        """
        Delete the given named :class:`.Definition`, along with all instances
        of the that definition.

        Parameters:
            name (str): The name of the :class:`.Definition` whose definition\
                and instances are to be deleted.
        """

        # Forget the definition in the caches (if present)
        del self._definition_cache[name]
        del self._canvas_cache[name]

        return self._definition(name, action='delete-instances')


    @rmi
    def _paste_defns(self, with_dependents: bool):
        pass


    @requires('5.0.3')
    def paste_definitions(self) -> None:
        """
        Paste definitions from the clipboard into this project.

        .. versionadded:: 2.9
        """

        # Cache is possibly very out-of-date, start from scratch
        self._definition_cache.clear()

        self._paste_defns(False)


    @requires('5.0.3')
    def paste_definitions_with_dependents(self) -> None:
        """
        Paste definitions and their dependents from the clipboard
        into this project.

        .. versionadded:: 2.9
        """

        # Cache is possibly very out-of-date, start from scratch
        self._definition_cache.clear()

        self._paste_defns(True)


    @requires('5.1')
    def remap_definitions(self, old: 'Project', new: 'Project',
                          *definitions: str) -> None:
        """
        Remap definitions from one namespace to another namespace.

        .. versionadded:: 3.0.2
        """

        old_defns = set(old.definitions())
        new_defns = set(new.definitions())
        common = old_defns & new_defns

        if not common:
            raise ValueError("Namespaces have no definitions in common")

        replace = set(definitions)
        if replace and not replace <= common:
            missing = ", ".join(map(repr, replace - common))
            raise ValueError(f"Not common to both namespaces: {missing}")

        if replace:
            for definition in replace:
                self._rmi("_remap", old.name, new.name, definition)
        else:
            self._rmi("_remap", old.name, new.name)


    #===========================================================================
    # Layers
    #===========================================================================

    @rmi
    def layers(self) -> Dict[str, str]:
        """
        Fetch the state of all of the layers

        .. versionadded:: 2.0
        """

    #---------------------------------------------------------------------------

    @rmi
    def _create_layer(self, name):
        pass

    def create_layer(self, name: str, state: str = "Enabled") -> Layer:
        """
        Create a new layer

        Parameters:
            name (str): Name of the layer to create.
            state (str): Initial state of layer (optional, default='Enabled')
        """

        LOG.info("%s: create layer '%s'", self, name)
        layer = self._create_layer(name)
        layer.state = state
        return layer


    #---------------------------------------------------------------------------

    # states (invisible, disabled, enabled, ...)
    @deprecated("Use project.set_layer_state(name, state)")
    def set_layer(self, name, state):
        """
        Set the state of a layer

        Parameters:
            name (str): Name of the layer to alter.
            state (str): "Enabled", "Disabled", "Invisible" or a custom state.
        """

        self.set_layer_state(name, state)


    def set_layer_state(self, name: str, state: str) -> None:
        """
        Set the state of a layer

        Parameters:
            name (str): Name of the layer to alter.
            state (str): "Enabled", "Disabled", "Invisible" or a custom state.

        .. versionchanged:: 2.0
            Renamed from ``.set_layer(state)``
        """

        self.layer(name).state = state


    @rmi
    def layer_states(self, name: str) -> List[str]:
        """
        Fetch all valid states for the given layer

        .. versionadded:: 2.0
        """

    #---------------------------------------------------------------------------

    @rmi
    def _remove_layers(self, names):
        pass


    def delete_layer(self, name: str) -> None:
        """
        Delete an existing layer

        Parameters:
            name (str): Name of the layer to delete.
        """

        LOG.info("%s: delete layer '%s'", self, name)

        return self._remove_layers([name])


    def delete_layers(self, *names: str) -> None:
        """
        Delete existing layers

        Parameters:
            *names (str): Name of the layer to delete.
        """

        return self._remove_layers(names)


    #---------------------------------------------------------------------------

    @rmi
    def layer(self, name: str) -> Layer:
        """
        Fetch the given layer

        .. versionadded:: 2.0
       """


    #---------------------------------------------------------------------------

    @rmi
    def _move_layers(self, delta, names):
        pass


    def move_layers_up(self, *names: str, delta: int = 1):
        """
        Move the list of layers up the list by 1
        """
        return self._move_layers(-delta, names)


    def move_layers_down(self, *names: str, delta: int = 1):
        """
        Move the list of layers down the list by 1
        """
        return self._move_layers(delta, names)


    #---------------------------------------------------------------------------

    @rmi
    def _merge_layers(self, new_name, names):
        pass


    def merge_layers(self, dest: str, *names: str):
        """
        Merge the list of layers into a layer with the name provided.

        Parameters:
            dest (str): The name of the layer to merge to, created if necessary
            *names (str): Layers to merge into the destination layer

        Returns:
            Layer: The destination layer
        """

        if len(names) < 1:
            raise ValueError("Expected 1 or more layers to merge")

        return self._merge_layers(dest, names)


    #===========================================================================
    # Scenarios
    #===========================================================================

    @rmi
    def scenarios(self) -> List[str]:
        """
        List the scenarios which exist in the project.

        Returns:
            List[str]: List of scenario names.

        .. versionchanged:: 2.0
            Was ``ProjectCommands.list_scenarios()``
        """


    @deprecated("Use Project.scenarios")
    def list_scenarios(self):       # pylint: disable=missing-function-docstring
        return self.scenarios()


    @rmi
    def scenario(self, name: Optional[str] = None) -> str:
        """
        Get or set the current scenario.

        Parameters:
            name (str): Name of scenario to switch to (optional).

        Returns:
            str: The name of the (now) current scenario.
        """


    @rmi
    def _delete_scenario(self, name):
        pass


    def delete_scenario(self, name: str) -> None:
        """
        Delete the named scenario.

        Parameters:
            name (str): Name of scenario to delete.
        """

        LOG.info("%s: Delete scenario '%s'", self, name)
        return self._delete_scenario(name)


    @rmi
    def _save_scenario(self, *args):
        pass


    def save_scenario(self) -> None:
        """
        Save the current scenario.

        .. versionadded:: 2.0
        """

        LOG.info("%s: Saved current scenario", self)

        return self._save_scenario()


    def save_as_scenario(self, name: str) -> None:
        """
        Save the current configuration under the given scenario name.

        Parameters:
            name (str): Name of scenario to create or overwrite.
        """

        LOG.info("%s: Save scenario as '%s'", self, name)

        return self._save_scenario(name)


    #===========================================================================
    # Canvas
    #===========================================================================

    @rmi
    def _schematic(self, name=None):
        pass


    def canvas(self, name: str) -> Canvas:
        """
        Retrieve the drawing canvas of a component definition.

        Only T-Lines, Cables, and module-type user components have a canvas.

        Parameters:
            name (str): Definition name of the component.

        Returns:
            The corresponding canvas proxy object.

        Getting the main page of a project::

            main = project.canvas('Main')

        .. versionchanged:: 2.0
            Was ``Project.user_canvas(name)``
        """

        canvas = self._canvas_cache.get(name)
        if canvas is None:
            canvas = self._schematic(name)
            self._canvas_cache[name] = canvas

        return canvas


    @deprecated("Use Project.canvas(name)")
    def user_canvas(self, name):    # pylint: disable=missing-function-docstring
        return self.canvas(name)


    @requires("5.0.1")
    def current_canvas(self) -> Canvas:
        """
        Retrieve the currently focuses canvas of the project.

        Returns:
            The currently focused canvas.

        .. versionadded:: 2.3.2
        """

        return self._schematic()


    #===========================================================================
    # Components
    #===========================================================================

    @rmi
    def component(self, iid: int) -> Component:
        """
        Retrieve a component by ID.

        Parameters:
            iid (int): The ID attribute of the component.

        .. versionadded:: 2.0
            This command replaces all of the type specific versions.
        """


    @deprecated("Use Project.component(id)")
    def _component_by_id(self, defn, iid):     # pylint: disable=unused-argument
        return self.component(iid)


    @deprecated("Use Project.component(id)")
    def _component_by_ids(self, defn, *iid):   # pylint: disable=unused-argument
        return self.component(iid[-1])

    # Obsolete functions which no longer require the canvas name,
    # and only require the last component id number.
    user_cmp = _component_by_id
    slider = _component_by_ids
    switch = _component_by_ids
    button = _component_by_ids
    selector = _component_by_ids
    overlay_graph = _component_by_ids
    graph_frame = _component_by_id


    #---------------------------------------------------------------------------
    # Find all
    #---------------------------------------------------------------------------

    def _find(self, *names, **params):

        if len(names) > 2 and params:
            namespace, defn_name, *_ = names

            if namespace and defn_name:
                try:
                    prj = self._pscad.project(namespace)
                    defn = prj.definition(defn_name)
                    codec = defn.form_codec
                    params = codec.encode(params)
                except ValueError:
                    pass

        return self._rmi('_find', *names, **params)


    def find_all(self, *name: str, layer: Optional[str] = None,
                 **params) -> List[Component]:
        """
        find_all( [[definition,] name,] [layer=name,] [key=value, ...])

        Find all components that match the given criteria.

        Parameters:
            definition (str): One of "Bus", "TLine", "Cable", "GraphFrame",
                "Sticky", or a colon-seperated definition name, such as
                "master:source3" (optional)
            name (str): the component's name, as given by a parameter
                called "name", "Name", or "NAME".
                If no definition was given, and if the provided name is
                "Bus", "TLine", "Cable", "GraphFrame", "Sticky", or
                contains a colon, it is treated as the definition name.
                (optional)
            layer (str): only return components on the given layer (optional)
            key=value: A keyword list specifying additional parameters
               which must be matched.  Parameter names and values must match
               exactly. For example, Voltage="230 [kV]" will not match
               components with a Voltage parameter value of "230.0 [kV]".
               (optional)

        Returns:
            List[ZComponent]: The list of matching components,
            or an empty list if no matching components are found.

        Examples::

           c = find_all('Bus'                # all Bus components
           c = find_all('Bus10')             # all components named "Bus10"
           c = find_all('Bus', 'Bus10')      # all Bus component named "Bus10"
           c = find_all('Bus', BaseKV='138') # all Buses with BaseKV="138"
           c = find_all(BaseKV='138')        # all components with BaseKV="138"

        .. versionadded:: 2.0
        """

        if len(name) == 0 and layer is None and len(params) == 0:
            raise ValueError("No search criteria given")

        if len(name) > 2:
            raise ValueError("Too many names")

        namespace = None
        defn = name[0] if len(name) > 0 else None
        named = name[1] if len(name) > 1 else None

        if defn:
            if defn in _BUILTIN_COMPONENTS:
                pass
            elif defn in _BUILTIN_COMPONENT_ALIAS:
                defn = _BUILTIN_COMPONENT_ALIAS[defn]
            elif ':' in defn:
                namespace, defn = defn.split(':', 1)
            elif not named:
                named = defn
                defn = None

        return self._find(namespace, defn, named, layer, **params)


    #---------------------------------------------------------------------------
    # Find first
    #---------------------------------------------------------------------------

    def find_first(self, *names: str, layer: Optional[str] = None,
                   **params) -> Optional[Component]:
        """
        find_first( [[definition,] name,] [layer=name,] [key=value, ...])

        Find the first component that matches the given criteria,
        or ``None`` if no matching component can be found.

        .. versionadded:: 2.0
        """

        components = self.find_all(*names, layer=layer, **params)
        return components[0] if components else None


    #---------------------------------------------------------------------------
    # Find (singular)
    #---------------------------------------------------------------------------

    def find(self, *names: str, layer: Optional[str] = None,
             **params) -> Optional[Component]:
        """
        find( [[definition,] name,] [layer=name,] [key=value, ...])

        Find the (singular) component that matches the given criteria,
        or ``None`` if no matching component can be found.
        Raises an exception if more than one component matches
        the given criteria.

        .. versionadded:: 2.0
        """

        components = self.find_all(*names, layer=layer, **params)
        if len(components) > 1:
            raise ValueError("Multiple components found")

        return components[0] if components else None


    #===========================================================================
    # Names in Use
    #===========================================================================

    @rmi(fallback=True)
    def _param_values(self, param_name, namespace, defn, named, **params):

        values = set()
        for defn_name in self.definitions():
            prj_defn = self.definition(defn_name)
            if prj_defn.is_module():
                canvas = prj_defn.canvas()
                canvas_values = canvas._param_values(param_name,
                                                     namespace, defn, named,
                                                     **params)
                values.update(canvas_values)

        return values


    def names_in_use(self, defn: Optional[str] = None, **params) -> Set[str]:
        """
        Return the set of "Name" parameter values, for all components on the
        canvas that have a "Name" parameter.
        """

        namespace = None
        if defn:
            if defn in _BUILTIN_COMPONENTS:
                pass
            elif defn in _BUILTIN_COMPONENT_ALIAS:
                defn = _BUILTIN_COMPONENT_ALIAS[defn]
            else:
                namespace, defn = defn.split(':', 1)

        return self._param_values('Name', namespace, defn, None, **params)


    #===========================================================================
    # Parameter Grid
    #===========================================================================

    @rmi
    def _export_param_grid(self, filename):
        pass


    @rmi
    def _import_param_grid(self, filename):
        pass


    def export_parameter_grid(self, filename: str,
                              folder: Optional[str] = None) -> None:
        """
        Export parameters to a CSV file.

        Parameters:
            filename (str): Filename of the CSV file to write.
            folder (str): Directory where the CSV file will be stored (optional)
        """

        filename = mhi.common.path.expand_path(filename, abspath=True,
                                                     folder=folder)

        LOG.info("%s: Export parameter grid to '%s'", self, filename)

        return self._export_param_grid(filename)


    def import_parameter_grid(self, filename: str,
                              folder: Optional[str] = None) -> None:
        """
        Import parameters from a CSV file.

        Parameters:
            filename (str): Filename of the CSV file to read.
            folder (str): Directory to read the CSV file from (optional)
        """

        filename = mhi.common.path.expand_path(filename, abspath=True,
                                                     folder=folder)

        LOG.info("%s: Import parameter grid from '%s'", self, filename)

        return self._import_param_grid(filename)


    #===========================================================================
    # Resources
    #===========================================================================

    @rmi
    def _create_resource(self, path):
        pass


    def create_resource(self, path: str) -> Resource:
        """
        Add a new resource to the Project's resource folder

        Parameter:
            path (str): Pathname of the resource
        """
        return self._create_resource(path)


    @rmi
    def resources(self) -> List[Resource]:
        """
        Fetch list of all resources in project
        """


    @rmi
    def resource(self, path: str) -> Resource:
        """
        Find a resource by path
        """


    @rmi
    def remove_resource(self, resource: Resource):
        """
        Remove a resource
        """


    #===========================================================================
    # Global Substitutions
    #===========================================================================

    @rmi
    def _gs_list_sets(self):
        pass

    @rmi
    def _gs_create_set(self, *set_names):
        pass

    @rmi
    def _gs_remove_set(self, *set_names):
        pass

    @rmi
    def _gs_rename_set(self, old_set_name, new_set_name):
        pass

    @rmi
    def _gs_list(self):
        pass

    @rmi
    def _gs_create(self, *var_names):
        pass

    @rmi
    def _gs_remove(self, *var_names):
        pass

    @rmi
    def _gs_rename(self, old_var_name, new_var_name):
        pass

    @rmi
    def _gs_get(self, set_name, var_name):
        pass

    @rmi
    def _gs_set(self, set_name, var_name, value):
        pass

    @rmi
    def _gs_save(self, filename, all_sets):
        pass

    @rmi
    def _gs_load(self, filename, all_sets, clear):
        pass


    _gs_active = rmi_property(True, True, name='_gs_active')


    @cached_property
    def global_substitution(self):
        """
        The global substitution container for the project.
        Can be referenced as a dictionary of dictionaries.
        ``Dict[SetName, Dict[VariableName, Value]]``

        Examples::

            prj.global_substitution.create_sets('Set1', 'Set2')
            prj.global_substitution.create('freq', 'VBase')
            prj.global_substitution['']['freq'] = "60.0 [Hz]"      # Default set
            prj.global_substitution['Set1']['freq'] = "50.0 [Hz]"
            prj.global_substitution['Set2'] = { 'freq': "60.0 [Hz]", 'VBase': '13.8 [kV]' }
            prj.global_substitution.active_set = "Set1"

            # List all global substitution sets
            >>> list(prj.global_substitution))
            ['', 'S1', 'S2']

            # Print active global substitutions:
            >>> gs = prj.global_substitution
            >>> for name, value in gs[gs.active_set].items():
                    print(name, "=", value)


            freq = 50.0 [Hz]
            VBase =
        """

        if '_gs' not in self.__dict__:
            self._gs = GlobalSubstitution(self) # pylint: disable=attribute-defined-outside-init
        return self._gs


#===============================================================================
# Global Substitutions
#===============================================================================

class GlobalSubstitution:

    """
    Management for a project's global substitutions and sets of global
    substitutions.

    Returned by :attr:`.Project.global_substitution`
    """

    class Set(collections.abc.Mapping):
        """
        Global Substitute Set
        """

        def __init__(self, project: Project, set_name: str):
            self._prj = project
            self._name = set_name

        def __bool__(self):
            return self._name in self._prj._gs_list_sets()

        def __len__(self):
            return len(self._prj._gs_list())

        def __iter__(self):
            return iter(self._prj._gs_list())

        def __getitem__(self, var_name):
            return self._prj._gs_get(self._name, var_name)

        def __setitem__(self, var_name, value):
            self._prj._gs_set(self._name, var_name, value)

        def __delitem__(self, var_name):
            self._prj._gs_remove(var_name)


    def __init__(self, project: Project):
        self._prj = project


    @property
    def main(self):
        """The PSCAD application object"""
        return self._prj.main

    def __len__(self):
        return len(self._prj._gs_list_sets())

    def __iter__(self):
        return iter(self._prj._gs_list_sets())

    def __getitem__(self, set_name):
        return self.Set(self._prj, set_name)

    def __setitem__(self, set_name, values):
        if not isinstance(values, dict):
            raise TypeError("Expected dictionary")

        if set_name and not bool(self[set_name]):
            self._prj._gs_create_set(set_name)

        create = set(values.keys()) - set(self[set_name])
        if create:
            self._prj._gs_create(*create)

        for var_name, value in values.items():
            self._prj._gs_set(set_name, var_name, value)

    def __delitem__(self, set_name):
        self._prj._gs_remove_set(set_name)


    @property
    def active_set(self) -> str:
        """
        The currently active global substitution set.

        Returns the name of the currently active substitution set,
        or `None` for the default set

        Set to the desired global substitution set name to change
        the active global substitution set.
        Setting this to ``""`` or ``None`` reverts to the default set.
        """
        return self._prj._gs_active

    @active_set.setter
    def active_set(self, set_name: str):
        self._prj._gs_active = set_name


    def create_sets(self, *set_names: str) -> None:
        """
        Creates 1 or more named global substitution sets

        Parameters:
            *set_names (str): One or more names for the new sets
        """

        return self._prj._gs_create_set(*set_names)


    def create(self, *val_names: str) -> None:
        """
        Creates 1 or more named global substitution variables.

        Parameters:
            *val_names (str): One or more new variable names
        """

        return self._prj._gs_create(*val_names)


    def remove_sets(self, *set_names: str) -> None:
        """
        Removes 1 or more named global substitution sets

        Parameters:
            *set_names (str): One or more names of sets to be deleted
        """

        return self._prj._gs_remove_set(*set_names)


    def remove(self, *val_names: str) -> None:
        """
        Removes 1 or more named global substitution variables

        Parameters:
            *val_names (str): One or more names of variables to be deleted
        """

        return self._prj._gs_remove(*val_names)


    def rename_set(self, old_name: str, new_name: str) -> bool:
        """
        Rename a global substitution set

        Parameters:
            old_name (str): Current name of the substitution set
            new_name (str): Desired name of the substitution set
        """
        return self._prj._gs_rename_set(old_name, new_name)


    def rename(self, old_name: str, new_name: str) -> bool:
        """
        Rename a global substitution variable

        Parameters:
            old_name (str): Current name of the substitution variable
            new_name (str): Desired name of the substitution variable
        """
        return self._prj._gs_rename(old_name, new_name)


    @requires('5.0.2')
    def save_set(self, filename: str, set_name: Optional[str] = None) -> None:
        """
        Save global substitution set to a CSV file.

        Parameters:
            filename (str): Filename for the CSV file
            set_name (str): Set name to save (default is currently active set)

        .. versionadded:: 2.8.1
        """

        filename = mhi.common.path.expand_path(filename, abspath=True)

        if set_name:
            self.active_set = set_name
        self._prj._gs_save(filename, False)


    @requires('5.0.2')
    def load_set(self, filename: str, set_name: Optional[str] = None) -> None:
        """
        Load global substitution set from a CSV file, replacing current values

        Parameters:
            filename (str): Filename of the CSV file
            set_name (str): Set name to load (default is currently active set)

        .. versionadded:: 2.8.1
        """

        filename = mhi.common.path.expand_path(filename, abspath=True)

        if set_name:
            self.active_set = set_name
        self._prj._gs_load(filename, False, True)


    @requires('5.0.2')
    def append_set(self, filename: str, set_name: Optional[str] = None) -> None:
        """
        Load global substitution set from a CSV file, without clear old values

        Parameters:
            filename (str): Filename of the CSV file
            set_name (str): Set name to load (default is currently active set)

        .. versionadded:: 2.8.1
        """

        filename = mhi.common.path.expand_path(filename, abspath=True)

        if set_name:
            self.active_set = set_name
        self._prj._gs_load(filename, False, False)


    @requires('5.0.2')
    def save_all_sets(self, filename: str) -> None:
        """
        Save all global substitution sets to a CSV file.

        Parameters:
            filename (str): Filename for the CSV file

        .. versionadded:: 2.8.1
        """

        filename = mhi.common.path.expand_path(filename, abspath=True)

        self._prj._gs_save(filename, True)


    @requires('5.0.2')
    def load_all_sets(self, filename: str) -> None:
        """
        Load all global substitution sets from a CSV file, replacing all
        current values.

        Parameters:
            filename (str): Filename of the CSV file

        .. versionadded:: 2.8.1
        """

        filename = mhi.common.path.expand_path(filename, abspath=True)

        self._prj._gs_load(filename, True, True)


    @requires('5.0.2')
    def append_all_sets(self, filename: str) -> None:
        """
        Load global substitution sets from a CSV file, creating new sets when
        a set name already exists.

        Parameters:
            filename (str): Filename of the CSV file

        .. versionadded:: 2.8.1
        """

        filename = mhi.common.path.expand_path(filename, abspath=True)

        self._prj._gs_load(filename, True, False)


#===============================================================================
# Layer
#===============================================================================

class Layer(Remotable):
    """
    Project Component Layer
    """

    @rmi_property
    def project(self) -> str:
        """
        The project this layer belongs to (read-only)
        """


    @rmi_property
    def id(self) -> int:
        """
        The ID of this layer (read-only)
        """


    name = rmi_property(True, True, name='name',
                        doc='The name of this layer')

    state = rmi_property(True, True, name='state',
                         doc='The current state of this layer')

    #---------------------------------------------------------------------------

    @rmi
    def _add(self, *components):
        pass


    def add(self, *components: Component):
        """
        Add one or more components to this layer
        """

        if len(components) == 0:
            raise ValueError("Requires at least one component")

        return self._add(*components)

    #---------------------------------------------------------------------------

    @rmi
    def _parameters(self, parameters):
        pass


    @overload
    def parameters(self) -> Parameters: ...

    @overload
    def parameters(self, parameters: Optional[Parameters] = None,
                   **kwargs) -> None: ...

    def parameters(self, parameters: Optional[Parameters] = None,
                   **kwargs) -> Optional[Parameters]:
        """
        Get or set layer parameters

        Parameters:
            parameters (dict): A dictionary of name=value parameters
            **kwargs: Zero or more name=value keyword parameters

        Returns:
            A dictionary of current parameters, if no parameters were given.


        .. table:: Layer Properties

           ================= ===== ============================================
           Param Name        Type  Description
           ================= ===== ============================================
           disabled_color    Color Disabled Colour
           disabled_opacity  int   Diabled Opacity
           highlight_color   Color Highlight Colour
           highlight_opacity int   Highlight Opacity
           ================= ===== ============================================
        """

        codec = FormCodec.layer_options(self)

        # Combined **kwargs in parameters dictionary
        parameters = dict(parameters, **kwargs) if parameters else kwargs

        parameters = codec.encode(parameters)
        parameters = self._parameters(parameters)
        parameters = codec.decode(parameters)

        return parameters


    #---------------------------------------------------------------------------

    @rmi
    def _add_state(self, new_name):
        pass


    def add_state(self, new_name: str) -> None:
        """
        Create a new custom configuration name for list layer

        Parameters:
            new_name (str): Name of the new configuration to create.
        """
        self._add_state(new_name)


    #---------------------------------------------------------------------------

    @rmi
    def _remove_state(self, state_name):
        pass


    def remove_state(self, state_name: str) -> None:
        """
        Remove an existing custom state from this layer

        Parameters:
            state_name (str): The name of the custom configuration state to remove.
        """
        self._remove_state(state_name)


    #---------------------------------------------------------------------------

    @rmi
    def _rename_state(self, old_name, new_name):
        pass


    def rename_state(self, old_name: str, new_name: str) -> None:
        """
        Rename an existing custom state in this layer

        Parameters:
            old_name (str): The name of the custom configuration state to rename.
            new_name (str): The new name to rename the custom configuration state to.
        """
        self._rename_state(old_name, new_name)


    #---------------------------------------------------------------------------

    @rmi
    def _set_custom_state(self, state_name, component, component_state):
        pass


    def set_custom_state(self, state_name: str, component: Component,
                         component_state: str) -> None:
        """
        Set the state of a component when the layer is set to the state name provided.

        Parameters:
            state_name (str): The name of the custom configuration state to configure.
            component  (Component): The component to set the state to
            component_state (str): One of the strings ('Enabled', 'Disabled', 'Invisible') \
                for the state of the provided component when the provided state is set.
        """
        if component.layer != self.name:
            raise ValueError("Component not part of this layer")

        component.custom_state(state_name, component_state)


    #---------------------------------------------------------------------------

    def _move(self, delta):
        self._pscad.project(self.project)._move_layers(delta, [self.name])


    def move_up(self, delta: int = 1) -> None:
        """
        Move the layer up the list by 1
        """
        self._move(-delta)


    def move_down(self, delta: int = 1) -> None:
        """
        Move the layer down the list by 1
        """
        self._move(delta)


    def to_top(self) -> None:
        """
        Move the layer to top of list
        """
        self._move(-0x8000_0000)


    def to_bottom(self) -> None:
        """
        Move the layer to bottom of list
        """
        self._move(0x7fff_ffff)


#===============================================================================
# Resource
#===============================================================================

class Resource(Remotable):
    """
    Project Resource
    """

    @rmi_property
    def project(self) -> str:
        """
        The project this resource belongs to (read-only)
        """


    @rmi_property
    def id(self) -> int:
        """
        The ID of this resource (read-only)
        """


    @rmi_property
    def name(self) -> str:
        """
        The name of the this resource.
        """


    @rmi_property
    def path(self) -> str:
        """
        The path of the this resource, relative to the project.
        """


    @rmi_property
    def abspath(self) -> str:
        """
        The absolute path of the this resource.
        """


    def __repr__(self) -> str:

        return f"{self.project}.resource({self.path!r})"


    @rmi
    def _form_xml(self):
        pass


    def _param_codec(self):
        xml = self._form_xml()

        if xml:
            codec = FormCodec(xml)
        else:
            codec = None

        return codec


    @rmi
    def _parameters(self, parameters):
        pass


    @overload
    def parameters(self) -> Parameters: ...

    @overload
    def parameters(self, parameters: Optional[Parameters] = None,
                   **kwargs) -> None: ...

    def parameters(self, parameters: Optional[Parameters] = None,
                   **kwargs) -> Optional[Parameters]:
        """
        Get/Set Resource parameters
        """

        parameters = dict(parameters, **kwargs) if parameters else kwargs

        codec = self._param_codec()
        if codec is None:
            if parameters:
                raise NotImplementedError("No parameters for this resource")
            return {}

        if 'filepath' in parameters:
            if parameters['filepath'] != self.path:
                raise NotImplementedError('Cannot change filepath.  '
                                          'Remove & recreate resource.')

        parameters = codec.encode(parameters)
        parameters = self._parameters(parameters)
        parameters = codec.decode(parameters)

        return parameters
