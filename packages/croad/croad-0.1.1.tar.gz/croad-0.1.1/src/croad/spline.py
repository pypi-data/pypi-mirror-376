from typing import Any
from geomdl import BSpline, fitting
from geomdl.knotvector import generate
from pydantic import BaseModel, Field, ConfigDict
import numpy as np
from scipy.integrate import quad


class InteractiveSpline(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    curve: BSpline.Curve = Field(default_factory=BSpline.Curve)
    ctrl_pts: np.ndarray = Field(default_factory=lambda: np.empty((0, 2), dtype=float))
    clamped: bool = False
    loop: bool = False
    sample_size: int = 100

    valid: bool = False

    def model_post_init(self, context: Any, /) -> None:
        self.curve.degree = 4

    def prepare_curve(self):
        self.valid = False
        if self.curve.degree < 1:
            return
        if len(self.ctrl_pts) <= self.curve.degree:
            return
        if not self.loop:
            self.curve.ctrlpts = self.ctrl_pts.tolist()
        else:
            self.curve.ctrlpts = np.vstack((self.ctrl_pts, self.ctrl_pts[:self.curve.degree])).tolist()
        self.curve.knotvector = generate(self.curve.degree, self.curve.ctrlpts_size, clamped=self.clamped)
        self.curve.delta = 1. / self.sample_size
        self.valid = True

    @property
    def points(self) -> np.ndarray:
        if not self.valid:
            return np.empty((0, 2), dtype=float)
        return np.array(self.curve.evalpts)

    @property
    def x(self) -> np.ndarray:
        if not self.valid:
            return np.array([], dtype=float)
        return np.linspace(self.curve.domain[0], self.curve.domain[1], self.curve.sample_size)

    @property
    def s(self) -> np.ndarray:
        if not self.valid:
            return np.array([], dtype=float)
        x = self.x
        length = np.zeros_like(x, dtype=float)
        def _fun(u):
            return np.linalg.norm(self.curve.derivatives(u, 1)[1])
        for i in range(1, len(x)):
            length[i] = length[i - 1] + quad(_fun, x[i - 1], x[i])[0]
        return length

    @property
    def k(self) -> np.ndarray:
        if not self.valid:
            return np.array([], dtype=float)
        if self.curve.degree < 3:
            return np.array([], dtype=float)
        return np.vectorize(self.get_k)(self.x)

    @property
    def kv(self) -> np.ndarray:
        if not self.valid:
            return np.array([], dtype=float)
        if self.curve.degree < 4:
            return np.array([], dtype=float)
        return np.vectorize(self.get_kv)(self.x)

    def get_k(self, u: float):
        if not self.valid:
            return None
        if self.curve.degree < 3:
            return None
        der = self.curve.derivatives(u, 2)
        dx = der[1][0]
        dy = der[1][1]
        ddx = der[2][0]
        ddy = der[2][1]
        f = dx * ddy - dy * ddx
        g = (dx ** 2 + dy ** 2) ** 1.5
        if g < 1e-9:
            return 0.
        return f / g

    def get_kv(self, u: float):
        if not self.valid:
            return None
        if self.curve.degree < 4:
            return None
        der = self.curve.derivatives(u, 3)
        dx = der[1][0]
        dy = der[1][1]
        ddx = der[2][0]
        ddy = der[2][1]
        dddx = der[3][0]
        dddy = der[3][1]
        f = dx * ddy - dy * ddx
        df = dx * dddy - dy * dddx
        h = dx ** 2 + dy ** 2
        m = dx * ddx + dy * ddy
        if h < 1e-9:
            return 0
        return (df * h - 3. * f * m) / (h ** 3)


def fit_spline(
        method: str,
        origin_points: np.ndarray,
        minimal_interval: float = 0.,
        degree: int = 4,
        centripetal = False,
        fit_size: int = None,
):
    if len(origin_points) < 2:
        return None
    points = []
    if minimal_interval > 0.:
        points.append(origin_points[0])
        interval2 = minimal_interval ** 2
        for p in origin_points:
            if np.sum((points[-1] - p) ** 2) >= interval2:
                points.append(p)
    else:
        points = origin_points.tolist()
    if len(points) <= degree + 1:
        return None
    curve = None
    if method in 'interpolate':
        curve = fitting.interpolate_curve(points, degree, centripetal=centripetal)
    if method in 'approximate':
        if fit_size is None:
            curve = fitting.approximate_curve(points, degree, centripetal=centripetal)
        else:
            fit_size = min(len(points) - 1, max(degree + 1, fit_size))
            curve = fitting.approximate_curve(points, degree, centripetal=centripetal, ctrlpts_size=fit_size)
    def purge():
        x_min, y_min = origin_points.min(axis=0)
        x_max, y_max = origin_points.max(axis=0)
        x_range = x_max - x_min
        y_range = y_max - y_min
        x_min -= x_range
        x_max += x_range
        y_min -= y_range
        y_max += y_range
        curve.ctrlpts = [
            point for point in curve.ctrlpts
            if x_min <= point[0] <= x_max and y_min <= point[1] <= y_max
        ]
    purge()
    return curve

def update_spline_from_fit(
        interactive: InteractiveSpline,
        fit: BSpline.Curve,
):
    if fit is None:
        return
    interactive.curve = fit
    interactive.ctrl_pts = np.array(fit.ctrlpts)
    interactive.clamped = True
    interactive.loop = False
    interactive.valid = False
