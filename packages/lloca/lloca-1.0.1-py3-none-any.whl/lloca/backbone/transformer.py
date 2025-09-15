from functools import partial
from typing import Optional

import torch
from torch import nn
from torch.utils.checkpoint import checkpoint

from .attention import LLoCaAttention
from ..reps.tensorreps import TensorReps


class BaselineLayerNorm(nn.Module):
    """Baseline layer norm over all dimensions except the first."""

    @staticmethod
    def forward(inputs: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Parameters
        ----------
        inputs : Tensor
            Input data

        Returns
        -------
        outputs : Tensor
            Normalized inputs.
        """
        return torch.nn.functional.layer_norm(
            inputs, normalized_shape=inputs.shape[-1:]
        )


class MultiHeadQKVLinear(nn.Module):
    """Compute queries, keys, and values via multi-head attention.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    hidden_channels : int
        Number of hidden channels = size of query, key, and value.
    num_heads : int
        Number of attention heads.
    """

    def __init__(self, in_channels, hidden_channels, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.linear = nn.Linear(in_channels, 3 * hidden_channels * num_heads)

    def forward(self, inputs):
        """Forward pass.

        Returns
        -------
        q : Tensor
            Queries
        k : Tensor
            Keys
        v : Tensor
            Values
        """
        qkv = self.linear(inputs)  # (..., num_items, 3 * hidden_channels * num_heads)

        *leading, items, last = qkv.shape
        hidden_channels = last // (3 * self.num_heads)
        qkv = qkv.view(*leading, items, 3, hidden_channels, self.num_heads)
        qkv = qkv.movedim(-3, 0).movedim(-1, len(leading) + 1)
        q, k, v = qkv.unbind(dim=0)  # 3x (..., num_heads, num_items, hidden_channels)
        return q, k, v


class MultiQueryQKVLinear(nn.Module):
    """Compute queries, keys, and values via multi-query attention.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    hidden_channels : int
        Number of hidden channels = size of query, key, and value.
    num_heads : int
        Number of attention heads.
    """

    def __init__(self, in_channels, hidden_channels, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.q_linear = nn.Linear(in_channels, hidden_channels * num_heads)
        self.k_linear = nn.Linear(in_channels, hidden_channels)
        self.v_linear = nn.Linear(in_channels, hidden_channels)

    def forward(self, inputs):
        """Forward pass.

        Parameters
        ----------
        inputs : Tensor
            Input data

        Returns
        -------
        q : Tensor
            Queries
        k : Tensor
            Keys
        v : Tensor
            Values
        """
        q = self.q_linear(inputs)

        *leading, items, last = q.shape
        hidden_channels = last // self.num_heads
        q = q.reshape(*leading, items, self.num_heads, hidden_channels)
        q = q.movedim(-2, -3)

        k = self.k_linear(inputs)[
            ..., None, :, :
        ]  # (..., head=1, item, hidden_channels)
        v = self.v_linear(inputs)[..., None, :, :]
        return q, k, v


class BaselineSelfAttention(nn.Module):
    """Baseline self-attention layer.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of input channels.
    hidden_channels : int
        Number of hidden channels = size of query, key, and value.
    attention
    num_heads : int
        Number of attention heads.
    multi_query : bool
        Use multi-query attention instead of multi-head attention.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        hidden_channels: int,
        attention,
        num_heads: int = 8,
        multi_query: bool = True,
        dropout_prob=None,
    ) -> None:
        super().__init__()

        # Store settings
        self.num_heads = num_heads
        self.hidden_channels = hidden_channels

        self.attention = attention

        # Linear maps
        qkv_class = MultiQueryQKVLinear if multi_query else MultiHeadQKVLinear
        self.qkv_linear = qkv_class(in_channels, hidden_channels, num_heads)
        self.out_linear = nn.Linear(hidden_channels * num_heads, out_channels)

        if dropout_prob is not None:
            self.dropout = nn.Dropout(dropout_prob)
        else:
            self.dropout = None

    def forward(
        self,
        inputs: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        is_causal: bool = False,
    ) -> torch.Tensor:
        """Forward pass.

        Parameters
        ----------
        inputs : Tensor
            Input data
        attention_mask : None or Tensor or xformers.ops.AttentionBias
            Optional attention mask

        Returns
        -------
        outputs : Tensor
            Outputs
        """
        q, k, v = self.qkv_linear(
            inputs
        )  # each: (..., num_heads, num_items, num_channels)

        # Attention layer
        h = self.attention(
            q.contiguous(),
            k.expand_as(q).contiguous(),
            v.expand_as(q),
            attn_mask=attention_mask,
            is_causal=is_causal,
        )

        # Concatenate heads and transform linearly
        *leading, num_heads, num_items, hidden_channels = h.shape
        h = h.permute(*range(len(leading)), -2, -3, -1)
        h = h.reshape(*leading, num_items, num_heads * hidden_channels)

        outputs = self.out_linear(h)  # (..., num_items, out_channels)

        if self.dropout is not None:
            outputs = self.dropout(outputs)

        return outputs


