# This code is part of KQCircuits
# Copyright (C) 2021 IQM Finland Oy
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see
# https://www.gnu.org/licenses/gpl-3.0.html.
#
# The software distribution should follow IQM trademark policy for open-source software
# (meetiqm.com/iqm-open-source-trademark-policy). IQM welcomes contributions to the code.
# Please see our contribution agreements for individuals (meetiqm.com/iqm-individual-contributor-license-agreement)
# and organizations (meetiqm.com/iqm-organization-contributor-license-agreement).

from sys import float_info
import textwrap

from kqcircuits.defaults import default_layers
from kqcircuits.elements.chip_frame import ChipFrame
from kqcircuits.elements.element import Element, get_refpoints, insert_cell_into
from kqcircuits.elements.waveguide_coplanar import WaveguideCoplanar
from kqcircuits.elements.waveguide_composite import WaveguideComposite, Node
from kqcircuits.util.parameters import pdt
from kqcircuits.pya_resolver import pya


def convert_cells_to_code(
    top_cell,
    print_waveguides_as_composite=False,
    add_instance_names=True,
    refpoint_snap=50.0,
    grid_snap=1.0,
    output_format="chip",
    include_imports=True,
    create_code=True,
):
    """Prints out the Python code required to create the cells in top_cell.

    For each instance that is selected in GUI, prints out an `insert_cell()` command that can be copy pasted to a chip's
    `build()`. If no instances are selected, then it will do the same for all instances that are one level below
    the chip cell in the cell hierarchy. PCell parameters are taken into account. Waveguide points can automatically be
    snapped to closest refpoints in the generated code.

    Args:
        top_cell: cell whose child cells will be printed as code
        print_waveguides_as_composite: If true, then WaveguideCoplanar elements are printed as WaveguideComposite.
        add_instance_names: If true, then unique instance names will be added for each printed element. This is required
            if you want to have waveguides connect to refpoints of elements that were placed in GUI.
        refpoint_snap: If a waveguide point is closer than `refpoint_snap` to a refpoint, the waveguide point will be
            at that refpoint.
        grid_snap: If a waveguide point was not close enough to a refpoint, it will be snapped to a square grid with
            square side length equal to `grid_snap`
        output_format: Determines the format of the code for placing cells. Has the following options:

            * "build": Creates code that can be used inside the ``build`` method of a ``Chip`` or ``Element``
            * "chip": Same as the above, but also outputs a full ``Chip`` class definition
            * "macro": Creates code that can be used in a stand-alone KLayout macro or python script

        include_imports: If true, then import statements for all used elements are included in the generated code
        create_code: if False then does not export code but snap cells to refpoints in place

    Returns:
        str: The generated Python code. This is also printed.
    """

    if output_format in ["build", "chip"]:
        parent_object = "self"
        element_context = True
    elif output_format == "macro":
        parent_object = "view"
        element_context = False
    else:
        raise ValueError(f"Unknown output format: {output_format}")
    layout = top_cell.layout()

    instances = []
    inst_names = []
    pcell_classes = set()

    # If some instances are selected, then we are only going to export code for them
    cell_view = pya.CellView.active() if hasattr(pya, "CellView") else None
    if cell_view and cell_view.is_valid() and len(cell_view.view().object_selection) > 0:
        for obj in cell_view.view().object_selection:
            if obj.is_cell_inst():
                _add_instance(obj.inst(), instances, inst_names, pcell_classes)
    # Otherwise get all instances at one level below top_cell.
    else:
        for inst in top_cell.each_inst():
            _add_instance(inst, instances, inst_names, pcell_classes)

    def sort_order(inst):
        """Move waveguide instances to the end without reordering, and sort all other elements by name and position."""
        if isinstance(inst.pcell_declaration(), (WaveguideComposite, WaveguideCoplanar)):
            return (1,)
        else:
            return 0, inst.cell.name, -inst.dtrans.disp.y, inst.dtrans.disp.x

    instances = sorted(instances, key=sort_order)
    pcell_classes = sorted(pcell_classes, key=lambda pcell_class: pcell_class.__module__)

    # Add names to placed instances and create chip-level refpoints with those names
    if add_instance_names:
        for inst in instances:
            if inst.property("id") is None:
                inst_name = _get_unique_inst_name(inst, inst_names)
                inst_names.append(inst_name)
                inst.set_property("id", inst_name)
                inst_refpoints = get_refpoints(
                    layout.layer(default_layers["refpoints"]), inst.cell, inst.dcplx_trans, 0
                )
                for name, refpoint in inst_refpoints.items():
                    text = pya.DText(f"{inst_name}_{name}", refpoint.x, refpoint.y)
                    top_cell.shapes(layout.layer(default_layers["refpoints"])).insert(text)

    # Get refpoints used for snapping waveguide points
    refpoints = get_refpoints(layout.layer(default_layers["refpoints"]), top_cell)
    # only use refpoints of named instances
    prefixes_to_filter = tuple(name + "_" for name in inst_names)
    refpoints = {name: point for name, point in refpoints.items() if name.startswith(prefixes_to_filter)}

    # Generate code for importing the used element. More element imports may be added later when generating code from
    # waveguide nodes.
    element_imports = ""
    if include_imports:
        for pcell_class in pcell_classes:
            element_imports += f"from {pcell_class.__module__} import {pcell_class.__name__}\n"
        if print_waveguides_as_composite or WaveguideComposite in pcell_classes:
            element_imports += f"from {WaveguideComposite.__module__} import {Node.__name__}\n"

    def format_element_code(pcell_type, inst_name, transform_string, parameter_string):
        var_name = inst_name.replace("-", "_")
        args = [pcell_type]
        if transform_string:
            args.append(transform_string)
        if inst_name:
            args.append(f'inst_name="{inst_name}"')
        args.append(parameter_string)
        arg_string = ", ".join(args)
        if element_context or var_name == "":
            return f"{parent_object}.insert_cell({arg_string})\n"
        else:
            return f"{var_name}, {var_name}_refpoints = {parent_object}.insert_cell({arg_string})\n"

    def get_waveguide_code(inst, pcell_type, instance_names_defined_so_far):
        point_prefix = "pya.DPoint"
        point_postfix = ""
        refpoint_prefix = ""
        refpoint_postfix = ""
        path_str = "path=pya.DPath(["
        postfix = "], 0)"
        if pcell_type == "WaveguideComposite":
            point_prefix = "Node("
            point_postfix = ")"
            refpoint_prefix = "Node("
            refpoint_postfix = ")"
            path_str = "nodes=["
            postfix = "]"

        wg_points = []
        nodes = None
        _params = inst.pcell_parameters_by_name()
        if type(inst.pcell_declaration()).__name__ == "WaveguideCoplanar":
            wg_points = _params.pop("path").each_point()
        else:
            nodes = Node.nodes_from_string(_params.pop("nodes"))
            for node in nodes:
                wg_points.append(node.position)

        wg_params = ""  # non-default parameters of the cell
        for k, v in inst.pcell_declaration().get_schema().items():
            if k in _params and v.data_type not in [pdt.TypeShape, pdt.TypeLayer] and _params[k] != v.default:
                wg_params += f",  {k}={_params[k]}"

        for i, path_point in enumerate(wg_points):
            path_point += inst.dtrans.disp
            x_snapped = grid_snap * round(path_point.x / grid_snap)
            y_snapped = grid_snap * round(path_point.y / grid_snap)
            node_params = ""
            if nodes is not None:
                node_params, node_elem = get_node_params(nodes[i])
                if node_elem is not None and include_imports:
                    nonlocal element_imports
                    node_elem_import = f"from {node_elem.__module__} import {node_elem.__name__}\n"
                    if node_elem_import not in element_imports:
                        element_imports += node_elem_import

            # If a refpoint is close to the path point, snap the path point to it
            closest_refpoint_name = _get_closest_refpoint(
                refpoints, path_point, refpoint_snap, instance_names_defined_so_far
            )
            if closest_refpoint_name is not None:
                if element_context:
                    path_str += (
                        f'{refpoint_prefix}{parent_object}.refpoints["{closest_refpoint_name}"]{node_params}'
                        f"{refpoint_postfix}, "
                    )
                else:
                    refp_split = closest_refpoint_name.split("_")
                    refp_name = "_".join(refp_split[1:])
                    path_str += (
                        f"{refpoint_prefix}{refp_split[0].replace('-', '_')}_refpoints[\"{refp_name}\"]"
                        f"{node_params}{refpoint_postfix}, "
                    )
            else:
                path_str += f"{point_prefix}({x_snapped}, {y_snapped}){node_params}{point_postfix}, "
        path_str = path_str[:-2]  # Remove extra comma and space
        path_str += postfix + wg_params

        inst_name = inst.property("id") if (inst.property("id") is not None) else ""
        return format_element_code(pcell_type, inst_name, "", path_str)

    # Generate the code for creating each instance
    instances_code = ""
    instance_names_so_far = set()
    for inst in instances:
        pcell_declaration = inst.pcell_declaration()
        pcell_type = type(pcell_declaration).__name__
        cell = _get_cell(inst)

        if isinstance(pcell_declaration, (WaveguideComposite, WaveguideCoplanar)):
            output_pcell_type = "WaveguideComposite" if print_waveguides_as_composite else pcell_type
            if create_code:
                instances_code += get_waveguide_code(inst, output_pcell_type, instance_names_so_far)
            else:
                _snap_waveguide_to_refpoints(inst, refpoints, refpoint_snap, grid_snap, instance_names_so_far)
        else:
            inst_name = inst.property("id") if (inst.property("id") is not None) else ""
            instances_code += format_element_code(
                pcell_type, inst_name, _transform_as_string(inst), _pcell_params_as_string(cell)
            )

        if inst.property("id") is not None:
            instance_names_so_far.add(inst.property("id"))

    if not create_code:
        return ""

    # Generate code for the beginning of the chip or macro file if needed
    if output_format == "chip":
        return (
            "from kqcircuits.pya_resolver import pya\n"
            "from kqcircuits.chips.chip import Chip\n\n" + element_imports + "\n"
            "class NewChip(Chip):\n\n"
            "    def build(self):\n" + textwrap.indent(instances_code, "        ") + "\n"
        )
    elif output_format == "macro":
        return (
            "from kqcircuits.pya_resolver import pya\n"
            "from kqcircuits.klayout_view import KLayoutView\n\n" + element_imports + "\n"
            "view = KLayoutView()\n"
            "layout = view.layout\n\n" + instances_code
        )
    else:
        return element_imports + "\n" + instances_code


