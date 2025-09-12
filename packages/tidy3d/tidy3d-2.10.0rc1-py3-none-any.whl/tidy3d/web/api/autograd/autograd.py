# autograd wrapper for web functions
from __future__ import annotations

import os
import tempfile
import typing
from collections import defaultdict
from os.path import basename, dirname, join
from pathlib import Path

import numpy as np
import xarray as xr
from autograd.builtins import dict as dict_ag
from autograd.extend import defvjp, primitive

import tidy3d as td
from tidy3d.components.autograd import AutogradFieldMap, get_static
from tidy3d.components.autograd.constants import (
    ADJOINT_FREQ_CHUNK_SIZE,
    MAX_NUM_ADJOINT_PER_FWD,
    MAX_NUM_TRACED_STRUCTURES,
)
from tidy3d.components.autograd.derivative_utils import DerivativeInfo
from tidy3d.components.data.data_array import DataArray
from tidy3d.components.grid.grid_spec import GridSpec
from tidy3d.components.types.workflow import WorkflowDataType, WorkflowType
from tidy3d.exceptions import AdjointError
from tidy3d.web.api.asynchronous import DEFAULT_DATA_DIR
from tidy3d.web.api.asynchronous import run_async as run_async_webapi
from tidy3d.web.api.container import DEFAULT_DATA_PATH, Batch, BatchData, Job
from tidy3d.web.api.webapi import run as run_webapi
from tidy3d.web.core.s3utils import download_file, upload_file
from tidy3d.web.core.types import PayType

from .utils import E_to_D, FieldMap, TracerKeys, get_derivative_maps

# keys for data into auxiliary dictionary
AUX_KEY_SIM_DATA_ORIGINAL = "sim_data"
AUX_KEY_SIM_DATA_FWD = "sim_data_fwd_adjoint"
AUX_KEY_FWD_TASK_ID = "task_id_fwd"
AUX_KEY_SIM_ORIGINAL = "sim_original"
# server-side auxiliary files to upload/download
SIM_VJP_FILE = "output/autograd_sim_vjp.hdf5"
SIM_FIELDS_KEYS_FILE = "autograd_sim_fields_keys.hdf5"

# default value for whether to do local gradient calculation (True) or server side (False)
LOCAL_GRADIENT = False

# directory to store adjoint data for local gradient calculation relative to run path
LOCAL_ADJOINT_DIR = "adjoint_data"

# if True, will plot the adjoint fields on the plane provided. used for debugging only
_INSPECT_ADJOINT_FIELDS = False
_INSPECT_ADJOINT_PLANE = td.Box(center=(0, 0, 0), size=(td.inf, td.inf, 0))


def is_valid_for_autograd(simulation: td.Simulation) -> bool:
    """Check whether a supplied Simulation can use the autograd path."""
    if not isinstance(simulation, td.Simulation):
        return False

    # if no tracers just use regular web.run()
    traced_fields = simulation._strip_traced_fields(
        include_untraced_data_arrays=False, starting_path=("structures",)
    )
    if not traced_fields:
        return False

    # if no frequency-domain data (e.g. only field time monitors), raise an error
    if not simulation._freqs_adjoint:
        raise AdjointError(
            "No frequency-domain data found in simulation, but found traced structures. "
            "For an autograd run, you must have at least one frequency-domain monitor."
        )

    # if too many structures, raise an error
    structure_indices = {i for key, i, *_ in traced_fields.keys() if key == "structures"}
    num_traced_structures = len(structure_indices)
    if num_traced_structures > MAX_NUM_TRACED_STRUCTURES:
        raise AdjointError(
            f"Autograd support is currently limited to {MAX_NUM_TRACED_STRUCTURES} structures with "
            f"traced fields. Found {num_traced_structures} structures with traced fields."
        )

    return True


def is_valid_for_autograd_async(simulations: dict[str, td.Simulation]) -> bool:
    """Check whether the supplied simulations dict can use autograd run_async."""
    if not isinstance(simulations, dict):
        return False
    if not all(is_valid_for_autograd(sim) for sim in simulations.values()):
        return False
    return True


