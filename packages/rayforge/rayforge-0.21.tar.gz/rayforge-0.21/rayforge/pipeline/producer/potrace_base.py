from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, TYPE_CHECKING
import cairo
import numpy as np
import cv2
import potrace
from ...core.ops import Ops
from .base import OpsProducer

if TYPE_CHECKING:
    from ...core.workpiece import WorkPiece

BORDER_SIZE = 2


def _prepare_surface_for_potrace(surface: cairo.ImageSurface) -> np.ndarray:
    """
    Prepares a Cairo surface for Potrace by converting it to a NumPy
    array of dtype=bool.
    Dark areas of the source image will be `True`.
    """
    surface_format = surface.get_format()
    channels = 4 if surface_format == cairo.FORMAT_ARGB32 else 3

    width, height = surface.get_width(), surface.get_height()
    buf = surface.get_data()
    img = (
        np.frombuffer(buf, dtype=np.uint8)
        .reshape(height, width, channels)
        .copy()
    )

    border_color = [255] * channels
    img = cv2.copyMakeBorder(
        img,
        BORDER_SIZE,
        BORDER_SIZE,
        BORDER_SIZE,
        BORDER_SIZE,
        cv2.BORDER_CONSTANT,
        value=border_color,
    )

    if channels == 4:
        alpha = img[:, :, 3]
        img[alpha == 0] = 255

    gray = cv2.cvtColor(
        img, cv2.COLOR_BGR2GRAY if channels == 3 else cv2.COLOR_BGRA2GRAY
    )
    return gray < 128


class PotraceProducer(OpsProducer, ABC):
    """
    A base class for OpsProducers that use the Potrace engine.
    Subclasses must implement the _filter_curves method.
    """

    def run(
        self,
        laser,
        surface: cairo.ImageSurface,
        pixels_per_mm: Optional[Tuple[float, float]],
        *,
        workpiece: "Optional[WorkPiece]" = None,
        y_offset_mm: float = 0.0,
    ) -> Ops:
        """
        Orchestrates the tracing process and calls a hook for filtering
        the results.
        """
        # It's possible for pixels_per_mm to be None when we want unscaled
        # pixel-based output.
        if surface:
            self.original_surface_height = surface.get_height()
        self.pixels_per_mm = pixels_per_mm

        boolean_image = _prepare_surface_for_potrace(surface)

        # Use aggressive parameters to ensure sharp corners and path fidelity.
        potrace_path = potrace.Bitmap(boolean_image).trace(
            turdsize=1,
            opttolerance=0.055,
            alphamax=0,
            turnpolicy=potrace.TURNPOLICY_MINORITY,
        )

        if not potrace_path:
            return Ops()

        filtered_curves = self._filter_curves(list(potrace_path))
        return self._curves_to_ops(filtered_curves)

    @abstractmethod
    def _filter_curves(
        self, curves: List[potrace.Curve]
    ) -> List[potrace.Curve]:
        """
        An abstract method for subclasses to implement their filtering
        strategy.
        """
        pass

    def _curves_to_ops(self, curves: List[potrace.Curve]) -> Ops:
        """Converts the final list of curves to an Ops object."""
        final_ops = Ops()
        for curve in curves:
            final_ops += self._process_curve(curve)
        return final_ops

    def _transform_point(self, p: Tuple[float, float]) -> Tuple[float, float]:
        """
        Transforms a point from Potrace's bordered coordinate space to the
        final Ops coordinate space, inverting the Y-axis correctly.
        """
        px, py = p

        # Always remove border and invert Y-axis to get a standard
        # bottom-left origin coordinate system.
        ops_px = px - BORDER_SIZE
        ops_py = self.original_surface_height - (py - BORDER_SIZE)

        # If no scaler is provided, return coordinates in this standardized
        # pixel space.
        if self.pixels_per_mm is None:
            return ops_px, ops_py

        # If a scaler is provided, convert from the standardized pixel space
        # to millimeters.
        scale_x, scale_y = self.pixels_per_mm
        ops_mm_x = ops_px / scale_x
        ops_mm_y = ops_py / scale_y
        return ops_mm_x, ops_mm_y

    def _process_curve(self, curve: potrace.Curve) -> Ops:
        """Processes a single closed path from Potrace."""
        ops = Ops()
        ops.move_to(*self._transform_point(curve.start_point))
        for segment in curve:
            self._process_segment(segment, ops)
        ops.close_path()
        return ops

    def _process_segment(self, segment, ops: Ops):
        """Processes a single segment, dispatching to corner or curve logic."""
        if segment.is_corner:
            ops.line_to(*self._transform_point(segment.c))
            ops.line_to(*self._transform_point(segment.end_point))
        else:
            # Only flatten the bezier if we are scaling to mm.
            # Otherwise, just connect the endpoints with a line.
            if self.pixels_per_mm is not None:
                self._flatten_bezier_segment(segment, ops)
            else:
                ops.line_to(*self._transform_point(segment.end_point))

    def _flatten_bezier_segment(self, segment, ops: Ops, num_steps: int = 20):
        """Approximates a cubic Bézier curve with small line segments."""
        if not ops.commands or not ops.commands[-1].end:
            return

        if self.pixels_per_mm is None or not ops.commands:
            return

        last_cmd = ops.commands[-1]
        if last_cmd.end is None:
            return

        # last_cmd.end is a 3D point (x, y, z), but we only need x and y for
        # the 2D reverse-transform calculation.
        start_ops_x, start_ops_y = last_cmd.end[:2]
        scale_x, scale_y = self.pixels_per_mm

        # Reverse the transform to get back to the original Potrace pixel
        # coords
        start_px = np.array(
            [
                (start_ops_x * scale_x) + BORDER_SIZE,
                (self.original_surface_height - (start_ops_y * scale_y))
                + BORDER_SIZE,
            ]
        )

        c1_px = np.array(segment.c1)
        c2_px = np.array(segment.c2)
        end_px = np.array(segment.end_point)

        for t in np.linspace(0, 1, num_steps)[1:]:
            p_px = (
                (1 - t) ** 3 * start_px
                + 3 * (1 - t) ** 2 * t * c1_px
                + 3 * (1 - t) * t**2 * c2_px
                + t**3 * end_px
            )
            ops.line_to(*self._transform_point(p_px))