class BaselineTransformerBlock(nn.Module):
    """Baseline transformer block.

    Inputs are first processed by a block consisting of LayerNorm, multi-head self-attention, and
    residual connection. Then the data is processed by a block consisting of another LayerNorm, an
    item-wise two-layer MLP with GeLU activations, and another residual connection.

    Parameters
    ----------
    channels : int
        Number of input and output channels.
    attention
    num_heads : int
        Number of attention heads.
    increase_hidden_channels : int
        Factor by which the key, query, and value size is increased over the default value of
        hidden_channels / num_heads.
    multi_query : bool
        Use multi-query attention instead of multi-head attention.
    """

    def __init__(
        self,
        channels,
        attention,
        num_heads: int = 8,
        increase_hidden_channels=1,
        multi_query: bool = True,
        mlp_factor: int = 2,
        dropout_prob=None,
    ) -> None:
        super().__init__()

        self.norm = BaselineLayerNorm()

        hidden_channels = channels // num_heads * increase_hidden_channels

        self.attention = BaselineSelfAttention(
            channels,
            channels,
            hidden_channels,
            attention,
            num_heads=num_heads,
            multi_query=multi_query,
            dropout_prob=dropout_prob,
        )

        self.mlp = nn.Sequential(
            nn.Linear(channels, mlp_factor * channels),
            nn.Dropout(dropout_prob) if dropout_prob is not None else nn.Identity(),
            nn.GELU(),
            nn.Linear(mlp_factor * channels, channels),
            nn.Dropout(dropout_prob) if dropout_prob is not None else nn.Identity(),
        )

    def forward(
        self, inputs: torch.Tensor, attention_mask=None, is_causal=False
    ) -> torch.Tensor:
        """Forward pass.

        Parameters
        ----------
        inputs : Tensor
            Input data
        attention_mask : None or Tensor or xformers.ops.AttentionBias
            Optional attention mask

        Returns
        -------
        outputs : Tensor
            Outputs
        """

        # Residual attention
        h = self.norm(inputs)
        h = self.attention(h, attention_mask=attention_mask, is_causal=is_causal)
        outputs = inputs + h

        # Residual MLP
        h = self.norm(outputs)
        h = self.mlp(h)
        outputs = outputs + h

        return outputs


class Transformer(nn.Module):
    """Baseline transformer.

    Combines num_blocks transformer blocks, each consisting of multi-head self-attention layers, an
    MLP, residual connections, and normalization layers.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    attn_reps : str
        Representation of each attention head.
    out_channels : int
        Number of output channels.
    num_blocks : int
        Number of transformer blocks.
    num_heads : int
        Number of attention heads.
    increase_hidden_channels : int
        Factor by which the key, query, and value size is increased over the default value of
        hidden_channels / num_heads.
    multi_query : bool
        Use multi-query attention instead of multi-head attention.
    """

    def __init__(
        self,
        in_channels: int,
        attn_reps: str,
        out_channels: int,
        num_blocks: int,
        num_heads: int,
        checkpoint_blocks: bool = False,
        increase_hidden_channels=1,
        mlp_factor: int = 2,
        multi_query: bool = False,
        dropout_prob=None,
    ) -> None:
        super().__init__()
        attn_reps = TensorReps(attn_reps)
        self.hidden_channels = attn_reps.dim * num_heads
        self.checkpoint_blocks = checkpoint_blocks
        self.attention = LLoCaAttention(attn_reps, num_heads)

        self.linear_in = nn.Linear(in_channels, self.hidden_channels)
        self.blocks = nn.ModuleList(
            [
                BaselineTransformerBlock(
                    self.hidden_channels,
                    attention=self.attention,
                    num_heads=num_heads,
                    increase_hidden_channels=increase_hidden_channels,
                    mlp_factor=mlp_factor,
                    multi_query=multi_query,
                    dropout_prob=dropout_prob,
                )
                for _ in range(num_blocks)
            ]
        )
        self.linear_out = nn.Linear(self.hidden_channels, out_channels)

    def forward(
        self, inputs: torch.Tensor, frames, attention_mask=None, is_causal=False
    ) -> torch.Tensor:
        """Forward pass.

        Parameters
        ----------
        inputs : Tensor
            Input data with shape (..., num_items, in_channels)
        frames : Frames
            Local frames used for invariant particle attention
        attention_mask : None or Tensor or xformers.ops.AttentionBias
            Optional attention mask
        is_causal: bool

        Returns
        -------
        outputs : Tensor
            Outputs with shape (..., num_items, out_channels)
        """
        self.attention.prepare_frames(frames)

        h = self.linear_in(inputs)
        for block in self.blocks:
            if self.checkpoint_blocks:
                fn = partial(block, attention_mask=attention_mask, is_causal=is_causal)
                h = checkpoint(fn, h)
            else:
                h = block(h, attention_mask=attention_mask, is_causal=is_causal)
        outputs = self.linear_out(h)
        return outputs