def run(
    simulation: WorkflowType,
    task_name: str,
    folder_name: str = "default",
    path: str = "simulation_data.hdf5",
    callback_url: typing.Optional[str] = None,
    verbose: bool = True,
    progress_callback_upload: typing.Optional[typing.Callable[[float], None]] = None,
    progress_callback_download: typing.Optional[typing.Callable[[float], None]] = None,
    solver_version: typing.Optional[str] = None,
    worker_group: typing.Optional[str] = None,
    simulation_type: str = "tidy3d",
    parent_tasks: typing.Optional[list[str]] = None,
    local_gradient: bool = LOCAL_GRADIENT,
    max_num_adjoint_per_fwd: int = MAX_NUM_ADJOINT_PER_FWD,
    reduce_simulation: typing.Literal["auto", True, False] = "auto",
    pay_type: typing.Union[PayType, str] = PayType.AUTO,
    priority: typing.Optional[int] = None,
) -> WorkflowDataType:
    """
    Submits a :class:`.Simulation` to server, starts running, monitors progress, downloads,
    and loads results as a :class:`.WorkflowDataType` object.

    Parameters
    ----------
    simulation : Union[:class:`.Simulation`, :class:`.HeatSimulation`, :class:`.EMESimulation`, :class:`.ModalComponentModeler`, :class:`.TerminalComponentModeler`]
        Simulation to upload to server.
    task_name : str
        Name of task.
    folder_name : str = "default"
        Name of folder to store task on web UI.
    path : str = "simulation_data.hdf5"
        Path to download results file (.hdf5), including filename.
    callback_url : str = None
        Http PUT url to receive simulation finish event. The body content is a json file with
        fields ``{'id', 'status', 'name', 'workUnit', 'solverVersion'}``.
    verbose : bool = True
        If ``True``, will print progressbars and status, otherwise, will run silently.
    simulation_type : str = "tidy3d"
        Type of simulation being uploaded.
    progress_callback_upload : Callable[[float], None] = None
        Optional callback function called when uploading file with ``bytes_in_chunk`` as argument.
    progress_callback_download : Callable[[float], None] = None
        Optional callback function called when downloading file with ``bytes_in_chunk`` as argument.
    solver_version: str = None
        target solver version.
    worker_group: str = None
        worker group
    local_gradient: bool = False
        Whether to perform gradient calculation locally, requiring more downloads but potentially
        more stable with experimental features.
    max_num_adjoint_per_fwd: int = 10
        Maximum number of adjoint simulations allowed to run automatically.
    reduce_simulation: Literal["auto", True, False] = "auto"
        Whether to reduce structures in the simulation to the simulation domain only. Note: currently only implemented for the mode solver.
    pay_type: typing.Union[PayType, str] = PayType.AUTO
        Which method to pay for the simulation.
    priority: int = None
        Task priority for vGPU queue (1=lowest, 10=highest).
    Returns
    -------
    Union[:class:`.SimulationData`, :class:`.HeatSimulationData`, :class:`.EMESimulationData`, :class:`.ModalComponentModelerData`, :class:`.TerminalComponentModelerData`]
        Object containing solver results for the supplied input.

    Notes
    -----

        Submitting a simulation to our cloud server is very easily done by a simple web API call.

        .. code-block:: python

            sim_data = tidy3d.web.api.webapi.run(simulation, task_name='my_task', path='out/data.hdf5')

        The :meth:`tidy3d.web.api.webapi.run()` method shows the simulation progress by default.  When uploading a
        simulation to the server without running it, you can use the :meth:`tidy3d.web.api.webapi.monitor`,
        :meth:`tidy3d.web.api.container.Job.monitor`, or :meth:`tidy3d.web.api.container.Batch.monitor` methods to
        display the progress of your simulation(s).

    Examples
    --------

        To access the original :class:`.Simulation` object that created the simulation data you can use:

        .. code-block:: python

            # Run the simulation.
            sim_data = web.run(simulation, task_name='task_name', path='out/sim.hdf5')

            # Get a copy of the original simulation object.
            sim_copy = sim_data.simulation

    See Also
    --------

    :meth:`tidy3d.web.api.webapi.monitor`
        Print the real time task progress until completion.

    :meth:`tidy3d.web.api.container.Job.monitor`
        Monitor progress of running :class:`Job`.

    :meth:`tidy3d.web.api.container.Batch.monitor`
        Monitor progress of each of the running tasks.
    """
    if priority is not None and (priority < 1 or priority > 10):
        raise ValueError("Priority must be between '1' and '10' if specified.")

    # component modeler path: route autograd-valid modelers to local run
    from tidy3d.plugins.smatrix.component_modelers.types import ComponentModelerType

    if isinstance(simulation, typing.get_args(ComponentModelerType)):
        if any(is_valid_for_autograd(s) for s in simulation.sim_dict.values()):
            from tidy3d.plugins.smatrix import run as smatrix_run

            path_dir = dirname(path) or "."
            return smatrix_run._run_local(
                simulation,
                path_dir=path_dir,
                folder_name=folder_name,
                callback_url=callback_url,
                verbose=verbose,
                solver_version=solver_version,
                pay_type=pay_type,
                priority=priority,
                local_gradient=local_gradient,
                max_num_adjoint_per_fwd=max_num_adjoint_per_fwd,
            )

    if isinstance(simulation, td.Simulation) and is_valid_for_autograd(simulation):
        return _run(
            simulation=simulation,
            task_name=task_name,
            folder_name=folder_name,
            path=path,
            callback_url=callback_url,
            verbose=verbose,
            progress_callback_upload=progress_callback_upload,
            progress_callback_download=progress_callback_download,
            solver_version=solver_version,
            worker_group=worker_group,
            simulation_type="tidy3d_autograd",
            parent_tasks=parent_tasks,
            local_gradient=local_gradient,
            max_num_adjoint_per_fwd=max_num_adjoint_per_fwd,
            pay_type=pay_type,
            priority=priority,
        )

    return run_webapi(
        simulation=simulation,
        task_name=task_name,
        folder_name=folder_name,
        path=path,
        callback_url=callback_url,
        verbose=verbose,
        progress_callback_upload=progress_callback_upload,
        progress_callback_download=progress_callback_download,
        solver_version=solver_version,
        worker_group=worker_group,
        simulation_type=simulation_type,
        parent_tasks=parent_tasks,
        reduce_simulation=reduce_simulation,
        pay_type=pay_type,
        priority=priority,
    )


def run_async(
    simulations: dict[str, td.Simulation],
    folder_name: str = "default",
    path_dir: str = DEFAULT_DATA_DIR,
    callback_url: typing.Optional[str] = None,
    num_workers: typing.Optional[int] = None,
    verbose: bool = True,
    simulation_type: str = "tidy3d",
    solver_version: typing.Optional[str] = None,
    parent_tasks: typing.Optional[dict[str, list[str]]] = None,
    local_gradient: bool = LOCAL_GRADIENT,
    max_num_adjoint_per_fwd: int = MAX_NUM_ADJOINT_PER_FWD,
    reduce_simulation: typing.Literal["auto", True, False] = "auto",
    pay_type: typing.Union[PayType, str] = PayType.AUTO,
    priority: typing.Optional[int] = None,
) -> BatchData:
    """Submits a set of Union[:class:`.Simulation`, :class:`.HeatSimulation`, :class:`.EMESimulation`] objects to server,
    starts running, monitors progress, downloads, and loads results as a :class:`.BatchData` object.

    .. TODO add example and see also reference.

    Parameters
    ----------
    simulations : Dict[str, Union[:class:`.Simulation`, :class:`.HeatSimulation`, :class:`.EMESimulation`]]
        Mapping of task name to simulation.
    folder_name : str = "default"
        Name of folder to store each task on web UI.
    path_dir : str
        Base directory where data will be downloaded, by default current working directory.
    callback_url : str = None
        Http PUT url to receive simulation finish event. The body content is a json file with
        fields ``{'id', 'status', 'name', 'workUnit', 'solverVersion'}``.
    num_workers: int = None
        Number of tasks to submit at once in a batch, if None, will run all at the same time.
    verbose : bool = True
        If ``True``, will print progressbars and status, otherwise, will run silently.
    simulation_type : str = "tidy3d"
        Type of simulation being uploaded.
    solver_version: Optional[str] = None
        Target solver version.
    local_gradient: bool = False
        Whether to perform gradient calculations locally, requiring more downloads but potentially
        more stable with experimental features.
    max_num_adjoint_per_fwd: int = 10
        Maximum number of adjoint simulations allowed to run automatically.
    reduce_simulation: Literal["auto", True, False] = "auto"
        Whether to reduce structures in the simulation to the simulation domain only. Note: currently only implemented for the mode solver.
    pay_type: typing.Union[PayType, str] = PayType.AUTO
        Specify the payment method.

    Returns
    ------
    :class:`BatchData`
        Contains the Union[:class:`.SimulationData`, :class:`.HeatSimulationData`, :class:`.EMESimulationData`] for each
        Union[:class:`.Simulation`, :class:`.HeatSimulation`, :class:`.EMESimulation`] in :class:`Batch`.

    See Also
    --------

    :class:`Job`:
        Interface for managing the running of a Simulation on server.

    :class:`Batch`
        Interface for submitting several :class:`.Simulation` objects to sever.
    """
    # validate priority if specified
    if priority is not None and (priority < 1 or priority > 10):
        raise ValueError("Priority must be between '1' and '10' if specified.")

    if is_valid_for_autograd_async(simulations):
        return _run_async(
            simulations=simulations,
            folder_name=folder_name,
            path_dir=path_dir,
            callback_url=callback_url,
            num_workers=num_workers,
            verbose=verbose,
            simulation_type="tidy3d_autograd_async",
            solver_version=solver_version,
            parent_tasks=parent_tasks,
            local_gradient=local_gradient,
            max_num_adjoint_per_fwd=max_num_adjoint_per_fwd,
            pay_type=pay_type,
            priority=priority,
        )

    return run_async_webapi(
        simulations=simulations,
        folder_name=folder_name,
        path_dir=path_dir,
        callback_url=callback_url,
        num_workers=num_workers,
        verbose=verbose,
        simulation_type=simulation_type,
        solver_version=solver_version,
        parent_tasks=parent_tasks,
        reduce_simulation=reduce_simulation,
        pay_type=pay_type,
        priority=priority,
    )


