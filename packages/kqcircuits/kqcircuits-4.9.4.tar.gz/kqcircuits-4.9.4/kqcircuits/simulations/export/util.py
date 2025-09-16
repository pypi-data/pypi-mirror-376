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


import math
from typing import List
from kqcircuits.pya_resolver import pya


def _dist(edge: pya.Edge, point: pya.Point):
    """
    If point projected to line by edge is in edge then use `distance_abs`
    but otherwise take the minimum distance to end points
    """
    v_edge = pya.Vector(edge.p2 - edge.p1)
    if v_edge.sprod(v_edge) > 0:
        v_point_start = pya.Vector(point - edge.p1)
        v_point_end = pya.Vector(point - edge.p2)

        v_point_start_projection = v_edge.sprod(v_point_start) / math.sqrt(v_edge.sprod(v_edge))
        v_point_end_projection = v_edge.sprod(v_point_end) / math.sqrt(v_edge.sprod(v_edge))

        if edge.length() >= abs(v_point_start_projection + v_point_end_projection):
            out = edge.distance_abs(point)
        else:
            out = min(point.distance(edge.p1), point.distance(edge.p2))
    else:
        out = min(point.distance(edge.p1), point.distance(edge.p2))
    return out


def find_edge_from_point_in_polygons(polygons: List[pya.Polygon], point: pya.DPoint, dbu, tolerance=0.01):
    """
    Finds the edge closest to a point, and returns the edge as well as it's polygon and edge index
    """

    # Find closest edge to point
    edges = [
        (i, j, edge.to_dtype(dbu))
        for (i, polygon) in enumerate(polygons)
        for (j, edge) in enumerate(polygon.each_edge())
    ]
    (distance, i, j, nearest_edge) = sorted([(_dist(edge, point), i, j, edge) for (i, j, edge) in edges])[0]
    if distance < tolerance:
        return i, j, nearest_edge
    else:
        raise ValueError(f"No edge found at {point=}, {nearest_edge=}, {distance=}")


def get_enclosing_polygon(points: List[List[float]]):
    """
    Order points in such a way that they form a polygon without intersecting
    lines. The ordering is clockwise starting from the left-most point.

    Arguments:
        points: List of points [x,y]

    Returns:
        ordered list of points [x,y]
    """

    # Find y-coordinate of linear interpolation between p0 = [x0,y0] and
    # p1 = [x1,y1] corresponding to x
    def _linearinterpy(p0, p1, x):
        """
        Find y-coordinate of linear interpolation between p0 = [x0,y0] and p1 = [x1,y1] corresponding to x

        Arguments:
            p0, p1: Points [x,y]
            x: x-coordinate to interpolate at

        Returns:
            y = y0 + (x-x0)*(dy/dx)
        """
        return p0[1] + (x - p0[0]) * ((p1[1] - p0[1]) / (p1[0] - p0[0]))

    # Sort by x and then y, to ensure we go from lowest left-most point to
    # highest right-most point.
    points.sort()

    # Leftmost and rightmost point
    pleft = points[0]
    pright = points[-1]

    # Split remaining points into groups above and below
    # the line pleft - pright
    pabove = []
    pbelow = []
    for p in points[1:-1]:
        if p[1] > _linearinterpy(pleft, pright, p[0]):
            pabove.append(p)
        else:
            pbelow.append(p)

    # Construct polygon starting from pleft and going clockwise
    # Note: we rely on the fact that pabove and pbelow are still sorted by x
    # Note: the polygon is not closed.
    pbelow.reverse()
    return [pleft] + pabove + [pright] + pbelow
