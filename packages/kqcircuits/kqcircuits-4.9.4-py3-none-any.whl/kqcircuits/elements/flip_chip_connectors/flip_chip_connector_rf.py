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


import logging

from kqcircuits.elements.element import Element
from kqcircuits.elements.finger_capacitor_square import FingerCapacitorSquare, eval_a2, eval_b2
from kqcircuits.elements.flip_chip_connectors.flip_chip_connector import FlipChipConnector
from kqcircuits.elements.launcher import Launcher
from kqcircuits.pya_resolver import pya
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.util.refpoints import WaveguideToSimPort


@add_parameters_from(FingerCapacitorSquare, "a2", "b2")
@add_parameters_from(FlipChipConnector, bump_type="Flip Chip Connector Dc")
class FlipChipConnectorRf(Element):
    """PCell declaration for an inter-chip rf connector.

    Flip chip connector with two coplanar waveguide connections and different ground bump configurations.
    The input port is on the first face and on the left. The output port is on the second face and rotated as chosen.

    .. MARKERS_FOR_PNG 0,0 15,0 0,-40 -28,0
    """

    inter_bump_distance = Param(pdt.TypeDouble, "Distance between In bumps", 100, unit="μm")
    output_rotation = Param(pdt.TypeDouble, "Rotation of output port w.r.t. input port", 180, unit="degrees")
    connector_a = Param(pdt.TypeDouble, "Conductor width at the connector area", 40, unit="μm")
    connector_b = Param(pdt.TypeDouble, "Gap width at the connector area", 40, unit="μm")
    round_connector = Param(pdt.TypeBoolean, "Use round connector shape", False)
    n_center_bumps = Param(pdt.TypeInt, "Number of center bumps in series", 1)

    def build(self):

        # Flip-chip bump
        bump = self._get_bump()
        for i in range(self.n_center_bumps):
            self.insert_cell(bump, pya.DTrans((i - (self.n_center_bumps - 1) / 2) * self.inter_bump_distance, 0))
        bump_ref = self.get_refpoints(bump)
        logging.debug("bump_ref: %s", bump_ref)

        if self.round_connector:
            # Rounded geometry
            def rounded_plate(center_x, width, length):
                reg = pya.Region(
                    pya.DBox(center_x - length / 2, -width / 2, center_x + length / 2, width / 2).to_itype(
                        self.layout.dbu
                    )
                )
                return reg.rounded_corners(0, min(width, length) / (2 * self.layout.dbu), self.n)

            def trace(start_x, width, length):
                return pya.Region(pya.DBox(start_x, -width / 2, start_x + length, width / 2).to_itype(self.layout.dbu))

            w = self.connector_a + 2 * self.connector_b
            bumps_length = (self.n_center_bumps - 1) * self.inter_bump_distance
            length = w + bumps_length

            def produce_shape(face, a, b, rotation, trace_rotation):
                # Base metal gap outline
                trace_dtrans = pya.DCplxTrans(1, trace_rotation, False, -bumps_length / 2, 0)
                trace_itrans = trace_dtrans.to_itrans(self.layout.dbu)
                region = rounded_plate(0, w, length) + trace(0, a + 2 * b, -w / 2).transformed(trace_itrans)

                # Ground grid avoidance
                avoid_region = region.sized(self.margin / self.layout.dbu, self.margin / self.layout.dbu, 2)

                # Subtract circles under bumps
                for i in range(self.n_center_bumps):
                    region -= rounded_plate(
                        (i - (self.n_center_bumps - 1) / 2) * self.inter_bump_distance,
                        self.connector_a,
                        self.connector_a,
                    )

                # Subtract input trace with possible rotation
                region -= trace(0, a, -w / 2).transformed(trace_itrans)

                # Subtract trace connecting the series bumps
                region -= trace(-bumps_length / 2, a, bumps_length)

                dtrans = pya.DCplxTrans(1, rotation, False, 0, 0)
                itrans = dtrans.to_itrans(self.layout.dbu)
                self.cell.shapes(self.get_layer("base_metal_gap_wo_grid", face)).insert(region.transformed(itrans))
                self.add_protection(avoid_region.transformed(itrans), face)
                self.add_port(
                    f"{self.face_ids[face]}_port",
                    dtrans * pya.DPoint(-bumps_length / 2, 0) + trace_dtrans * dtrans * pya.DVector(-w / 2, 0),
                    trace_dtrans * dtrans * pya.DVector(-1, 0),
                    face,
                )

            produce_shape(0, self.a, self.b, 0, 0)
            produce_shape(1, eval_a2(self), eval_b2(self), 180, self.output_rotation - 180)

        else:
            # Taper geometry
            s = self.connector_a + (self.n_center_bumps - 1) * self.inter_bump_distance
            trans = pya.DCplxTrans(1, 0, False, bump_ref["base"] + pya.DPoint(-self.connector_a - s / 2, 0))
            tt = pya.DCplxTrans(1, self.output_rotation, False, 0, 0)
            self.insert_cell(
                Launcher,
                trans,
                self.face_ids[0],
                s=s,
                l=self.connector_a,
                a_launcher=self.connector_a,
                b_launcher=self.connector_b,
                launcher_frame_gap=self.connector_b,
            )

            # If there are many center bumps and output direction is not colinear with the input direction than a simple
            # Launcher won't do. For arbitrary angles we use two Launcher objects one to cover the parallel part, like
            # in the colinear case, but without the tapering part and we add a second short Launcher rotated to the
            # right output direction. Additionally, we use the metal addition layer to get rid of the parts where one
            # Launcher's gap overlaps with the others center conductor.
            add_metal = False
            if int(self.output_rotation) not in (0, 180) and self.n_center_bumps > 1:
                ubm = self.connector_a
                ibm = self.inter_bump_distance
                l = (self.n_center_bumps - 1) * ibm / 2
                pts = [
                    pya.DPoint(l - ibm, ubm / 2),
                    pya.DPoint(l, ubm / 2),
                    pya.DPoint(l, -ubm / 2),
                    pya.DPoint(l - ibm, -ubm / 2),
                ]
                self.cell.shapes(self.get_layer("base_metal_addition", self.face_ids[1])).insert(pya.DPolygon(pts))

                lc = ubm * 1.5
                ts = pya.DCplxTrans(1, 180, False, -lc, 0)
                self.insert_cell(
                    Launcher,
                    ts * trans,
                    None,
                    s=s - lc,
                    l=ubm,
                    a_launcher=self.connector_a,
                    b_launcher=self.connector_b,
                    launcher_frame_gap=self.connector_b,
                    face_ids=[self.face_ids[1], self.face_ids[0]],
                    a=ubm,
                    b=ubm,
                )
                s = ubm
                trans = pya.DCplxTrans(1, 0, False, bump_ref["base"] + pya.DPoint(-ubm - s / 2, 0))
                tt = pya.DCplxTrans(1, self.output_rotation, False, (self.n_center_bumps - 1) / 2 * ibm, 0)
                add_metal = True

            self.insert_cell(
                Launcher,
                tt * trans,
                self.face_ids[1],
                s=s,
                l=self.connector_a,
                a_launcher=self.connector_a,
                b_launcher=self.connector_b,
                launcher_frame_gap=self.connector_b,
                face_ids=[self.face_ids[1], self.face_ids[0]],
                a=eval_a2(self),
                b=eval_b2(self),
                add_metal=add_metal,
            )

        self._insert_ground_bumps(bump)
        for face_id in self.face_ids[:2]:
            self.refpoints[f"{face_id}_signal_bump"] = pya.DPoint(0, 0)

    def _insert_ground_bumps(self, bump):
        # Insert ground bumps
        dist_y = 0.5**0.5 * self.inter_bump_distance
        dist_x = dist_y + self.inter_bump_distance * (self.n_center_bumps - 1) / 2
        self.insert_cell(bump, pya.DCplxTrans(1, 0, False, dist_x, dist_y))
        self.insert_cell(bump, pya.DCplxTrans(1, 0, False, -dist_x, dist_y))
        self.insert_cell(bump, pya.DCplxTrans(1, 0, False, dist_x, -dist_y))
        self.insert_cell(bump, pya.DCplxTrans(1, 0, False, -dist_x, -dist_y))

    def _get_bump(self):
        return self.add_element(FlipChipConnector, face_ids=self.face_ids, bump_type=self.bump_type)

    @classmethod
    def get_sim_ports(cls, simulation):
        """An implementation of get_sim_ports that adds waveguides on both sides of a face-changing element.
        The port names are '{face_ids[0]}_port' and '{face_ids[1]}_port'.
        The first port points to left and the second port orientation is determined by output_rotation parameter.
        The a and b values of the second waveguide are adjusted by a2 and b2 parameters.
        """

        def diff_to_rotation(x):
            return abs(x - (simulation.output_rotation % 360))

        side = {0: "left", 90: "bottom", 180: "right", 270: "top", 360: "left"}.get(
            min([0, 90, 180, 270, 360], key=diff_to_rotation)
        )
        return [
            WaveguideToSimPort(f"{simulation.face_ids[0]}_port", side="left"),
            WaveguideToSimPort(
                f"{simulation.face_ids[1]}_port", side=side, face=1, a=eval_a2(simulation), b=eval_b2(simulation)
            ),
        ]