""" User-facing ``run`` and `run_async`` functions, compatible with ``autograd`` """


def _run(
    simulation: td.Simulation,
    task_name: str,
    local_gradient: bool = LOCAL_GRADIENT,
    max_num_adjoint_per_fwd: int = MAX_NUM_ADJOINT_PER_FWD,
    **run_kwargs,
) -> td.SimulationData:
    """User-facing ``web.run`` function, compatible with ``autograd`` differentiation."""

    traced_fields_sim = setup_run(simulation=simulation)

    # if we register this as not needing adjoint at all (no tracers), call regular run function
    if not traced_fields_sim:
        td.log.warning(
            "No autograd derivative tracers found in the 'Simulation' passed to 'run'. "
            "This could indicate that there is no path from your objective function arguments "
            "to the 'Simulation'. If this is unexpected, double check your objective function "
            "pre-processing. Running regular tidy3d simulation."
        )
        data, _ = _run_tidy3d(simulation, task_name=task_name, **run_kwargs)
        return data

    # will store the SimulationData for original and forward so we can access them later
    aux_data = {}

    # run our custom @primitive, passing the traced fields first to register with autograd
    traced_fields_data = _run_primitive(
        traced_fields_sim,  # if you pass as a kwarg it will not trace :/
        sim_original=simulation.to_static(),
        task_name=task_name,
        aux_data=aux_data,
        local_gradient=local_gradient,
        max_num_adjoint_per_fwd=max_num_adjoint_per_fwd,
        **run_kwargs,
    )

    return postprocess_run(traced_fields_data=traced_fields_data, aux_data=aux_data)


def _run_async(
    simulations: dict[str, td.Simulation],
    local_gradient: bool = LOCAL_GRADIENT,
    max_num_adjoint_per_fwd: int = MAX_NUM_ADJOINT_PER_FWD,
    **run_async_kwargs,
) -> dict[str, td.SimulationData]:
    """User-facing ``web.run_async`` function, compatible with ``autograd`` differentiation."""

    task_names = simulations.keys()

    traced_fields_sim_dict = {}
    for task_name in task_names:
        traced_fields_sim_dict[task_name] = setup_run(simulation=simulations[task_name])
    traced_fields_sim_dict = dict_ag(traced_fields_sim_dict)

    # TODO: shortcut primitive running for any items with no tracers?

    aux_data_dict = {task_name: {} for task_name in task_names}
    sims_original = {
        task_name: simulation.to_static() for task_name, simulation in simulations.items()
    }
    traced_fields_data_dict = _run_async_primitive(
        traced_fields_sim_dict,  # if you pass as a kwarg it will not trace :/
        sims_original=sims_original,
        aux_data_dict=aux_data_dict,
        local_gradient=local_gradient,
        max_num_adjoint_per_fwd=max_num_adjoint_per_fwd,
        **run_async_kwargs,
    )

    # TODO: package this as a Batch? it might be not possible as autograd tracers lose their
    # powers when we save them to file.
    sim_data_dict = {}
    for task_name in task_names:
        traced_fields_data = traced_fields_data_dict[task_name]
        aux_data = aux_data_dict[task_name]
        sim_data = postprocess_run(traced_fields_data=traced_fields_data, aux_data=aux_data)
        sim_data_dict[task_name] = sim_data

    return sim_data_dict


def setup_run(simulation: td.Simulation) -> AutogradFieldMap:
    """Process a user-supplied ``Simulation`` into inputs to ``_run_primitive``."""

    # get a mapping of all the traced fields in the provided simulation
    return simulation._strip_traced_fields(
        include_untraced_data_arrays=False, starting_path=("structures",)
    )


def postprocess_run(traced_fields_data: AutogradFieldMap, aux_data: dict) -> td.SimulationData:
    """Process the return from ``_run_primitive`` into ``SimulationData`` for user."""

    # grab the user's 'SimulationData' and return with the autograd-tracers inserted
    sim_data_original = aux_data[AUX_KEY_SIM_DATA_ORIGINAL]
    return sim_data_original._insert_traced_fields(traced_fields_data)


""" Autograd-traced Primitive for FWD pass ``run`` functions """


@primitive
def _run_primitive(
    sim_fields: AutogradFieldMap,
    sim_original: td.Simulation,
    task_name: str,
    aux_data: dict,
    local_gradient: bool,
    max_num_adjoint_per_fwd: int,
    **run_kwargs,
) -> AutogradFieldMap:
    """Autograd-traced 'run()' function: runs simulation, strips tracer data, caches fwd data."""

    td.log.info("running primitive '_run_primitive()'")

    # indicate this is a forward run. not exposed to user but used internally by pipeline.
    run_kwargs["is_adjoint"] = False

    # compute the combined simulation for both local and remote, so we can validate it
    sim_combined = setup_fwd(
        sim_fields=sim_fields,
        sim_original=sim_original,
        local_gradient=local_gradient,
    )

    if local_gradient:
        sim_data_combined, _ = _run_tidy3d(sim_combined, task_name=task_name, **run_kwargs)

        field_map = postprocess_fwd(
            sim_data_combined=sim_data_combined,
            sim_original=sim_original,
            aux_data=aux_data,
        )
    else:
        sim_combined.validate_pre_upload()
        sim_original = sim_original.updated_copy(simulation_type="autograd_fwd", deep=False)
        run_kwargs["simulation_type"] = "autograd_fwd"
        run_kwargs["sim_fields_keys"] = list(sim_fields.keys())

        sim_data_orig, task_id_fwd = _run_tidy3d(
            sim_original,
            task_name=task_name,
            **run_kwargs,
        )

        # TODO: put this in postprocess?
        aux_data[AUX_KEY_FWD_TASK_ID] = task_id_fwd
        aux_data[AUX_KEY_SIM_DATA_ORIGINAL] = sim_data_orig
        field_map = sim_data_orig._strip_traced_fields(
            include_untraced_data_arrays=True, starting_path=("data",)
        )

    return field_map


