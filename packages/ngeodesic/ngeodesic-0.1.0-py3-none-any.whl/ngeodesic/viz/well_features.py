# -*- coding: utf-8 -*-
"""
# ==============================================================================
# Apache 2.0 License (ngeodesic.ai)
# ==============================================================================
# Copyright 2025 Ian C. Moore (Provisional Patents #63/864,726, #63/865,437, #63/871,647 and #63/872,334)
# Email: ngeodesic@gmail.com
# Part of Noetic Geodesic Framework (NGF)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""

from __future__ import annotations
from typing import Tuple, Union, Optional
import numpy as np

from ngeodesic.core.smoothing import moving_average
from ngeodesic.synth.arc_like import PRIMS, make_synthetic_traces_stage11
from ngeodesic.core.energies import perpendicular_energy


def _z(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, float)
    return (x - x.mean()) / (x.std() + 1e-8)

def _as_rng(rng: Optional[Union[int, np.random.Generator]]) -> np.random.Generator:
    if isinstance(rng, np.random.Generator):
        return rng
    return np.random.default_rng(None if rng is None else int(rng))

def collect_HE(samples: int, rng: Union[int, np.random.Generator, None], T: int, sigma: int, **gen_kwargs) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build (H, E) where:
      - H: rows are concatenated z-scored smoothed residuals per channel
      - E: normalized total energy per sample (for coloring)
    """
    rng = _as_rng(rng)
    H_rows, E_vals = [], []
    for _ in range(int(samples)):
        traces, _ = make_synthetic_traces_stage11(rng, T=T, **gen_kwargs)
        E_perp = perpendicular_energy(traces)
        S = {p: moving_average(E_perp[p], k=sigma) for p in PRIMS}
        feats = np.concatenate([_z(S[p]) for p in PRIMS], axis=0)
        H_rows.append(feats)
        E_vals.append(float(sum(np.trapz(S[p]) for p in PRIMS)))
    H = np.vstack(H_rows)
    E = np.asarray(E_vals, float)
    E = (E - E.min()) / (E.ptp() + 1e-9)
    return H, E
