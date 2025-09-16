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


from kqcircuits.pya_resolver import pya

DPoint = pya.DPoint


class Port:
    """Base data structure for simulation ports.

    Depending on your simulation type, these produce excitations, set potentials, or act as ideal RLC lumped elements.
    """

    def __init__(
        self,
        number: int,
        resistance: float = 50,
        reactance: float = 0,
        inductance: float = 0,
        capacitance: float = 0,
        face: int = 0,
        junction: bool = False,
        renormalization: float = 50,
    ):
        """
        Args:
            number: Port number.
            resistance: Real part of impedance. Given in Ohms (:math:`\\Omega`).
            reactance: Imaginary part of impedance. Given in Ohms (:math:`\\Omega`).
            inductance: Inductance of the element. Given in Henrys (:math:`\\text{H}`).
            capacitance: Capacitance of the element. Given in Farads (:math:`\\text{F}`).
            face: Integer-valued face index for the port.
            junction: Whether this port models a SQUID/Junction. Used in EPR calculations.
            renormalization: Port renormalization in Ohms or None to not re-normalize the port.
        """
        self.number = number
        self.resistance = resistance
        self.reactance = reactance
        self.inductance = inductance
        self.capacitance = capacitance
        self.face = face
        self.junction = junction
        self.renormalization = renormalization
        self.type = type(self).__name__

    def as_dict(self):
        """Returns attributes as a dictionary."""
        return vars(self)


class InternalPort(Port):
    """Data structure for ports inside the simulation area."""

    def __init__(
        self,
        number: int,
        signal_location: DPoint,
        ground_location: DPoint = None,
        resistance: float = 50,
        reactance: float = 0,
        inductance: float = 0,
        capacitance: float = 0,
        face: int = 0,
        junction: bool = False,
        etch_width: float = None,
        floating: bool = False,
    ):
        """
        Args:
            number: Port number.
            signal_location: Edge location for signal source.
            ground_location: Edge location to connect signal to. Usually ground.
            resistance: Real part of impedance. Given in Ohms (:math:`\\Omega`).
            reactance: Imaginary part of impedance. Given in Ohms (:math:`\\Omega`).
            inductance: Inductance of the element. Given in Henrys (:math:`\\text{H}`).
            capacitance: Capacitance of the element. Given in Farads (:math:`\\text{F}`).
            face: Integer-valued face index for the port.
            junction: Whether this port models a SQUID/Junction. Used in EPR calculations.
            etch_width: Width of a trace between signal_location and ground_location, on which the metal is etched away.
                Useful when adding a lumped port on a waveguide.
            floating: activate floating port -> does not force "ground side" to ground.
        """
        super().__init__(number, resistance, reactance, inductance, capacitance, face, junction)
        self.signal_location = signal_location
        if ground_location is not None:
            self.ground_location = ground_location
        if etch_width is not None:
            self.etch_width = etch_width
        self.floating = floating

    def get_etch_polygon(self):
        """Returns polygon under which the metal should be etched away"""
        try:
            d = self.signal_location - self.ground_location
            v = (0.5 * self.etch_width / d.length()) * pya.DVector(-d.y, d.x)
            return pya.DPolygon(
                [self.signal_location - v, self.signal_location + v, self.ground_location + v, self.ground_location - v]
            )
        except AttributeError:
            return pya.DPolygon()


class EdgePort(Port):
    """Data structure for ports at the edge of the simulation area."""

    def __init__(
        self,
        number: int,
        signal_location: DPoint,
        resistance: float = 50,
        reactance: float = 0,
        inductance: float = 0,
        capacitance: float = 0,
        deembed_len: float = None,
        face: int = 0,
        junction: bool = False,
        size=None,
        deembed_cross_section: str = None,
    ):
        """
        Args:
            number: Port number.
            signal_location: Edge location for signal source.
            resistance: Real part of impedance. Given in Ohms (:math:`\\Omega`).
            reactance: Imaginary part of impedance. Given in Ohms (:math:`\\Omega`).
            inductance: Inductance of the element. Given in Henrys (:math:`\\text{H}`).
            capacitance: Capacitance of the element. Given in Farads (:math:`\\text{F}`).
            deembed_len: Port de-embedding length. Given in simulation units, usually microns (:math:`\\text{um}`).
            face: Integer-valued face index for the port.
            junction: Whether this port models a SQUID/Junction. Used in EPR calculations.
            size: Width and height of the port to override Simulation.port_size. Optionally, the size can be set as a
                list specifying the extensions from the center of the port to left, right, down and up, respectively.
            deembed_cross_section: name of the port described by a cross-section
        """
        super().__init__(number, resistance, reactance, inductance, capacitance, face, junction)
        self.signal_location = signal_location
        self.deembed_len = deembed_len
        self.size = size
        self.deembed_cross_section = deembed_cross_section