@primitive
def _run_async_primitive(
    sim_fields_dict: dict[str, AutogradFieldMap],
    sims_original: dict[str, td.Simulation],
    aux_data_dict: dict[dict[str, typing.Any]],
    local_gradient: bool,
    max_num_adjoint_per_fwd: int,
    **run_async_kwargs,
) -> dict[str, AutogradFieldMap]:
    task_names = sim_fields_dict.keys()

    sims_combined = {}
    for task_name in task_names:
        sim_fields = sim_fields_dict[task_name]
        sim_original = sims_original[task_name]
        sims_combined[task_name] = setup_fwd(
            sim_fields=sim_fields,
            sim_original=sim_original,
            local_gradient=local_gradient,
        )

    if local_gradient:
        batch_data_combined, _ = _run_async_tidy3d(sims_combined, **run_async_kwargs)

        field_map_fwd_dict = {}
        for task_name in task_names:
            sim_data_combined = batch_data_combined[task_name]
            sim_original = sims_original[task_name]
            aux_data = aux_data_dict[task_name]
            field_map_fwd_dict[task_name] = postprocess_fwd(
                sim_data_combined=sim_data_combined,
                sim_original=sim_original,
                aux_data=aux_data,
            )
    else:
        for sim in sims_combined.values():
            sim.validate_pre_upload()
        run_async_kwargs["simulation_type"] = "autograd_fwd"
        run_async_kwargs["sim_fields_keys_dict"] = {}
        for task_name, sim_fields in sim_fields_dict.items():
            run_async_kwargs["sim_fields_keys_dict"][task_name] = list(sim_fields.keys())

        sims_original = {
            task_name: sim.updated_copy(simulation_type="autograd_fwd", deep=False)
            for task_name, sim in sims_original.items()
        }

        sim_data_orig_dict, task_ids_fwd_dict = _run_async_tidy3d(
            sims_original,
            **run_async_kwargs,
        )

        field_map_fwd_dict = {}
        for task_name, task_id_fwd in task_ids_fwd_dict.items():
            sim_data_orig = sim_data_orig_dict[task_name]
            aux_data_dict[task_name][AUX_KEY_FWD_TASK_ID] = task_id_fwd
            aux_data_dict[task_name][AUX_KEY_SIM_DATA_ORIGINAL] = sim_data_orig
            field_map = sim_data_orig._strip_traced_fields(
                include_untraced_data_arrays=True, starting_path=("data",)
            )
            field_map_fwd_dict[task_name] = field_map

    return field_map_fwd_dict


def setup_fwd(
    sim_fields: AutogradFieldMap,
    sim_original: td.Simulation,
    local_gradient: bool = LOCAL_GRADIENT,
) -> td.Simulation:
    """Return a forward simulation with adjoint monitors attached."""

    # Always try to build the variant that includes adjoint monitors so that
    # errors in monitor placement are caught early.
    sim_with_adj_mon = sim_original._with_adjoint_monitors(sim_fields)
    return sim_with_adj_mon if local_gradient else sim_original


def postprocess_fwd(
    sim_data_combined: td.SimulationData,
    sim_original: td.Simulation,
    aux_data: dict,
) -> AutogradFieldMap:
    """Postprocess the combined simulation data into an Autograd field map."""

    num_mnts_original = len(sim_original.monitors)
    sim_data_original, sim_data_fwd = sim_data_combined._split_original_fwd(
        num_mnts_original=num_mnts_original
    )

    aux_data[AUX_KEY_SIM_DATA_ORIGINAL] = sim_data_original
    aux_data[AUX_KEY_SIM_DATA_FWD] = sim_data_fwd

    # strip out the tracer AutogradFieldMap for the .data from the original sim
    data_traced = sim_data_original._strip_traced_fields(
        include_untraced_data_arrays=True, starting_path=("data",)
    )

    # return the AutogradFieldMap that autograd registers as the "output" of the primitive
    return data_traced


def upload_sim_fields_keys(sim_fields_keys: list[tuple], task_id: str, verbose: bool = False):
    """Function to grab the VJP result for the simulation fields from the adjoint task ID."""
    handle, fname = tempfile.mkstemp(suffix=".hdf5")
    os.close(handle)
    try:
        TracerKeys(keys=sim_fields_keys).to_file(fname)
        upload_file(
            task_id,
            fname,
            SIM_FIELDS_KEYS_FILE,
            verbose=verbose,
        )
    except Exception as e:
        td.log.error(f"Error occurred while uploading simulation fields keys: {e}")
        raise e
    finally:
        os.unlink(fname)


""" VJP maker for ADJ pass."""


def get_vjp_traced_fields(task_id_adj: str, verbose: bool) -> AutogradFieldMap:
    """Function to grab the VJP result for the simulation fields from the adjoint task ID."""
    handle, fname = tempfile.mkstemp(suffix=".hdf5")
    os.close(handle)
    try:
        download_file(task_id_adj, SIM_VJP_FILE, to_file=fname, verbose=verbose)
        field_map = FieldMap.from_file(fname)
    except Exception as e:
        td.log.error(f"Error occurred while getting VJP traced fields: {e}")
        raise e
    finally:
        os.unlink(fname)
    return field_map.to_autograd_field_map