def _transform_as_string(inst):
    trans = inst.dcplx_trans
    x, y = trans.disp.x, trans.disp.y
    if trans.mag == 1 and trans.angle % 90 == 0:
        if trans.rot() == 0 and not trans.is_mirror():
            if x == 0 and trans.disp.y == 0:
                return ""
            else:
                return f"pya.DTrans({x}, {y})"
        else:
            return f"pya.DTrans({trans.rot()}, {trans.is_mirror()}, {x}, {y})"
    else:
        return f"pya.DCplxTrans({trans.mag}, {trans.angle}, {trans.is_mirror()}, {x}, {y})"


def _add_instance(inst, instances, inst_names, pcell_classes):
    inst_name = inst.property("id")
    pcell_decl = inst.pcell_declaration()
    # ChipFrame is always constructed by Chip, so we don't want to generate code for it
    if isinstance(pcell_decl, ChipFrame):
        return
    # We exclude PCells that are not KQCircuits elements
    if not isinstance(pcell_decl, Element):
        return
    instances.append(inst)
    if inst_name is not None:
        inst_names.append(inst_name)
    if pcell_decl is not None:
        pcell_classes.add(pcell_decl.__class__)


def _get_cell(inst):
    # workaround for getting the cell due to KLayout bug, see
    # https://www.klayout.de/forum/discussion/1191/cell-shapes-cannot-call-non-const-method-on-a-const-reference
    # TODO: replace by `inst.cell` once KLayout bug is fixed
    return inst.layout().cell(inst.cell_index)


