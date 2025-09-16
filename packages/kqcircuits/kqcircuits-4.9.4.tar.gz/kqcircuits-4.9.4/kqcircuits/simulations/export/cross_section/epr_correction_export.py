# This code is part of KQCircuits
# Copyright (C) 2025 IQM Finland Oy
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
from typing import Callable, Sequence

from kqcircuits.simulations.export.cross_section.cross_section_export import (
    visualise_cross_section_cut_on_original_layout,
)
from kqcircuits.simulations.export.cross_section.cut_simulation import CutSimulation

from kqcircuits.simulations.simulation import Simulation

from kqcircuits.simulations.partition_region import get_list_of_two

from kqcircuits.simulations.export.simulation_export import cross_combine

from kqcircuits.simulations.export.elmer.elmer_solution import ElmerCrossSectionSolution

from kqcircuits.pya_resolver import pya
from kqcircuits.simulations.post_process import PostProcess


def get_epr_correction_elmer_solution(**override_args):
    """Returns ElmerCrossSectionSolution for EPR correction simulations with default arguments.
    Optionally, 'override_args' can be used to override any arguments.
    """
    return ElmerCrossSectionSolution(
        **{
            "linear_system_method": "mg",
            "p_element_order": 3,
            "is_axisymmetric": False,
            "mesh_size": {
                "ms_layer_mer&ma_layer_mer": [0.0005, 0.0005, 0.2],
            },
            "integrate_energies": True,
            "run_inductance_sim": False,
            **override_args,
        }
    )