def _run_bwd(
    data_fields_original: AutogradFieldMap,
    sim_fields_original: AutogradFieldMap,
    sim_original: td.Simulation,
    task_name: str,
    aux_data: dict,
    local_gradient: bool,
    max_num_adjoint_per_fwd: int,
    **run_kwargs,
) -> typing.Callable[[AutogradFieldMap], AutogradFieldMap]:
    """VJP-maker for ``_run_primitive()``. Constructs and runs adjoint simulations, computes grad."""

    # indicate this is an adjoint run
    run_kwargs["is_adjoint"] = True

    # get the fwd epsilon and field data from the cached aux_data
    sim_data_orig = aux_data[AUX_KEY_SIM_DATA_ORIGINAL]
    sim_fields_keys = list(sim_fields_original.keys())

    td.log.info(f"Number of fields to compute gradients for: {len(sim_fields_keys)}")

    if local_gradient:
        sim_data_fwd = aux_data[AUX_KEY_SIM_DATA_FWD]
        td.log.info("Using local gradient computation mode")
    else:
        td.log.info("Using server-side gradient computation mode")

    td.log.info("Constructing custom VJP function for backwards pass.")

    def vjp(data_fields_vjp: AutogradFieldMap) -> AutogradFieldMap:
        """dJ/d{sim.traced_fields()} as a function of Function of dJ/d{data.traced_fields()}"""

        # build the (possibly multiple) adjoint simulations
        sims_adj = setup_adj(
            data_fields_vjp=data_fields_vjp,
            sim_data_orig=sim_data_orig,
            sim_fields_keys=sim_fields_keys,
            max_num_adjoint_per_fwd=max_num_adjoint_per_fwd,
        )

        if not sims_adj:
            td.log.warning(
                f"Adjoint simulation for task '{task_name}' contains no sources. "
                "This can occur if the objective function does not depend on the "
                "simulation's output. If this is unexpected, please review your "
                "setup or contact customer support for assistance."
            )
            return {
                k: (type(v)(0 * x for x in v) if isinstance(v, (list, tuple)) else 0 * v)
                for k, v in sim_fields_original.items()
            }

        # Run adjoint simulations in batch
        task_names_adj = [f"{task_name}_adjoint_{i}" for i in range(len(sims_adj))]
        sims_adj_dict = dict(zip(task_names_adj, sims_adj))

        td.log.info(f"Running {len(sims_adj)} adjoint simulations")

        vjp_traced_fields = {}

        if local_gradient:
            # Run all adjoint sims in batch
            td.log.info("Starting local batch adjoint simulations")
            path = Path(run_kwargs.pop("path"))
            path_dir_adj = path.parent / LOCAL_ADJOINT_DIR
            path_dir_adj.mkdir(exist_ok=True)

            batch_data_adj, _ = _run_async_tidy3d(
                sims_adj_dict, path_dir=str(path_dir_adj), **run_kwargs
            )
            td.log.info("Completed local batch adjoint simulations")

            # Process results from local gradient computation
            vjp_fields_dict = {}
            for task_name_adj, sim_data_adj in batch_data_adj.items():
                td.log.info(f"Processing VJP contribution from {task_name_adj}")
                vjp_fields_dict[task_name_adj] = postprocess_adj(
                    sim_data_adj=sim_data_adj,
                    sim_data_orig=sim_data_orig,
                    sim_data_fwd=sim_data_fwd,
                    sim_fields_keys=sim_fields_keys,
                )
        else:
            td.log.info("Starting server-side batch of adjoint simulations ...")

            # Link each adjoint sim to the forward task it depends on
            task_id_fwd = aux_data[AUX_KEY_FWD_TASK_ID]
            run_kwargs["simulation_type"] = "autograd_bwd"

            # Build a per-task parent_tasks mapping
            parent_tasks = {}
            for tname_adj in sims_adj_dict:
                parent_tasks[tname_adj] = [task_id_fwd]
            run_kwargs["parent_tasks"] = parent_tasks

            # Update each simulation's type, then run them in batch
            sims_adj_dict = {
                tname_adj: sim.updated_copy(simulation_type="autograd_bwd", deep=False)
                for tname_adj, sim in sims_adj_dict.items()
            }
            vjp_fields_dict = _run_async_tidy3d_bwd(
                simulations=sims_adj_dict,
                **run_kwargs,
            )
            td.log.info("Completed server-side batch of adjoint simulations.")

        # Accumulate gradients from all adjoint simulations
        for task_name_adj, vjp_fields in vjp_fields_dict.items():
            td.log.info(f"Processing VJP contribution from {task_name_adj}")
            for k, v in vjp_fields.items():
                if k in vjp_traced_fields:
                    val = vjp_traced_fields[k]
                    if isinstance(val, (list, tuple)) and isinstance(v, (list, tuple)):
                        vjp_traced_fields[k] = type(val)(x + y for x, y in zip(val, v))
                    else:
                        vjp_traced_fields[k] += v
                else:
                    vjp_traced_fields[k] = v

        td.log.debug(f"Computed gradients for {len(vjp_traced_fields)} fields")
        return vjp_traced_fields

    return vjp


def _run_async_bwd(
    data_fields_original_dict: dict[str, AutogradFieldMap],
    sim_fields_original_dict: dict[str, AutogradFieldMap],
    sims_original: dict[str, td.Simulation],
    aux_data_dict: dict[str, dict[str, typing.Any]],
    local_gradient: bool,
    max_num_adjoint_per_fwd: int,
    **run_async_kwargs,
) -> typing.Callable[[dict[str, AutogradFieldMap]], dict[str, AutogradFieldMap]]:
    """VJP-maker for ``_run_primitive()``. Constructs and runs adjoint simulation, computes grad."""

    # indicate this is an adjoint run
    run_async_kwargs["is_adjoint"] = True

    task_names = data_fields_original_dict.keys()

    # get the fwd epsilon and field data from the cached aux_data
    sim_data_orig_dict = {}
    sim_data_fwd_dict = {}
    sim_fields_keys_dict = {}
    for task_name in task_names:
        aux_data = aux_data_dict[task_name]
        sim_data_orig_dict[task_name] = aux_data[AUX_KEY_SIM_DATA_ORIGINAL]
        sim_fields_keys_dict[task_name] = list(sim_fields_original_dict[task_name].keys())

        if local_gradient:
            sim_data_fwd_dict[task_name] = aux_data[AUX_KEY_SIM_DATA_FWD]

    td.log.info("constructing custom vjp function for backwards pass.")

    def vjp(data_fields_dict_vjp: dict[str, AutogradFieldMap]) -> dict[str, AutogradFieldMap]:
        """dJ/d{sim.traced_fields()} as a function of Function of dJ/d{data.traced_fields()}"""

        # Collect all adjoint simulations across all forward tasks
        all_sims_adj = {}
        sim_fields_vjp_dict = {}
        task_name_mapping = {}  # Maps adjoint task names to original task names

        for task_name in task_names:
            data_fields_vjp = data_fields_dict_vjp[task_name]
            sim_data_orig = sim_data_orig_dict[task_name]
            sim_fields_keys = sim_fields_keys_dict[task_name]

            sims_adj = setup_adj(
                data_fields_vjp=data_fields_vjp,
                sim_data_orig=sim_data_orig,
                sim_fields_keys=sim_fields_keys,
                max_num_adjoint_per_fwd=max_num_adjoint_per_fwd,
            )

            if not sims_adj:
                td.log.debug(f"Adjoint simulation for task '{task_name}' contains no sources.")
                sim_fields_vjp_dict[task_name] = {
                    k: (type(v)(0 * x for x in v) if isinstance(v, (list, tuple)) else 0 * v)
                    for k, v in sim_fields_original_dict[task_name].items()
                }
                continue

            # Add each adjoint simulation to the combined batch with unique task names
            for i, sim_adj in enumerate(sims_adj):
                adj_task_name = f"{task_name}_adjoint_{i}"
                all_sims_adj[adj_task_name] = sim_adj
                task_name_mapping[adj_task_name] = task_name

        if not all_sims_adj:
            td.log.warning(
                "No simulation in batch contains adjoint sources and thus all gradients are zero."
            )
            return sim_fields_vjp_dict

        # Dictionary to store VJP results from all adjoint simulations
        vjp_results = {}

        if local_gradient:
            # Run all adjoint simulations in a single batch
            path_dir = Path(run_async_kwargs.pop("path_dir"))
            path_dir_adj = path_dir / LOCAL_ADJOINT_DIR
            path_dir_adj.mkdir(exist_ok=True)

            batch_data_adj, _ = _run_async_tidy3d(
                all_sims_adj, path_dir=str(path_dir_adj), **run_async_kwargs
            )

            # Process results for each adjoint task
            for adj_task_name, sim_data_adj in batch_data_adj.items():
                task_name = task_name_mapping[adj_task_name]
                sim_data_orig = sim_data_orig_dict[task_name]
                sim_data_fwd = sim_data_fwd_dict[task_name]
                sim_fields_keys = sim_fields_keys_dict[task_name]

                # Compute VJP contribution
                vjp_results[adj_task_name] = postprocess_adj(
                    sim_data_adj=sim_data_adj,
                    sim_data_orig=sim_data_orig,
                    sim_data_fwd=sim_data_fwd,
                    sim_fields_keys=sim_fields_keys,
                )
        else:
            # Set up parent tasks mapping for all adjoint simulations
            parent_tasks = {}
            for adj_task_name, task_name in task_name_mapping.items():
                task_id_fwd = aux_data_dict[task_name][AUX_KEY_FWD_TASK_ID]
                parent_tasks[adj_task_name] = [task_id_fwd]

            run_async_kwargs["parent_tasks"] = parent_tasks
            run_async_kwargs["simulation_type"] = "autograd_bwd"

            # Update simulation types
            all_sims_adj = {
                task_name: sim.updated_copy(simulation_type="autograd_bwd", deep=False)
                for task_name, sim in all_sims_adj.items()
            }

            # Run all adjoint simulations in a single batch
            vjp_results = _run_async_tidy3d_bwd(
                simulations=all_sims_adj,
                **run_async_kwargs,
            )

        # Accumulate gradients from all adjoint simulations
        for adj_task_name, vjp_fields in vjp_results.items():
            task_name = task_name_mapping[adj_task_name]

            if task_name not in sim_fields_vjp_dict:
                sim_fields_vjp_dict[task_name] = {}

            for k, v in vjp_fields.items():
                if k in sim_fields_vjp_dict[task_name]:
                    val = sim_fields_vjp_dict[task_name][k]
                    if isinstance(val, (list, tuple)) and isinstance(v, (list, tuple)):
                        sim_fields_vjp_dict[task_name][k] = type(val)(x + y for x, y in zip(val, v))
                    else:
                        sim_fields_vjp_dict[task_name][k] += v
                else:
                    sim_fields_vjp_dict[task_name][k] = v

        return sim_fields_vjp_dict

    return vjp


