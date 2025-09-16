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


"""Helper module for general geometric functions"""

from math import cos, sin, radians, atan2, degrees, pi, ceil
from typing import List
import numpy as np
from scipy import spatial
from kqcircuits.defaults import default_layers, default_path_length_layers
from kqcircuits.pya_resolver import pya


def vector_length_and_direction(vector):
    """Returns the direction and length of the pya.DVector "vector"."""
    length = vector.length()
    direction = vector / length
    return length, direction


def point_shift_along_vector(start, other, distance=None):
    """Returns a point at a `distance` away from point `start` in the direction of point `other`."""
    v = other - start
    if distance is not None:
        return start + v / v.length() * distance
    else:
        return start + v


def get_direction(angle):
    """
    Returns the direction vector corresponding to `angle`.

    Args:
        angle: angle in degrees

    Returns: Unit vector in direction angle
    """
    return pya.DVector(cos(radians(angle)), sin(radians(angle)))


def get_angle(vector):
    """
    Returns the angle in degrees for a given DVector (or DPoint)

    Args:
        vector: input vector

    Returns: angle in degrees
    """
    return degrees(atan2(vector.y, vector.x))


def get_cell_path_length(cell, layer=None):
    """Returns the length of the paths in the cell.

    Adding together the cell's paths' lengths in the given 'layer' or in all layers of 'default_path_length_layers'.

    Args:
        cell: A cell object.
        layer: None or an unsigned int to specify a non-standard layer
    """

    if layer is not None:
        return _get_length_per_layer(cell, layer)

    length = 0
    for path_layer in default_path_length_layers:
        length += _get_length_per_layer(cell, path_layer)

    return length


def _get_length_per_layer(cell, layer):
    """Get length of the paths in the cell in the specified layer."""

    length = 0
    layer = cell.layout().layer(default_layers[layer]) if isinstance(layer, str) else layer

    for inst in cell.each_inst():  # over child cell instances, not instances of itself
        shapes_iter = inst.cell.begin_shapes_rec(layer)
        while not shapes_iter.at_end():
            shape = shapes_iter.shape()
            if shape.is_path():
                length += shape.path_dlength()
            shapes_iter.next()

    # in case of waveguide, there are no shapes in the waveguide cell itself
    # but the following allows function reuse in other applications
    for shape in cell.shapes(layer).each():
        if shape.is_path():
            length += shape.path_dlength()

    return length


def get_object_path_length(obj, layer=None):
    """Returns sum of lengths of all the paths in the object and its children

    Arguments:
        obj: ObjectInstPath object
        layer: layer integer id in the database, waveguide layer by default
    """

    if obj.is_cell_inst():
        # workaround for getting the cell due to KLayout bug, see
        # https://www.klayout.de/forum/discussion/1191/cell-shapes-cannot-call-non-const-method-on-a-const-reference
        # TODO: replace by `cell = obj.inst().cell` once KLayout bug is fixed
        cell = obj.layout().cell(obj.inst().cell_index)
        return get_cell_path_length(cell, layer)
    else:  # is a shape
        # TODO ignore paths on wrong layers
        shape = obj.shape
        if shape.is_path():
            return shape.path_dlength()
    return 0


def simple_region(region):
    return pya.Region([poly.to_simple_polygon() for poly in region.each()])


def region_with_merged_points(region, tolerance):
    """In each polygon of the region, removes points that are closer to other points than a given tolerance.

    Arguments:
        region: Input region
        tolerance: Minimum distance, in database units, between two adjacent points in the resulting region

    Returns:
        region: with merged points
    """

    def find_next(curr, step, data):
        """Returns the next index starting from 'i' to direction 'step' for which 'data' has positive value"""
        num = len(data)
        j = curr + step
        while data[j % num] <= 0.0:
            j += step
        return j

    def merged_points(points):
        """Removes points that are closer another points than a given tolerance. Returns list of points."""
        # find squared length of each segment of polygon
        num = len(points)
        squares = [0.0] * num
        for i in range(0, num):
            squares[i] = points[i].sq_distance(points[(i + 1) % num])

        # merge short segments
        curr_id = 0
        squared_tolerance = tolerance**2
        while curr_id < num:
            if squares[curr_id % num] >= squared_tolerance:
                # segment long enough: increase 'curr' for the next iteration
                curr_id = find_next(curr_id, 1, squares)
                continue

            # segment too short: merge segment with the shorter neighbor segment (prev or next)
            prev_id = find_next(curr_id, -1, squares)
            next_id = find_next(curr_id, 1, squares)
            if squares[prev_id % num] < squares[next_id % num]:  # merge with the previous segment
                squares[curr_id % num] = 0.0
                curr_id = prev_id
            else:  # merge with the next segment
                squares[next_id % num] = 0.0
                next_id = find_next(next_id, 1, squares)
            squares[curr_id % num] = points[curr_id % num].sq_distance(points[next_id % num])

        return [point for square, point in zip(squares, points) if square > 0.0]

    # Quick exit if tolerance is not positive
    if tolerance <= 0.0:
        return region

    # Merge points of hulls and holes of each polygon
    new_region = pya.Region()
    for poly in region.each():
        new_poly = pya.Polygon(merged_points(list(poly.each_point_hull())))
        for hole_id in range(poly.holes()):
            new_poly.insert_hole(merged_points(list(poly.each_point_hole(hole_id))))
        new_region.insert(new_poly)
    return new_region


