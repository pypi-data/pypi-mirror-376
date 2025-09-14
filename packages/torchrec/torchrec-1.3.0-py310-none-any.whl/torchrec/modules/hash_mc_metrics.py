#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict

import logging
import time
from typing import Optional

import torch

from torchrec.modules.hash_mc_evictions import HashZchEvictionConfig


class ScalarLogger(torch.nn.Module):
    """
    A logger to report various metrics related to multi-probe ZCH.

    Args:
        name: name of the embedding table.
        zch_size: size of the sharded embedding table.
        frequency: frequency of reporting metrics.
        start_bucket: start bucket of the rank.


    Example::
        logger = ScalarLogger(...)
        logger(run_type, identities)
    """

    STEPS_BUFFER: str = "_scalar_logger_steps"
    SECONDS_IN_HOUR: int = 3600
    MAX_HOURS: int = 2**31 - 1

    def __init__(
        self,
        name: str,
        zch_size: int,
        frequency: int,
        start_bucket: int,
        log_file_path: str = "",
    ) -> None:
        super().__init__()

        self.register_buffer(
            ScalarLogger.STEPS_BUFFER,
            torch.tensor(1, dtype=torch.int64),
            persistent=False,
        )

        self._name: str = name
        self._zch_size: int = zch_size
        self._frequency: int = frequency
        self._start_bucket: int = start_bucket

        self._dtype_checked: bool = False
        self._total_cnt: int = 0
        self._hit_cnt: int = 0
        self._insert_cnt: int = 0
        self._collision_cnt: int = 0
        self._eviction_cnt: int = 0
        self._opt_in_cnt: int = 0
        self._sum_eviction_age: float = 0.0

        self.logger: logging.Logger = logging.getLogger()
        if (
            log_file_path != ""
        ):  # if a log file path is provided, create a file handler to output logs to the file
            file_handler = logging.FileHandler(
                log_file_path, mode="w"
            )  # initialize file handler
            self.logger.addHandler(file_handler)  # add file handler to logger

    def should_report(self) -> bool:
        # We only need to report metrics from rank0 (start_bucket = 0)

        return (
            self._start_bucket == 0
            and self._total_cnt > 0
            and
            # pyre-fixme[29]: `Union[(self: TensorBase, other: Any) -> Tensor, Tensor,
            #  Module]` is not a function.
            self._scalar_logger_steps % self._frequency == 0
        )

    def update(
        self,
        identities_0: torch.Tensor,
        identities_1: torch.Tensor,
        values: torch.Tensor,
        remapped_ids: torch.Tensor,
        evicted_emb_indices: Optional[torch.Tensor],
        metadata: Optional[torch.Tensor],
        num_reserved_slots: int,
        eviction_config: Optional[HashZchEvictionConfig] = None,
    ) -> None:
        if not self._dtype_checked:
            assert (
                identities_0.dtype == values.dtype
            ), "identity type and feature type must match for meaningful metrics collection."
            self._dtype_checked = True

        remapped_identities_0 = torch.index_select(identities_0, 0, remapped_ids)[:, 0]
        remapped_identities_1 = torch.index_select(identities_1, 0, remapped_ids)[:, 0]
        empty_slot_cnt_before_process = remapped_identities_0 == -1
        empty_slot_cnt_after_process = remapped_identities_1 == -1
        insert_cnt = int(torch.sum(empty_slot_cnt_before_process).item()) - int(
            torch.sum(empty_slot_cnt_after_process).item()
        )

        self._insert_cnt += insert_cnt
        self._total_cnt += values.numel()
        hits = torch.eq(remapped_identities_0, values)
        hit_cnt = int(torch.sum(hits).item())
        self._hit_cnt += hit_cnt
        self._collision_cnt += values.numel() - hit_cnt - insert_cnt

        opt_in_range = self._zch_size - num_reserved_slots
        opt_in_ids = torch.lt(remapped_ids, opt_in_range)
        self._opt_in_cnt += int(torch.sum(opt_in_ids).item())

        if evicted_emb_indices is not None and evicted_emb_indices.numel() > 0:
            deduped_evicted_indices = torch.unique(evicted_emb_indices)
            self._eviction_cnt += deduped_evicted_indices.numel()

            assert (
                metadata is not None
            ), "metadata cannot be None when evicted_emb_indices has values"
            now_c = int(time.time())
            cur_hour = now_c / ScalarLogger.SECONDS_IN_HOUR % ScalarLogger.MAX_HOURS
            if eviction_config is not None and eviction_config.single_ttl is not None:
                self._sum_eviction_age += int(
                    torch.sum(
                        cur_hour
                        + eviction_config.single_ttl
                        - metadata[deduped_evicted_indices, 0]
                    ).item()
                )

    def forward(
        self,
        run_type: str,
        identities: torch.Tensor,
    ) -> None:
        """
        Args:
            run_type: type of the run (train, eval, etc).
            identities: the identities tensor for metrics computation.

        Returns:
            None
        """

        if self.should_report():
            hit_rate = round(self._hit_cnt / self._total_cnt, 3)
            insert_rate = round(self._insert_cnt / self._total_cnt, 3)
            collision_rate = round(self._collision_cnt / self._total_cnt, 3)
            eviction_rate = round(self._eviction_cnt / self._total_cnt, 3)
            total_unused_slots = int(torch.sum(identities[:, 0] == -1).item())
            table_usage_ratio = round(
                (self._zch_size - total_unused_slots) / self._zch_size, 3
            )
            opt_in_rate = (
                round(self._opt_in_cnt / self._total_cnt, 3)
                if self._total_cnt > 0
                else 0
            )
            avg_eviction_age = (
                round(self._sum_eviction_age / self._eviction_cnt, 3)
                if self._eviction_cnt > 0
                else 0
            )

            # log the metrics to console (if no log file path is provided) or to the file (if a log file path is provided)
            self.logger.info(
                f"{self._name=}, {run_type=}, "
                f"{self._total_cnt=}, {self._hit_cnt=}, {hit_rate=}, "
                f"{self._insert_cnt=}, {insert_rate=}, "
                f"{self._collision_cnt=}, {collision_rate=}, "
                f"{self._eviction_cnt=}, {eviction_rate=}, {avg_eviction_age=}, "
                f"{self._opt_in_cnt=}, {opt_in_rate=}, "
                f"{total_unused_slots=}, {table_usage_ratio=}"
            )

            # reset the counter after reporting
            self._total_cnt = 0
            self._hit_cnt = 0
            self._insert_cnt = 0
            self._collision_cnt = 0
            self._eviction_cnt = 0
            self._opt_in_cnt = 0
            self._sum_eviction_age = 0.0

        # pyre-ignore[16]: `ScalarLogger` has no attribute `_scalar_logger_steps`.
        # pyre-ignore[29]: `Union[(self: TensorBase, other: Any) -> Tensor, Tensor, Module]` is not a function.
        self._scalar_logger_steps += 1