def setup_adj(
    data_fields_vjp: AutogradFieldMap,
    sim_data_orig: td.SimulationData,
    sim_fields_keys: list[tuple],
    max_num_adjoint_per_fwd: int,
) -> list[td.Simulation]:
    """Construct an adjoint simulation from a set of data_fields for the VJP."""

    td.log.info("Running custom vjp (adjoint) pipeline.")

    # filter out any data_fields_vjp with all 0's
    data_fields_vjp = {
        k: get_static(v) for k, v in data_fields_vjp.items() if not np.allclose(v, 0)
    }

    for k, v in data_fields_vjp.items():
        if np.any(np.isnan(v)):
            raise AdjointError(
                f"NaN values detected for data field {k} in the adjoint pipeline. This may be "
                f"due to NaN values in the simulation data or the computed value of your "
                f"objective function."
            )

    # if all entries are zero, there is no adjoint sim to run
    if not data_fields_vjp:
        return []

    # start with the full simulation data structure and either zero out the fields
    # that have no tracer data for them or insert the tracer data
    full_sim_data_dict = sim_data_orig._strip_traced_fields(
        include_untraced_data_arrays=True, starting_path=("data",)
    )
    for path in full_sim_data_dict.keys():
        if path in data_fields_vjp:
            full_sim_data_dict[path] = data_fields_vjp[path]
        else:
            full_sim_data_dict[path] *= 0

    # insert the raw VJP data into the .data of the original SimulationData
    sim_data_vjp = sim_data_orig._insert_traced_fields(field_mapping=full_sim_data_dict)

    # make adjoint simulation from that SimulationData
    data_vjp_paths = set(data_fields_vjp.keys())

    num_monitors = len(sim_data_orig.simulation.monitors)
    adjoint_monitors = sim_data_orig.simulation._with_adjoint_monitors(sim_fields_keys).monitors[
        num_monitors:
    ]

    sims_adj = sim_data_vjp._make_adjoint_sims(
        data_vjp_paths=data_vjp_paths,
        adjoint_monitors=adjoint_monitors,
    )

    if _INSPECT_ADJOINT_FIELDS and sims_adj:
        adj_fld_mnt = td.FieldMonitor(
            center=_INSPECT_ADJOINT_PLANE.center,
            size=_INSPECT_ADJOINT_PLANE.size,
            freqs=adjoint_monitors[0].freqs,
            name="adjoint_fields",
        )

        import matplotlib.pylab as plt

        import tidy3d.web as web

        sim_data_new = web.run(
            sims_adj[0].updated_copy(monitors=[adj_fld_mnt]),
            task_name="adjoint_field_viz",
            verbose=False,
        )
        _, (ax1, ax2, ax3) = plt.subplots(1, 3, tight_layout=True, figsize=(10, 4))
        sim_data_new.plot_field("adjoint_fields", "Ex", "re", ax=ax1)
        sim_data_new.plot_field("adjoint_fields", "Ey", "re", ax=ax2)
        sim_data_new.plot_field("adjoint_fields", "Ez", "re", ax=ax3)
        plt.show()

    if len(sims_adj) > max_num_adjoint_per_fwd:
        raise AdjointError(
            f"Number of adjoint simulations ({len(sims_adj)}) exceeds the maximum allowed "
            f"({max_num_adjoint_per_fwd}) per forward simulation. This typically means that "
            "there are many frequencies and monitors in the simulation that are being differentiated "
            "w.r.t. in the objective function. To proceed, please double-check the simulation "
            "setup, increase the 'max_num_adjoint_per_fwd' parameter in the run function, and re-run."
        )

    return sims_adj


def _compute_eps_array(medium, frequencies):
    """Compute permittivity array for all frequencies.

    Parameters
    ----------
    medium : Medium
        Medium to compute permittivity for.
    frequencies : ArrayLike
        Array of frequencies at which to evaluate permittivity.

    Returns
    -------
    DataArray
        Permittivity values with frequency dimension.
    """
    eps_data = [np.mean(medium.eps_model(f)) for f in frequencies]
    return DataArray(data=np.array(eps_data), dims=("f",), coords={"f": frequencies})


