#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict

from typing import Any, cast, Dict, List, Optional, Type

import torch
from torchrec.metrics.metrics_namespace import MetricName, MetricNamespace, MetricPrefix
from torchrec.metrics.rec_metric import (
    MetricComputationReport,
    RecMetric,
    RecMetricComputation,
    RecMetricException,
)


THRESHOLD = "threshold"


def compute_precision(
    num_true_positives: torch.Tensor, num_false_positives: torch.Tensor
) -> torch.Tensor:
    return torch.where(
        num_true_positives + num_false_positives == 0.0,
        0.0,
        num_true_positives / (num_true_positives + num_false_positives).double(),
    )


def compute_true_pos_sum(
    labels: torch.Tensor,
    predictions: torch.Tensor,
    weights: torch.Tensor,
    threshold: float = 0.5,
) -> torch.Tensor:
    predictions = predictions.double()
    return torch.sum(weights * ((predictions >= threshold) * labels), dim=-1)


def compute_false_pos_sum(
    labels: torch.Tensor,
    predictions: torch.Tensor,
    weights: torch.Tensor,
    threshold: float = 0.5,
) -> torch.Tensor:
    predictions = predictions.double()
    return torch.sum(weights * ((predictions >= threshold) * (1 - labels)), dim=-1)


def get_precision_states(
    labels: torch.Tensor,
    predictions: torch.Tensor,
    weights: Optional[torch.Tensor],
    threshold: float = 0.5,
) -> Dict[str, torch.Tensor]:
    if weights is None:
        weights = torch.ones_like(predictions)
    return {
        "true_pos_sum": compute_true_pos_sum(labels, predictions, weights, threshold),
        "false_pos_sum": compute_false_pos_sum(labels, predictions, weights, threshold),
    }


class PrecisionMetricComputation(RecMetricComputation):
    r"""
    This class implements the RecMetricComputation for Precision.

    The constructor arguments are defined in RecMetricComputation.
    See the docstring of RecMetricComputation for more detail.

    Args:
        threshold (float): If provided, computes Precision metrics cutting off at
            the specified threshold.
    """

    def __init__(self, *args: Any, threshold: float = 0.5, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._add_state(
            "true_pos_sum",
            torch.zeros(self._n_tasks, dtype=torch.double),
            add_window_state=True,
            dist_reduce_fx="sum",
            persistent=True,
        )
        self._add_state(
            "false_pos_sum",
            torch.zeros(self._n_tasks, dtype=torch.double),
            add_window_state=True,
            dist_reduce_fx="sum",
            persistent=True,
        )
        self._threshold: float = threshold

    def update(
        self,
        *,
        predictions: Optional[torch.Tensor],
        labels: torch.Tensor,
        weights: Optional[torch.Tensor],
        **kwargs: Dict[str, Any],
    ) -> None:
        if predictions is None:
            raise RecMetricException(
                "Inputs 'predictions' should not be None for PrecisionMetricComputation update"
            )
        states = get_precision_states(labels, predictions, weights, self._threshold)
        num_samples = predictions.shape[-1]

        for state_name, state_value in states.items():
            state = getattr(self, state_name)
            state += state_value
            self._aggregate_window_state(state_name, state_value, num_samples)

    def _compute(self) -> List[MetricComputationReport]:
        reports = [
            MetricComputationReport(
                name=MetricName.PRECISION,
                metric_prefix=MetricPrefix.LIFETIME,
                value=compute_precision(
                    cast(torch.Tensor, self.true_pos_sum),
                    cast(torch.Tensor, self.false_pos_sum),
                ),
            ),
            MetricComputationReport(
                name=MetricName.PRECISION,
                metric_prefix=MetricPrefix.WINDOW,
                value=compute_precision(
                    self.get_window_state("true_pos_sum"),
                    self.get_window_state("false_pos_sum"),
                ),
            ),
        ]
        return reports


class PrecisionMetric(RecMetric):
    _namespace: MetricNamespace = MetricNamespace.PRECISION
    _computation_class: Type[RecMetricComputation] = PrecisionMetricComputation
