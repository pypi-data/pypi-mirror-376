#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict

#!/usr/bin/env python3

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import torch
from torch import distributed as dist
from torchrec.distributed.types import Multistreamable, ShardingEnv


@dataclass
class ObjectPoolShardingContext(Multistreamable):
    ids_before_input_dist: Optional[torch.Tensor] = None
    num_ids_each_rank_to_receive: Optional[torch.Tensor] = None
    num_ids_each_rank_to_send: Optional[torch.Tensor] = None
    bucketize_permute: Optional[torch.Tensor] = None
    unbucketize_permute: Optional[torch.Tensor] = None

    def record_stream(self, stream: torch.Stream) -> None:
        if self.ids_before_input_dist is not None:
            self.ids_before_input_dist.record_stream(stream)
        if self.num_ids_each_rank_to_receive is not None:
            self.num_ids_each_rank_to_receive.record_stream(stream)
        if self.num_ids_each_rank_to_send is not None:
            self.num_ids_each_rank_to_send.record_stream(stream)
        if self.bucketize_permute is not None:
            self.bucketize_permute.record_stream(stream)
        if self.unbucketize_permute is not None:
            self.unbucketize_permute.record_stream(stream)


@dataclass
class RwShardingContext(Multistreamable):
    block_size: Optional[torch.Tensor] = None

    def record_stream(self, stream: torch.Stream) -> None:
        if self.block_size is not None:
            self.block_size.record_stream(stream)


@dataclass
class ObjectPoolRwShardingContext(ObjectPoolShardingContext, RwShardingContext):
    def record_stream(self, stream: torch.Stream) -> None:
        super().record_stream(stream)


@dataclass
class ObjectPoolReplicatedRwShardingContext(ObjectPoolRwShardingContext):
    def record_stream(self, stream: torch.Stream) -> None:
        super().record_stream(stream)


@dataclass
class TensorPoolRwShardingContext(ObjectPoolRwShardingContext):
    """
    Placeholder for additional sharding context for TensorPool
    """

    def record_stream(self, stream: torch.Stream) -> None:
        super().record_stream(stream)


class ObjectPoolSharding(ABC):
    @abstractmethod
    def create_update_ids_dist(self) -> torch.nn.Module:
        pass

    @abstractmethod
    def create_update_values_dist(self) -> torch.nn.Module:
        pass

    @abstractmethod
    def create_lookup_ids_dist(self) -> torch.nn.Module:
        pass

    @abstractmethod
    def create_lookup_values_dist(self) -> torch.nn.Module:
        pass

    @abstractmethod
    def get_sharded_states_to_register(self) -> Iterable[Tuple[str, torch.Tensor]]:
        pass

    @abstractmethod
    def create_context(self) -> ObjectPoolShardingContext:
        pass


class InferObjectPoolSharding(ABC):
    def __init__(
        self,
        pool_size: int,
        env: ShardingEnv,
        device: torch.device,
    ) -> None:
        self._pool_size = pool_size
        self._env = env
        # pyre-ignore
        self._pg: dist.ProcessGroup = self._env.process_group
        self._world_size: int = self._env.world_size
        self._rank: int = self._env.rank
        self._device = device

        self._block_size: int = (
            pool_size + self._env.world_size - 1
        ) // self._env.world_size
        self._last_block_size: int = self._pool_size - self._block_size * (
            self._world_size - 1
        )
        self.local_pool_size_per_rank: List[int] = [self._block_size] * (
            self._world_size - 1
        ) + [self._last_block_size]

        self._block_size_t: torch.Tensor = torch.tensor(
            [self._block_size], device=self._device, dtype=torch.long
        )

    @abstractmethod
    def create_lookup_ids_dist(self) -> torch.nn.Module:
        pass

    @abstractmethod
    def create_lookup_values_dist(self) -> torch.nn.Module:
        pass