def _slice_field_data(
    field_data: dict, freqs: np.ndarray, component_indicator: typing.Optional[str] = None
) -> dict:
    """Slice field data dictionary along frequency dimension.

    Parameters
    ----------
    field_data : dict
        Dictionary of field components.
    freqs : np.ndarray
        Frequencies to select.
    component_indicator: str
        Component to filter field data selction on.

    Returns
    -------
    dict
        Sliced field data dictionary.
    """
    if component_indicator:
        return {k: v.sel(f=freqs) for k, v in field_data.items() if component_indicator in k}
    else:
        return {k: v.sel(f=freqs) for k, v in field_data.items()}


def postprocess_adj(
    sim_data_adj: td.SimulationData,
    sim_data_orig: td.SimulationData,
    sim_data_fwd: td.SimulationData,
    sim_fields_keys: list[tuple],
) -> AutogradFieldMap:
    """Postprocess some data from the adjoint simulation into the VJP for the original sim flds."""

    # map of index into 'structures' to the list of paths we need vjps for
    sim_vjp_map = defaultdict(list)
    for _, structure_index, *structure_path in sim_fields_keys:
        structure_path = tuple(structure_path)
        sim_vjp_map[structure_index].append(structure_path)

    # store the derivative values given the forward and adjoint data
    sim_fields_vjp = {}
    for structure_index, structure_paths in sim_vjp_map.items():
        # grab the forward and adjoint data
        fld_fwd = sim_data_fwd._get_adjoint_data(structure_index, data_type="fld")
        eps_fwd = sim_data_fwd._get_adjoint_data(structure_index, data_type="eps")
        fld_adj = sim_data_adj._get_adjoint_data(structure_index, data_type="fld")
        eps_adj = sim_data_adj._get_adjoint_data(structure_index, data_type="eps")

        # post normalize the adjoint fields if a single, broadband source
        fwd_flds_adj_normed = {}
        for key, val in fld_adj.field_components.items():
            fwd_flds_adj_normed[key] = val * sim_data_adj.simulation.post_norm

        fld_adj = fld_adj.updated_copy(**fwd_flds_adj_normed)

        # maps of the E_fwd * E_adj and D_fwd * D_adj, each as as td.FieldData & 'Ex', 'Ey', 'Ez'
        der_maps = get_derivative_maps(
            fld_fwd=fld_fwd,
            eps_fwd=eps_fwd,
            fld_adj=fld_adj,
            eps_adj=eps_adj,
        )
        E_der_map = der_maps["E"]
        D_der_map = der_maps["D"]
        H_der_map = der_maps["H"]

        H_info_exists = H_der_map is not None

        D_fwd = E_to_D(fld_fwd, eps_fwd)
        D_adj = E_to_D(fld_adj, eps_fwd)

        # compute the derivatives for this structure
        structure = sim_data_fwd.simulation.structures[structure_index]

        # compute epsilon arrays for all frequencies
        adjoint_frequencies = np.array(fld_adj.monitor.freqs)

        eps_in = _compute_eps_array(structure.medium, adjoint_frequencies)
        eps_out = _compute_eps_array(sim_data_orig.simulation.medium, adjoint_frequencies)

        # handle background medium if present
        if structure.background_medium:
            eps_background = _compute_eps_array(structure.background_medium, adjoint_frequencies)
        else:
            eps_background = None

        # auto permittivity detection for non-box geometries
        if not isinstance(structure.geometry, td.Box):
            sim_orig = sim_data_orig.simulation
            plane_eps = eps_fwd.monitor.geometry

            sim_orig_grid_spec = GridSpec.from_grid(sim_orig.grid)

            # permittivity without this structure
            structs_no_struct = list(sim_orig.structures)
            structs_no_struct.pop(structure_index)
            sim_no_structure = sim_orig.updated_copy(
                structures=structs_no_struct, monitors=[], sources=[], grid_spec=sim_orig_grid_spec
            )

            eps_no_structure_data = [
                sim_no_structure.epsilon(box=plane_eps, coord_key="centers", freq=f)
                for f in adjoint_frequencies
            ]

            eps_no_structure = xr.concat(eps_no_structure_data, dim="f").assign_coords(
                f=adjoint_frequencies
            )

            if structure.medium.is_pec:
                eps_inf_structure = None
            else:
                # permittivity with infinite structure
                structs_inf_struct = list(sim_orig.structures)[structure_index + 1 :]
                sim_inf_structure = sim_orig.updated_copy(
                    structures=structs_inf_struct,
                    medium=structure.medium,
                    monitors=[],
                    sources=[],
                    grid_spec=sim_orig_grid_spec,
                )

                eps_inf_structure_data = [
                    sim_inf_structure.epsilon(box=plane_eps, coord_key="centers", freq=f)
                    for f in adjoint_frequencies
                ]

                eps_inf_structure = xr.concat(eps_inf_structure_data, dim="f").assign_coords(
                    f=adjoint_frequencies
                )
        else:
            eps_no_structure = eps_inf_structure = None

        # compute bounds intersection
        struct_bounds = rmin_struct, rmax_struct = structure.geometry.bounds
        rmin_sim, rmax_sim = sim_data_orig.simulation.bounds
        rmin_intersect = tuple([max(a, b) for a, b in zip(rmin_sim, rmin_struct)])
        rmax_intersect = tuple([min(a, b) for a, b in zip(rmax_sim, rmax_struct)])
        bounds_intersect = (rmin_intersect, rmax_intersect)

        # get chunk size - if None, process all frequencies as one chunk
        freq_chunk_size = ADJOINT_FREQ_CHUNK_SIZE
        n_freqs = len(adjoint_frequencies)
        if freq_chunk_size is None:
            freq_chunk_size = n_freqs

        # process in chunks
        vjp_value_map = {}

        for chunk_start in range(0, n_freqs, freq_chunk_size):
            chunk_end = min(chunk_start + freq_chunk_size, n_freqs)
            freq_slice = slice(chunk_start, chunk_end)

            select_adjoint_freqs = adjoint_frequencies[freq_slice]

            # slice field data for current chunk
            E_der_map_chunk = _slice_field_data(E_der_map.field_components, select_adjoint_freqs)
            D_der_map_chunk = _slice_field_data(D_der_map.field_components, select_adjoint_freqs)
            E_fwd_chunk = _slice_field_data(
                fld_fwd.field_components, select_adjoint_freqs, component_indicator="E"
            )
            E_adj_chunk = _slice_field_data(
                fld_adj.field_components, select_adjoint_freqs, component_indicator="E"
            )
            D_fwd_chunk = _slice_field_data(D_fwd.field_components, select_adjoint_freqs)
            D_adj_chunk = _slice_field_data(D_adj.field_components, select_adjoint_freqs)
            eps_data_chunk = _slice_field_data(eps_fwd.field_components, select_adjoint_freqs)

            H_der_map_chunk = None
            H_fwd_chunk = None
            H_adj_chunk = None

            if H_info_exists:
                H_der_map_chunk = _slice_field_data(
                    H_der_map.field_components, select_adjoint_freqs
                )
                H_fwd_chunk = _slice_field_data(
                    fld_fwd.field_components, select_adjoint_freqs, component_indicator="H"
                )
                H_adj_chunk = _slice_field_data(
                    fld_adj.field_components, select_adjoint_freqs, component_indicator="H"
                )

            # slice epsilon arrays
            eps_in_chunk = eps_in.sel(f=select_adjoint_freqs)
            eps_out_chunk = eps_out.sel(f=select_adjoint_freqs)
            eps_background_chunk = (
                eps_background.sel(f=select_adjoint_freqs) if eps_background is not None else None
            )
            eps_no_structure_chunk = (
                eps_no_structure.sel(f=select_adjoint_freqs)
                if eps_no_structure is not None
                else None
            )
            eps_inf_structure_chunk = (
                eps_inf_structure.sel(f=select_adjoint_freqs)
                if eps_inf_structure is not None
                else None
            )

            # create derivative info with sliced data
            derivative_info = DerivativeInfo(
                paths=structure_paths,
                E_der_map=E_der_map_chunk,
                D_der_map=D_der_map_chunk,
                H_der_map=H_der_map_chunk,
                E_fwd=E_fwd_chunk,
                E_adj=E_adj_chunk,
                D_fwd=D_fwd_chunk,
                D_adj=D_adj_chunk,
                H_fwd=H_fwd_chunk,
                H_adj=H_adj_chunk,
                eps_data=eps_data_chunk,
                eps_in=eps_in_chunk,
                eps_out=eps_out_chunk,
                eps_background=eps_background_chunk,
                frequencies=select_adjoint_freqs,  # only chunk frequencies
                eps_no_structure=eps_no_structure_chunk,
                eps_inf_structure=eps_inf_structure_chunk,
                bounds=struct_bounds,
                bounds_intersect=bounds_intersect,
                simulation_bounds=sim_data_orig.simulation.bounds,
                is_medium_pec=structure.medium.is_pec,
            )

            # compute derivatives for chunk
            vjp_chunk = structure._compute_derivatives(derivative_info)

            # accumulate results
            for path, value in vjp_chunk.items():
                if path in vjp_value_map:
                    val = vjp_value_map[path]
                    if isinstance(val, (list, tuple)) and isinstance(value, (list, tuple)):
                        vjp_value_map[path] = type(val)(x + y for x, y in zip(val, value))
                    else:
                        vjp_value_map[path] += value
                else:
                    vjp_value_map[path] = value

        # store vjps in output map
        for structure_path, vjp_value in vjp_value_map.items():
            sim_path = ("structures", structure_index, *list(structure_path))
            sim_fields_vjp[sim_path] = vjp_value

    return sim_fields_vjp