def _get_unique_inst_name(inst, inst_names):
    idx = 1
    inst_name = type(inst.pcell_declaration()).__name__ + str(idx)
    while inst_name in inst_names:
        idx += 1
        inst_name = type(inst.pcell_declaration()).__name__ + str(idx)
    return inst_name


def _pcell_params_as_string(cell):
    params = cell.pcell_parameters_by_name()
    params_schema = type(cell.pcell_declaration()).get_schema()
    params_list = []
    for param_name, param_declaration in params_schema.items():
        if (
            not isinstance(params[param_name], pya.LayerInfo)
            and params[param_name] != param_declaration.default
            and param_name != "refpoints"
            and not param_name.startswith("_")
            and not param_name.endswith("_parameters")
        ):
            param_value = params[param_name]
            if isinstance(param_value, str):
                param_value = repr(param_value)
            if isinstance(param_value, pya.DPoint):
                param_value = f"pya.DPoint({param_value})"
            params_list.append(f"{param_name}={param_value}")
    return ", ".join(params_list)


def get_node_params(node: Node):
    """
    Generate a list of parameters for Node in string form

    Args:
        node: a Node to convert

    Returns: a tuple (node_params, element) where
        node_params: string of comma-separated key-value pairs that can be passed to the initializer of Node,
        starting with ``", "``
        element: class that implements the node's element, or None if the node has no element
    """
    node_params = ""
    elem = None
    for k, v in vars(node).items():
        if k == "element" and v is not None:
            node_params += f", {v.__name__}"
            elem = v
        elif (
            (k == "inst_name" and v is not None)
            or (k == "align" and v != tuple())
            or (k == "angle" and v is not None)
            or (k == "length_before" and v is not None)
            or (k == "length_increment" and v is not None)
            or (k == "meander_direction" and v != 1)
        ):
            node_params += f", {k}={repr(v)}"
        elif k == "params":
            # Expand keyword arguments to Node
            for kk, vv in v.items():
                node_params += f", {kk}={repr(vv)}"
    return node_params, elem