def get_epr_correction_simulations(
    simulations: list[Simulation],
    correction_cuts: dict[str, dict] | Callable[[Simulation], dict[str, dict]],
    ma_eps_r: float = 8,
    ms_eps_r: float = 11.4,
    sa_eps_r: float = 4,
    ma_thickness: float = 4.8e-3,  # in µm
    ms_thickness: float = 0.3e-3,  # in µm
    sa_thickness: float = 2.4e-3,  # in µm
    metal_height: float = 0.2,
) -> tuple[list[tuple[CutSimulation, ElmerCrossSectionSolution]], list[PostProcess]]:
    """Helper function to produce EPR correction simulations.

    Args:
        simulations: list of simulation objects
        correction_cuts: dictionary or function that returns a dictionary of correction cuts for given simulation.
        Key is the name of cut and values are dicts containing:
        - p1: pya.DPoint indicating the first end of the cut segment
        - p2: pya.DPoint indicating the second end of the cut segment
        - metal_edges: list of dictionaries indicating metal-edge-region locations and orientations in 2D simulation.
            Can contain keywords:
            - x: lateral distance from p1 to mer metal edge,
            - x_reversed: whether gap is closer to p1 than metal, default=False
            - z: height of substrate-vacuum interface, default=0
            - z_reversed: whether vacuum is below substrate, default=False
        - partition_regions: (optional) list of partition region names. The correction cut key is used if not assigned.
        - simulations: (optional) list of simulation names. Is applied on all simulations if not assigned.
        - solution: (optional) solution object for the sim. `get_epr_correction_elmer_solution` is used if not assigned.
            If `solution` is not set, all items under `correction_cuts[Key]`
            are given to `get_epr_correction_elmer_solution` except
            items with keys `["p1", "p2", "metal_edges", "partition_regions", "simulations"]`.
        ma_eps_r: relative permittivity of MA layer
        ms_eps_r: relative permittivity of MS layer
        sa_eps_r: relative permittivity of SA layer
        ma_thickness: thickness of MA layer
        ms_thickness: thickness of MS layer
        sa_thickness: thickness of SA layer
        metal_height: Thickness of metal layer if sheet in the source simulation

    Returns:
        tuple containing list of correction simulations and list of post_process objects
    """
    correction_simulations = []
    correction_layout = pya.Layout()
    simulations = [sim if isinstance(sim, Sequence) else (sim, None) for sim in simulations]
    source_sims, source_sols = list(zip(*simulations))

    for source_sim, source_sol in zip(source_sims, source_sols):
        cuts = correction_cuts(source_sim) if callable(correction_cuts) else correction_cuts

        for key, cut in cuts.items():
            if "simulations" in cut and source_sim.name not in cut["simulations"]:
                continue

            part_names = cut.get("partition_regions", [key])
            if not part_names:
                raise ValueError("Correction cut has no partition region attached")

            parts = [p for p in source_sim.get_partition_regions() if p.name in part_names]
            if not parts:
                continue

            v_dims = get_list_of_two(parts[0].vertical_dimensions)
            h_dims = get_list_of_two(parts[0].metal_edge_dimensions)
            if None in v_dims or any(v_dims != get_list_of_two(p.vertical_dimensions) for p in parts):
                raise ValueError(f"Partition region vertical_dimensions are invalid for correction_cut {key}.")
            if None in h_dims or any(h_dims != get_list_of_two(p.metal_edge_dimensions) for p in parts):
                raise ValueError(f"Partition region metal_edge_dimensions are invalid for correction_cut {key}.")

            mer_box = []
            for me in cut.get("metal_edges", []):
                # TODO: replace x, z, x_reversed, z_reversed with face, intersection_n
                # TODO: we can deduce x from intersection data, just need to know which intersection from the left
                # TODO: we can deduce z from face name. z_reversed implicit from face name (t or b)
                x = me.get("x", 0)
                z = me.get("z", 0)
                dx = int(me.get("x_reversed", False))
                dz = int(me.get("z_reversed", False))
                mer_box.append(pya.DBox(x - h_dims[1 - dx], z - v_dims[dz], x + h_dims[dx], z + v_dims[1 - dz]))

            cords_list = [(cut["p1"], cut["p2"])]
            correction_layout.dbu = 1e-4
            cross_section = CutSimulation(
                correction_layout,
                name=source_sim.name + getattr(source_sol, "name", "") + "_" + key,
                source_sim=source_sim,
                cut_start=cut["p1"],
                cut_end=cut["p2"],
                tls_layer_thickness=[ma_thickness, ms_thickness, sa_thickness],
                tls_layer_material=["ma", "ms", "sa"],
                material_dict={
                    "ma": {"permittivity": ma_eps_r},
                    "ms": {"permittivity": ms_eps_r},
                    "sa": {"permittivity": sa_eps_r},
                },
                region_map={"_mer": mer_box or part_names},
                metal_height=metal_height,
            )

            if "solution" in cut:
                cut_solution = cut["solution"]
            else:
                cut_solution = get_epr_correction_elmer_solution(
                    voltage_excitations=getattr(source_sol, "voltage_excitations", None),
                    **{
                        k: v
                        for k, v in cut.items()
                        if k not in ["p1", "p2", "metal_edges", "partition_regions", "simulations"]
                    },
                )

            correction_simulations += cross_combine(cross_section, cut_solution)

            visualise_cross_section_cut_on_original_layout([source_sim], cords_list, cut_label=key, width_ratio=0.03)

    post_process = [
        PostProcess(
            "produce_epr_table.py",
            data_file_prefix="correction",
            sheet_approximations={
                "MA": {"thickness": ma_thickness * 1e-6, "eps_r": ma_eps_r},
                "MS": {"thickness": ms_thickness * 1e-6, "eps_r": ms_eps_r},
                "SA": {"thickness": sa_thickness * 1e-6, "eps_r": sa_eps_r},
            },
            groups=["MA", "MS", "SA", "substrate", "vacuum"],
            region_corrections={
                **{p.name: None for s in source_sims for p in s.get_partition_regions()},
                **{p: k for k, v in cuts.items() for p in v.get("partition_regions", [k])},
            },
        ),
    ]
    return correction_simulations, post_process