""" Register primitives and VJP makers used by the user-facing functions."""

defvjp(_run_primitive, _run_bwd, argnums=[0])
defvjp(_run_async_primitive, _run_async_bwd, argnums=[0])


""" The fundamental Tidy3D run and run_async functions used above. """


def parse_run_kwargs(**run_kwargs):
    """Parse the ``run_kwargs`` to extract what should be passed to the ``Job`` initialization."""
    job_fields = [*list(Job._upload_fields), "solver_version", "pay_type"]
    job_init_kwargs = {k: v for k, v in run_kwargs.items() if k in job_fields}
    return job_init_kwargs


def _run_tidy3d(
    simulation: td.Simulation, task_name: str, **run_kwargs
) -> tuple[td.SimulationData, str]:
    """Run a simulation without any tracers using regular web.run()."""

    job_init_kwargs = parse_run_kwargs(**run_kwargs)
    job = Job(simulation=simulation, task_name=task_name, **job_init_kwargs)
    td.log.info(f"running {job.simulation_type} simulation with '_run_tidy3d()'")
    if job.simulation_type == "autograd_fwd":
        verbose = run_kwargs.get("verbose", False)
        upload_sim_fields_keys(run_kwargs["sim_fields_keys"], task_id=job.task_id, verbose=verbose)
    path = run_kwargs.get("path", DEFAULT_DATA_PATH)
    priority = run_kwargs.get("priority")
    if task_name.endswith("_adjoint"):
        path_parts = basename(path).split(".")
        path = join(dirname(path), path_parts[0] + "_adjoint." + ".".join(path_parts[1:]))
    data = job.run(path, priority=priority)
    return data, job.task_id


def _run_async_tidy3d(
    simulations: dict[str, td.Simulation], **run_kwargs
) -> tuple[BatchData, dict[str, str]]:
    """Run a batch of simulations using regular web.run()."""

    batch_init_kwargs = parse_run_kwargs(**run_kwargs)
    path_dir = run_kwargs.pop("path_dir", None)
    priority = run_kwargs.get("priority")
    batch = Batch(simulations=simulations, **batch_init_kwargs)
    td.log.info(f"running {batch.simulation_type} batch with '_run_async_tidy3d()'")

    if batch.simulation_type == "autograd_fwd":
        verbose = run_kwargs.get("verbose", False)
        # Need to upload to get the task_ids
        sims = {
            task_name: sim.updated_copy(simulation_type="autograd_fwd", deep=False)
            for task_name, sim in batch.simulations.items()
        }
        batch = batch.updated_copy(simulations=sims)

        batch.upload()
        task_ids = {key: job.task_id for key, job in batch.jobs.items()}
        for task_name, sim_fields_keys in run_kwargs["sim_fields_keys_dict"].items():
            task_id = task_ids[task_name]
            upload_sim_fields_keys(sim_fields_keys, task_id=task_id, verbose=verbose)

    if path_dir:
        batch_data = batch.run(path_dir, priority=priority)
    else:
        batch_data = batch.run(priority=priority)

    task_ids = {key: job.task_id for key, job in batch.jobs.items()}
    return batch_data, task_ids


def _run_async_tidy3d_bwd(
    simulations: dict[str, td.Simulation],
    **run_kwargs,
) -> dict[str, AutogradFieldMap]:
    """Run a batch of adjoint simulations using regular web.run()."""

    batch_init_kwargs = parse_run_kwargs(**run_kwargs)
    _ = run_kwargs.pop("path_dir", None)
    batch = Batch(simulations=simulations, **batch_init_kwargs)
    td.log.info(f"running {batch.simulation_type} batch with '_run_async_tidy3d_bwd()'")

    priority = run_kwargs.get("priority")
    batch.start(priority=priority)
    batch.monitor()

    vjp_traced_fields_dict = {}
    for task_name, job in batch.jobs.items():
        task_id = job.task_id
        vjp = get_vjp_traced_fields(task_id_adj=task_id, verbose=batch.verbose)
        vjp_traced_fields_dict[task_name] = vjp

    return vjp_traced_fields_dict