def extract_pcell_data_from_views():
    """Iterate over all KQCircuits PCells and return their data and instances.

    Returns: a tuple (views, instances) where
        views: a list of lists. Each element corresponds to a view in KLayout and it is a list of
        ``(type, location, parameters)`` tuples. These tuples completely describe the type, position
        and parameters of a single PCell in the "Top Cell" of this view.
        instances: flattened list of all instances of KQCircuits PCells found.
    """

    views = []
    instances = []
    main_window = pya.Application.instance().main_window()
    for vid in range(main_window.views()):
        top_cell = main_window.view(vid).active_cellview().cell
        pcells = []
        for inst in top_cell.each_inst():
            pc = inst.pcell_declaration()
            if isinstance(pc, Element):
                instances.append(inst)
                params = inst.pcell_parameters_by_name()
                def_params = pc.__class__.get_schema()
                for k, v in def_params.items():
                    # Attempts to retain _epr_ parameter values caused crashes, so reset them for now.
                    if k in params and (k.startswith("_epr_") or params[k] == v.default):
                        del params[k]
                pcells.append((pc.__class__, inst.dtrans, params))
        views.append(pcells)

    return views, instances


def restore_pcells_to_views(views):
    """Re-populate each view's Top Cell with PCells as extracted by ``extract_pcell_data_from_views``.

    Args:
        views: List of list of ``(type, location, parameters)`` tuples.
    """

    main_window = pya.Application.instance().main_window()
    if main_window.views() != len(views):
        raise ValueError("Number of views in KLayout unexpectedly changed during reload.")

    for vid in range(main_window.views()):
        top_cell = main_window.view(vid).active_cellview().cell
        pcells = views[vid]
        for pc in pcells:
            def_params = {k: v.default for k, v in pc[0].get_schema().items()}
            params = {**def_params, **pc[2]}
            insert_cell_into(top_cell, pc[0], pc[1], **params)
        top_cell.refresh()


def _snap_waveguide_to_refpoints(inst, refpoints, refpoint_snap, grid_snap, instance_names_defined_so_far):
    """Helper function to do only refpoint and grid snapping."""
    wg_points = []
    _params = inst.pcell_parameters_by_name()
    if type(inst.pcell_declaration()).__name__ == "WaveguideCoplanar":
        for p in _params.pop("path").each_point():
            wg_points.append(p)
    else:
        nodes = Node.nodes_from_string(_params.pop("nodes"))
        for node in nodes:
            wg_points.append(node.position)

    new_points = []
    for i, path_point in enumerate(wg_points):
        _point = path_point + inst.dtrans.disp
        x_snapped = grid_snap * round(_point.x / grid_snap)
        y_snapped = grid_snap * round(_point.y / grid_snap)

        closest_refpoint_name = _get_closest_refpoint(
            refpoints, path_point, refpoint_snap, instance_names_defined_so_far
        )
        if closest_refpoint_name is not None:
            new_points.append(refpoints[closest_refpoint_name])
        else:
            new_points.append(pya.DPoint(x_snapped, y_snapped))

    itrans = inst.dtrans.inverted()
    for i, point in enumerate(new_points):
        new_points[i] = point * itrans

    if type(inst.pcell_declaration()).__name__ == "WaveguideCoplanar":
        inst.change_pcell_parameter("path", pya.DPath(new_points, 1))
    else:
        inst.change_pcell_parameter("gui_path", pya.DPath(new_points, 1))


def _get_closest_refpoint(refpoints, path_point, refpoint_snap, allowed_instance_names=None):
    closest_dist = float_info.max
    closest_refpoint_name = None
    for name, point in refpoints.items():
        dist = point.distance(path_point)
        if dist <= closest_dist and dist < refpoint_snap:
            # If this refpoint is at exact same position as closest_refpoint, compare also refpoint names.
            # This should ensure that chip-level refpoints are chosen over lower-level refpoints.
            if dist < closest_dist or (len(name) > len(closest_refpoint_name)):
                if allowed_instance_names is None or name.split("_")[0] in allowed_instance_names:
                    closest_dist = dist
                    closest_refpoint_name = name
    return closest_refpoint_name