def region_with_merged_polygons(region, tolerance, expansion=0.0):
    """Merges polygons in given region. Ignores gaps that are smaller than given tolerance.

    Arguments:
        region: input region
        tolerance: largest gap size to be ignored
        expansion: the amount by which the polygons are expanded (edges move outwards)

    Returns:
        region with merged polygons
    """
    new_region = region.sized(0.5 * tolerance)  # expand polygons to ignore gaps in merge
    new_region.merge()
    new_region.size(expansion - 0.5 * tolerance)  # shrink polygons back to original shape (+ optional expansion)
    new_region = new_region.smoothed(2)  # smooth out the slight jaggedness on the edges
    return new_region


def merge_points_and_match_on_edges(regions, tolerance=2):
    """Merges adjacent points of regions.
    Also goes through each polygon edge and splits the edge whenever it passes close to existing point.

    This function can eliminate gaps and overlaps caused by transformation to simple_polygon.

    Arguments:
        regions: List of regions to be considered and modified
        tolerance: Tolerance in pixels
    """

    def fixed_polygon(pts):
        """Recursively removes spikes of zero width and splits polygon into pieces if possible without adding edges.
        Assumes that consecutive points in pts are not duplicates.
        Returns polygon as list of lists of points.
        """
        size = len(pts)
        if size < 3:
            return []  # ignore polygons with less than 3 points

        # Check for spikes of zero width
        for i, p in enumerate(pts):
            if pts[(i + 2) % size] == p:
                for j in range(1, (size - 1) // 2):
                    if pts[i - j] != pts[(i + 2 + j) % size]:
                        return fixed_polygon([pts[(i + 1 + j + k) % size] for k in range(size - 2 * j)])  # remove spike
                return []  # ignore polygon with zero area

        # Create mapping from point to list of indices
        instance_map = {p: [] for p in pts}
        for i, p in enumerate(pts):
            instance_map[p].append(i)

        # Check if polygon can be split
        for p, instances in instance_map.items():
            if len(instances) < 2:
                continue
            for i0, i1 in zip(instances, instances[1:] + instances[:1]):
                p0 = pts[i0 - 1]
                p1 = pts[(i1 + 1) % size]
                if p0 == p1:
                    continue  # detect equal points at i0-1 and i1+1
                e0, e1 = pya.Edge(p0, p), pya.Edge(p, p1)
                if any(e0.side_of(p2) + e1.side_of(p2) <= e0.side_of(p1) for p2 in (pts[i1 - 1], pts[(i0 + 1) % size])):
                    continue  # detected a hole connection at p
                return fixed_polygon([pts[(i0 + k) % size] for k in range((i1 - i0) % size)]) + fixed_polygon(
                    [pts[(i1 + k) % size] for k in range((i0 - i1) % size)]
                )
        return [pts]  # return polygon without modifications

    def merged_polygon(pts1, pts2):
        """Merges two polygons with common edges.
        Returns merged polygon as list of points. Returns empty list if common edge not found.
        """
        intersection = set(pts1).intersection(pts2)
        if len(intersection) < 2:
            return []

        size1, size2 = len(pts1), len(pts2)
        i1, i2, length = 0, 0, 0
        for pt in intersection:
            instances1 = [i for i, p in enumerate(pts1) if p == pt]
            instances2 = [i for i, p in enumerate(pts2) if p == pt]
            for inst1 in instances1:
                for inst2 in instances2:
                    n = 1
                    while n < len(intersection) and pts1[(inst1 + n) % size1] == pts2[(inst2 - n) % size2]:
                        n += 1
                    if n > length:
                        i1, i2, length = inst1, inst2, n

        if length < 2:
            return []
        j1, j2 = (i1 + length - 1) % size1, (i2 - length + 1) % size2
        return [pts1[(j1 + k) % size1] for k in range((i1 - j1) % size1)] + [
            pts2[(i2 + k) % size2] for k in range((j2 - i2) % size2)
        ]

    # Gather points from regions to `all_points` dictionary. This ignores duplicate points.
    all_points = {}
    for region in regions:
        for polygon in region.each():
            all_points.update({point: [] for point in polygon.to_simple_polygon().each_point()})
    if not all_points:
        return  # nothing is done if no points exist

    # For each point, assign a list of surrounding points using Voronoi diagram
    # Create point sets to merge adjacent points into single point
    merge_sets = []
    point_list = list(all_points)
    vor = spatial.Voronoi([(p.x, p.y) for p in point_list])
    for link in vor.ridge_points:
        p = [point_list[i] for i in link]
        all_points[p[0]].append(p[1])
        all_points[p[1]].append(p[0])
        if p[0].sq_distance(p[1]) <= tolerance**2:
            current_set = set(link)
            other_sets = []
            for merge_set in merge_sets:
                if current_set.intersection(merge_set):
                    current_set.update(merge_set)
                else:
                    other_sets.append(merge_set)
            merge_sets = [current_set] + other_sets

    # Create dictionary of moved points: includes the point to be moved as key and the new position as value
    moved = {}
    if merge_sets:
        for merge_set in merge_sets:
            average = pya.Point()
            for i in merge_set:
                average += point_list[i]
            average /= len(merge_set)
            for i in merge_set:
                if point_list[i] != average:
                    moved[point_list[i]] = average

    # Travel through polygon edges and split edge whenever it passes close to a point
    # Possibly move some points into new location
    for region in regions:
        polygons = []
        for polygon in region.each():
            points = list(polygon.to_simple_polygon().each_point())
            new_points = []
            for i, p1 in enumerate(points):
                p0 = points[i - 1]
                edge = pya.Edge(p0, p1)
                # Travel from p0 to p1 in Voronoi diagram
                while p0 != p1:
                    # Find the next Voronoi cell through which the edge passes
                    next_cell = []
                    for p in all_points[p0]:
                        dot = edge.d().sprod(p - p0)  # dot product between the edge vector and (p - p0)
                        if dot <= 0.0:
                            continue
                        t = (p.sq_distance(edge.p1) - p0.sq_distance(edge.p1)) / dot  # distance to the Voronoi cell
                        if not next_cell or t < next_cell[1]:
                            next_cell = [p, t]
                    # The next_cell is found unless the Voronoi diagram is badly broken
                    p0 = next_cell[0]
                    if edge.distance_abs(p0) <= tolerance:
                        # Point is close to edge, so add the point to the polygon. Finally, p0 is equal to p1 here.
                        new_points.append(moved[p0] if p0 in moved else p0)

            # Remove consecutive duplicate points and update list of polygons by fixed polygons
            polygons += fixed_polygon([p for i, p in enumerate(new_points) if p != new_points[i - 1]])

        # Replace region with merged polygons
        region.clear()
        for i, polygon in enumerate(polygons):
            for j in range(i + 1, len(polygons)):
                merged = merged_polygon(polygon, polygons[j])
                if merged:
                    polygons[j] = merged
                    break
            else:
                region.insert(pya.SimplePolygon(polygon, True))


def is_clockwise(polygon_points):
    """Returns True if the polygon points are in clockwise order, False if they are counter-clockwise.

    Args:
        polygon_points: list of polygon points, must be either in clockwise or counterclockwise order
    """
    # see https://en.wikipedia.org/wiki/Curve_orientation#Orientation_of_a_simple_polygon
    bottom_left_point_idx = 0
    for idx, point in enumerate(polygon_points[1:]):
        if point.x < polygon_points[bottom_left_point_idx].x and point.y < polygon_points[bottom_left_point_idx].y:
            bottom_left_point_idx = idx
    a = polygon_points[bottom_left_point_idx - 1]
    b = polygon_points[bottom_left_point_idx]
    c = polygon_points[(bottom_left_point_idx + 1) % len(polygon_points)]
    det = (b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)
    return det < 0


def circle_polygon(r, n=64, origin=pya.DPoint(0, 0)):
    """
    Returns a polygon for a full circle around the origin.

    Args:
        r: Radius
        origin: Center of the circle, default (0,0)
        n: Number of points.

    Returns: list of ``DPoint``s, length ``n``.
    """
    return pya.DPolygon([origin + pya.DPoint(cos(a / n * 2 * pi) * r, sin(a / n * 2 * pi) * r) for a in range(0, n)])


def arc_points(r, start=0, stop=2 * pi, n=64, origin=pya.DPoint(0, 0)):
    """
    Returns point describing an arc around the origin with specified start and stop angles. The start and stop angle
    are included.

    If start < stop, the points are counter-clockwise; if start > stop, the points are clockwise.

    Args:
        r: Arc radius
        start: Start angle in radians, default 0
        stop: Stop angle in radians, default 2*pi
        origin: Center of the arc, default (0,0)
        n: Number of steps corresponding to a full circle.

    """
    n_steps = max(ceil(n * abs(stop - start) / (2 * pi)), 2)
    step = (stop - start) / (n_steps - 1)
    return [origin + pya.DPoint(cos(start + a * step) * r, sin(start + a * step) * r) for a in range(0, n_steps)]


def _cubic_polynomial(
    control_points: List[pya.DPoint], spline_matrix: np.array, sample_points: int = 100, endpoint: bool = False
) -> List[pya.DPoint]:
    """Returns a list of DPoints sampled uniformly from a third order polynomial spline

    Args:
        control_points: list of exactly four control points
        spline_matrix: matrix of coefficients of the polynomial function
        sample_points: number of points to sample for the curve
        endpoint: if True, will distribute sample points to sample at t = 1.0
    """
    if len(control_points) != 4:
        raise ValueError("There should be exactly four control points for cubic polynomial")
    if spline_matrix.shape != (4, 4):
        raise ValueError("spline_matrix must be of shape (4, 4)")
    geometry_matrix = np.array([[p.x, p.y] for p in control_points]).T
    result_points = []
    for t in np.linspace(0.0, 1.0, sample_points, endpoint=endpoint):
        result_vector = geometry_matrix.dot(spline_matrix).dot(np.array([1, t, t * t, t * t * t]).T)
        result_points.append(pya.DPoint(result_vector[0], result_vector[1]))
    return result_points


def bspline_points(
    control_points: List[pya.DPoint], sample_points: int = 100, startpoint: bool = False, endpoint: bool = False
) -> List[pya.DPoint]:
    """Samples points uniformly from the B-Spline constructed from a sequence of control points.
    The spline is derived from a sequence of cubic splines for each subsequence of four-control points
    in a sliding window.

    Unlike Bezier curves, for each spline in B-Spline it is not guaranteed
    that the first and last control point will be in the spline.

    B-Spline cubic polynomial implemented based on the following reference:
    Kaihuai Qin, "General matrix representations for B-splines", Proceedings Pacific Graphics '98
    Sixth Pacific Conference on Computer Graphics and Applications, Singapore, 1998, pp. 37-43,
    doi: 10.1109/PCCGA.1998.731996

    Args:
        control_points: a sequence of control points, must have at least 4 pya.DPoints elements
        sample_points: number of uniform samples of each cubic B-spline,
            total number of samples is: sample_points * (control_points - 3)
        startpoint: If True, will prepend duplicates of the first control point so that the
            first control point will be in the B-Spline
        endpoint: If True, will append duplicates of the last control point so that the
            last control point will be in the B-Spline

    Returns:
        List of pya.DPoints that can be used as part of a polygon
    """
    # B-Spline doesn't guarantee that the spline will go through the end points,
    # duplicate points on either end if needed
    if startpoint:
        control_points = [control_points[0], control_points[0]] + control_points
    if endpoint:
        control_points = control_points + [control_points[-1], control_points[-1]]
    if len(control_points) < 4:
        raise ValueError("B-Spline needs at least four control points")
    bspline_matrix = (1.0 / 6.0) * np.array([[1, -3, 3, -1], [4, 0, -6, 3], [1, 3, 3, -3], [0, 0, 0, 1]])
    result_points = []
    # Sliding window
    for window_start in range(len(control_points) - 3):
        result_points += _cubic_polynomial(
            control_points[window_start : window_start + 4],
            bspline_matrix,
            sample_points,
            endpoint=(window_start == len(control_points) - 4),
        )
    return result_points


def bezier_points(control_points: List[pya.DPoint], sample_points: int = 100) -> List[pya.DPoint]:
    """Samples points uniformly from the Bezier curve constructed from a sequence of control points.
    The curve is derived from a sequence of cubic splines for each subsequence of four-control points
    such that subsequence shares one control point with the previous subsequence.

    Special care needs to be taken to guarantee continuity in the tangent of the curve.
    The third and fourth control point of each subsequence as well as the second
    control point of the next subsequence have to be in the same line.

    Bezier cubic polynomial implemented based on the following reference:
    Kaihuai Qin, "General matrix representations for B-splines", Proceedings Pacific Graphics '98
    Sixth Pacific Conference on Computer Graphics and Applications, Singapore, 1998, pp. 37-43,
    doi: 10.1109/PCCGA.1998.731996

    Args:
        control_points: a sequence of control points, must be of length equal to 3*n+1 for some integer n
        sample_points: number of uniform samples of each cubic spline,
            total number of samples is: sample_points * ((control_points - 3) / 3)

    Returns:
        List of pya.DPoints that can be used as part of a polygon
    """
    if (len(control_points) - 1) % 3 == 0:
        raise ValueError("For Bezier curve, the number of control points should equal to 3*n+1 for some integer n")
    bezier_matrix = np.array([[1, -3, 3, -1], [0, 3, -6, 3], [0, 0, 3, -3], [0, 0, 0, 1]])
    result_points = []
    # Windows with one shared control point
    for window_start in range(0, len(control_points) - 3, 3):
        result_points += _cubic_polynomial(
            control_points[window_start : window_start + 4],
            bezier_matrix,
            sample_points,
            endpoint=(window_start == len(control_points) - 4),
        )
    return result_points


def force_rounded_corners(region: pya.Region, r_inner: float, r_outer: float, n: int) -> pya.Region:
    """Returns region with rounded corners by trying to force radius as given by r_inner and r_outer.

    This function is useful when corner rounding is wanted next to curved segment. The point of curved segment that is
    closest to the corner limits the radius produced by the klayout round_corners method. This function solves this
    problem by removing the points next to the corner that prevent the full rounding radius from taking effect in the
    round_corners method.

    Please note that this function can't guarantee full radius in cases, where two corners are close to each other.
    For example, if two 90 degree angles are closer than 2 * r distance apart, then the rounding radius is decreased.

    Args:
        region: Region whose corners need to be rounded
        r_inner: Inner corner radius (in database units)
        r_outer: Outer corner radius (in database units)
        n: The number of points per circle

    Returns:
        Region with rounded corners
    """

    corner_max_cos = np.cos(3 * np.pi / n)  # consider point as corner if cos is below this

    def process_points(pts: list[pya.Point]):
        i0 = 0
        while i0 < len(pts):
            if len(pts) < 3:
                return []
            i1, i2, i3 = (i0 + 1) % len(pts), (i0 + 2) % len(pts), (i0 + 3) % len(pts)
            p0, p1, p2, p3 = pts[i0 % len(pts)], pts[i1], pts[i2], pts[i3]
            v0, v1, v2 = p1 - p0, p2 - p1, p3 - p2
            l0, l1, l2 = v0.length(), v1.length(), v2.length()
            cos0, cos1 = v0.sprod(v1) / (l0 * l1), v1.sprod(v2) / (l1 * l2)
            if cos0 > corner_max_cos or cos1 > corner_max_cos:  # do nothing between two corners
                r0, r1 = r_inner if v0.vprod(v1) > 0 else r_outer, r_inner if v1.vprod(v2) > 0 else r_outer
                cut0, cut1 = r0 * np.sqrt((1 - cos0) / (1 + cos0)), r1 * np.sqrt((1 - cos1) / (1 + cos1))  # r*tan(a/2)
                if cut0 + cut1 > l1:
                    div, x0, x1 = v0.vprod(v2), v2.vprod(p0 - p3), v0.vprod(p0 - p3)
                    if x1 * div < 0 < x0 * div:
                        p_cross = p0 + x0 / div * v0
                        if p_cross not in (p0, p3):
                            pts[i1] = p_cross
                            pts = [p for i, p in enumerate(pts) if i != i2]
                            i0 -= 1 + int(i2 < i0)
                            continue
                    pts = [p for i, p in enumerate(pts) if i not in (i1, i2)]
                    i0 -= 1 + int(i1 < i0) + int(i2 < i0)
                    continue
            i0 += 1
        return pts

    # Create new region and insert rounded shapes into it
    result = pya.Region()
    for polygon in region.each_merged():
        poly = pya.Polygon(process_points(list(polygon.each_point_hull())))
        for hole in range(polygon.holes()):
            poly.insert_hole(process_points(list(polygon.each_point_hole(hole))))
        result.insert(poly.round_corners(r_inner, r_outer, n))
    return result
