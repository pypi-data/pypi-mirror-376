from __future__ import annotations

from dataclasses import dataclass
import functools
import textwrap
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Generic,
    TypeVar,
    Union,
)
from collections.abc import Iterable

import torch

import torch.utils._pytree as pytree
from torch import Tensor
from torch.utils._pytree import Context, KeyEntry, PyTree
from typing_extensions import Self, TypeAlias

from tensorcontainer.types import DeviceLike, IndexType, ShapeLike
from tensorcontainer.utils import (
    ContextWithAnalysis,
    diagnose_pytree_structure_mismatch,
    resolve_device,
    format_path,
)

HANDLED_FUNCTIONS = {}

TCCompatible: TypeAlias = Union[torch.Tensor, "TensorContainer"]


def implements(torch_function):
    """Register a torch function override for TensorContainer."""

    @functools.wraps(torch_function)
    def decorator(func):
        HANDLED_FUNCTIONS[torch_function] = func
        return func

    return decorator


U = TypeVar("U", bound="TensorContainerPytreeContext")


@dataclass
class TensorContainerPytreeContext(ContextWithAnalysis[U], Generic[U], ABC):
    """Base PyTree context class for tensor containers with common device handling."""

    device: torch.device | None

    def analyze_mismatch_with(self, other: U, entry_index: int) -> str:
        """Analyze mismatches with another TensorContainerPytreeContext, starting with device analysis."""
        # Check device mismatch first
        if self.device != other.device:
            return f"Device mismatch: container 0 device={self.device}, container {entry_index} device={other.device}. "

        # If devices match, return empty string for subclasses to add their analysis
        return ""


class TensorContainer:
    """A foundational base class for PyTree-compatible tensor containers with batch semantics.

    TensorContainer provides a structured way to organize tensors that share common batch dimensions
    while allowing flexible event dimensions. It serves as the foundation for concrete implementations
    like TensorDict (dictionary-style) and TensorDataClass (dataclass-style).

    ## Core Concepts

    ### Batch vs Event Dimensions
    TensorContainer enforces a clear distinction between batch and event dimensions:

    - **Batch Dimensions**: The leading dimensions defined by the `shape` parameter that must be
      consistent across all tensors in the container. These represent the batching structure
      (e.g., batch size, sequence length).

    - **Event Dimensions**: The trailing dimensions beyond the batch shape that can vary between
      different tensors in the container. These represent the actual data structure
      (e.g., feature dimensions, action spaces).

    Example:
        >>> # Container with batch shape (4, 3) - 4 samples, 3 time steps
        >>> container.shape == (4, 3)
        >>>
        >>> # Valid tensors within this container:
        >>> observations = torch.randn(4, 3, 128)    # Event dims: (128,)
        >>> actions = torch.randn(4, 3, 6)           # Event dims: (6,)
        >>> rewards = torch.randn(4, 3)              # Event dims: ()
        >>>
        >>> # All share batch dims (4, 3), different event dims allowed

    ### Shape Management
    The container validates that all contained tensors have compatible shapes:
    - Tensors must have at least `len(shape)` dimensions
    - The first `len(shape)` dimensions must exactly match the container's shape
    - Additional dimensions (event dims) can be arbitrary and different per tensor

    ### Device Management
    Device consistency is enforced with flexible compatibility rules:
    - If container device is None, any tensor device is accepted
    - String device specs ("cuda") are compatible with indexed variants ("cuda:0")
    - All operations preserve device consistency across transformations

    ## PyTree Integration

    TensorContainer is designed for seamless PyTree integration, enabling:
    - Automatic registration via PytreeRegistered mixin in subclasses
    - Efficient tree transformations using `torch.utils._pytree`
    - Compatibility with `torch.compile` and `fullgraph=True`
    - Support for operations like `torch.stack`, `torch.cat` across containers

    ## Torch Function Override System

    Uses `__torch_function__` protocol to intercept torch operations:
    - Register custom implementations via `@implements(torch.function)` decorator
    - Maintains compatibility with PyTorch's dispatch system
    - Enables container-aware versions of functions like `torch.stack`, `torch.cat`

    ## Usage Patterns

    ### Basic Operations
    All tensor-like operations work at the batch dimension level:
    ```python
    # Shape transformations (batch dims only)
    reshaped = container.reshape(8, -1)      # Batch (4,3) -> (8,-1), events preserved
    expanded = container.expand(4, 3, -1)    # Expand batch dims, events unchanged
    permuted = container.permute(1, 0)       # Permute batch dims only

    # Device/type conversions (all tensors)
    gpu_container = container.cuda()         # Move all tensors to GPU
    float_container = container.float()      # Cast all tensors to float

    # Indexing (batch-aware)
    sample = container[0]                    # Select first batch element
    subset = container[1:3]                  # Slice batch dimension
    ```

    ### Advanced Indexing
    Supports full PyTorch indexing semantics:
    - Integer, slice, and ellipsis indexing
    - Boolean mask indexing
    - Advanced indexing with tensor indices
    - Automatic ellipsis transformation for complex indexing

    ### Cloning and Mutation
    ```python
    # Deep clone with memory format control
    cloned = container.clone(memory_format=torch.contiguous_format)

    # In-place assignment (batch-aware)
    container[mask] = new_values            # Boolean mask assignment
    container[:, 0] = initial_values        # Slice assignment
    ```

    ## Unsafe Construction

    For performance-critical scenarios where validation overhead is unacceptable,
    TensorContainer provides an unsafe construction context manager:

    ```python
    # Skip validation during construction
    with TensorContainer.unsafe_construction():
        container = MyContainer(data, shape=(4, 3), device="cuda")
        # No shape/device validation performed
    # Normal validation resumes after context
    ```

    Use this feature carefully - invalid tensor configurations can lead to runtime
    errors in subsequent operations.

    ## Implementation Notes

    ### Memory and Performance
    - Operations use PyTree transformations for efficiency
    - Lazy evaluation where possible (view operations)
    - Memory format preservation in clone operations
    - Reference sharing vs deep copying strategies

    ### Compilation Compatibility
    - Designed for `torch.compile` with `fullgraph=True`
    - Avoids Python constructs that cause graph breaks
    - Uses static shape information where possible
    - Minimal dynamic behavior in hot paths

    ### Error Handling
    - Comprehensive shape/device validation with detailed error messages
    - Path-based error reporting for nested structures using PyTree KeyPath
    - Early validation to catch incompatibilities during construction

    ## Subclassing Guide

    When creating TensorContainer subclasses:

    1. **Inherit from TensorContainer and PytreeRegistered**:
       ```python
       class MyContainer(TensorContainer, PytreeRegistered):
       ```

    2. **Implement PyTree methods**:
       - `_pytree_flatten()` - Convert to (leaves, context)
       - `_pytree_unflatten()` - Reconstruct from leaves and context
       - `_pytree_flatten_with_keys_fn()` - Provide key paths

    3. **Call super().__init__(shape, device)** in constructor

    4. **Override validation** if needed via `_is_shape_compatible()`, `_is_device_compatible()`

    5. **Register torch functions** using `@implements(torch_function)` decorator

    ## Limitations and Constraints

    - Only tensor data participates in transformations; metadata is shallow-copied
    - Batch dimensions must be consistent across all tensors (no ragged batching)
    - Device changes affect all tensors (no mixed-device containers)
    - Shape transformations apply uniformly (no per-tensor custom reshaping)

    Args:
        shape (Tuple[int, ...]): The batch shape that all contained tensors must share
            as their leading dimensions. Defines the batching structure.
        device (Optional[Union[str, torch.device]]): The device all tensors should reside on.
            If None, no device consistency is enforced.

    Raises:
        ValueError: If tensor shapes are incompatible with the specified batch shape
        ValueError: If tensor devices are incompatible with the specified device
        IndexError: For invalid indexing operations (e.g., too many indices)
        RuntimeError: For invalid shape transformations or other tensor operations

    Example:
        >>> # Create a simple subclass for demonstration
        >>> class SimpleContainer(TensorContainer):
        ...     def __init__(self, data, shape, device=None):
        ...         super().__init__(shape, device)
        ...         self.data = data
        >>>
        >>> # Usage with batch shape (2, 3)
        >>> container = SimpleContainer({
        ...     'obs': torch.randn(2, 3, 64),  # Event dims: (64,)
        ...     'action': torch.randn(2, 3, 4) # Event dims: (4,)
        ... }, shape=(2, 3))
        >>>
        >>> # Batch operations preserve event structure
        >>> flattened = container.reshape(6)     # Shape becomes (6,), events preserved
        >>> first_batch = container[0]           # Shape becomes (3,), events preserved
    """

    shape: torch.Size
    device: torch.device | None

    # Thread-local storage for unsafe construction flag
    _validation_disabled = threading.local()

    def __init__(
        self,
        shape: ShapeLike,
        device: DeviceLike | None,
    ):
        super().__init__()

        self.shape = torch.Size(shape)
        self.device = None if device is None else resolve_device(device)

        self._validate()

    @classmethod
    @contextmanager
    def unsafe_construction(cls):
        """Context manager to disable validation during construction.

        This context manager temporarily disables the validation that normally
        occurs during TensorContainer construction. This is for example use in
        TensorContainer.to() that changes the device of all children. This would
        lead to device validation error when we unflatten the TensorContainer.
        As we expect the device to change, we use unsafe_construction to disable
        validation here.

        Warning:
            Using unsafe construction can lead to runtime errors if tensors
            have incompatible shapes or devices. Use with caution.

        Example:
            >>> with TensorContainer.unsafe_construction():
            ...     container = MyContainer(data, shape=(4, 3), device="cuda")
            ...     # No validation performed during construction
            >>> # Normal validation resumes after context

        Yields:
            None: Context manager yields nothing
        """
        old_value = getattr(cls._validation_disabled, "value", False)
        cls._validation_disabled.value = True
        try:
            yield
        finally:
            cls._validation_disabled.value = old_value

    @abstractmethod
    def _pytree_flatten(self) -> tuple[list[Any], Context]:
        pass

    @abstractmethod
    def _pytree_flatten_with_keys_fn(
        self,
    ) -> tuple[list[tuple[KeyEntry, Any]], Any]:
        pass

    @classmethod
    @abstractmethod
    def _pytree_unflatten(
        cls: type[Self], leaves: Iterable[Any], context: Context
    ) -> PyTree:
        pass

    @classmethod
    def __torch_function__(cls, func, types, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        if func not in HANDLED_FUNCTIONS or not all(
            issubclass(t, (Tensor, TensorContainer)) for t in types
        ):
            return NotImplemented
        return HANDLED_FUNCTIONS[func](*args, **kwargs)

    @classmethod
    def _tree_map(
        cls,
        func: Callable[..., Any],
        tree: PyTree,
        *rests: PyTree,
        is_leaf: Callable[[PyTree], bool] | None = None,
    ) -> PyTree:
        def wrapped_func(keypath, x, *xs):
            try:
                return func(x, *xs)
            except Exception as e:
                path = format_path(keypath)
                message = f"Error at path {path}: {type(e).__name__}: {e}"
                raise type(e)(message) from e

        try:
            return pytree.tree_map_with_path(
                wrapped_func, tree, *rests, is_leaf=is_leaf
            )
        except Exception as e:
            # The following code is just to provide better error messages for operations that
            # work on multiple pytrees such as torch.stack() or torch.cat()
            # It is not necessary for TensorContainer to function properly.
            if len(rests) > 0:
                msg = diagnose_pytree_structure_mismatch(tree, *rests, is_leaf=is_leaf)
                if msg:
                    raise RuntimeError(msg) from e

            # Re-raise if it is an unknown error.
            raise e

    @classmethod
    def tree_map_with_path(
        cls,
        func: Callable[..., Any],
        tree: PyTree,
        *rests: PyTree,
        is_leaf: Callable[[PyTree], bool] | None = None,
    ) -> PyTree:
        # This is copied from pytree.tree_map_with_path()
        # We add the check for no leaves as operations are currently no supported for
        # empty TensorContainers.
        keypath_leaves, treespec = pytree.tree_flatten_with_path(tree, is_leaf)

        if len(keypath_leaves) == 0:
            raise RuntimeError(
                "TensorContainer does not allow operations on containers without leaves (i.e. not containing any tensors)."
            )

        keypath_leaves = list(zip(*keypath_leaves))
        all_keypath_leaves = keypath_leaves + [treespec.flatten_up_to(r) for r in rests]
        return treespec.unflatten(func(*xs) for xs in zip(*all_keypath_leaves))

    @classmethod
    def _is_shape_compatible(cls, parent: TensorContainer, child: TCCompatible):
        return child.shape[: parent.ndim] == parent.shape

    @classmethod
    def _is_device_compatible(cls, parent: TensorContainer, child: TCCompatible):
        if parent.device is None:
            return True

        return parent.device == child.device

    def _validate_shape(self, value):
        if not self._is_shape_compatible(self, value):
            raise RuntimeError(
                f"Invalid shape {value.shape}. Expected shape that is compatible to {self.shape}"
            )

    def _validate_device(self, value):
        if not self._is_device_compatible(self, value):
            raise RuntimeError(
                f"Invalid device {value.device}. Expected device that is compatible to {self.device}"
            )

    def _validate(self):
        # Check if validation is disabled via context manager
        if getattr(self._validation_disabled, "value", False):
            return

        key_value, _ = self._pytree_flatten_with_keys_fn()

        for k, v in key_value:
            try:
                self._validate_shape(v)
                self._validate_device(v)
            except RuntimeError as e:
                raise RuntimeError(f"Validation error at key {k}: {e.args}")

    @property
    def ndim(self):
        return len(self.shape)

    # --- Overloaded methods leveraging PyTrees ---

    def copy(self) -> Self:
        return self._tree_map(lambda x: x, self)

    def get_number_of_consuming_dims(self, item) -> int:
        """
        Returns the number of container dimensions consumed by an indexing item.

        This method is crucial for ellipsis expansion calculation. "Consuming" means
        the index item selects from existing container dimensions, reducing the
        container's rank. "Non-consuming" items either don't affect existing
        dimensions (Ellipsis) or add new dimensions (None).

        Args:
            item: An indexing element from an indexing tuple

        Returns:
            Number of container dimensions this item consumes:
            - 0 for non-consuming items (Ellipsis, None)
            - item.ndim for boolean tensors (advanced indexing)
            - 1 for standard consuming items (int, slice, non-bool tensor)

        Examples:
            >>> container.get_number_of_consuming_dims(0)          # int
            1
            >>> container.get_number_of_consuming_dims(slice(0, 2)) # slice
            1
            >>> container.get_number_of_consuming_dims(...)        # Ellipsis
            0
            >>> container.get_number_of_consuming_dims(None)       # None (newaxis)
            0
            >>> bool_mask = torch.tensor([[True, False], [False, True]])
            >>> container.get_number_of_consuming_dims(bool_mask)  # 2D bool tensor
            2
            >>> indices = torch.tensor([0, 2, 1])
            >>> container.get_number_of_consuming_dims(indices)    # non-bool tensor
            1

        Note:
            Used internally by transform_ellipsis_index to calculate how many ':'
            slices the ellipsis should expand to: rank - sum(consuming_dims)
        """
        if item is Ellipsis or item is None:
            return 0
        if isinstance(item, torch.Tensor) and item.dtype == torch.bool:
            return item.ndim

        return 1

    def transform_ellipsis_index(self, shape: torch.Size, idx: tuple) -> tuple:
        """
        Transforms an indexing tuple with ellipsis relative to container batch shape.

        This method is essential for TensorContainer's design: containers have batch dimensions
        (self.shape) but contain individual tensors with varying total shapes. Without this
        preprocessing, ellipsis (...) would expand differently for each tensor based on its
        individual shape, violating container semantics and batch/event dimension boundaries.

        Args:
            shape: The container's batch shape (self.shape), used as reference for ellipsis expansion
            idx: Indexing tuple potentially containing ellipsis (...)

        Returns:
            Equivalent indexing tuple with ellipsis expanded to explicit slices

        Example:
            Container with shape (4, 3) containing tensors (4, 3, 128) and (4, 3, 6, 64):

            # User indexing: container[..., 0]
            # This method transforms: (..., 0) -> (:, 0) based on container batch shape (4, 3)
            # Applied to tensors: [:, 0] works consistently on both tensor shapes
            # Result: Container shape becomes (4,) with tensors (4, 128) and (4, 6, 64)

            # Without this preprocessing, PyTorch would expand ellipsis per-tensor:
            # Tensor (4, 3, 128): [..., 0] -> [:, :, :, 0] (invalid - too many indices)
            # Tensor (4, 3, 6, 64): [..., 0] -> [:, :, :, :, 0] (invalid - too many indices)

        Raises:
            IndexError: If multiple ellipsis found or too many indices for container dimensions

        Note:
            This method is called internally during __getitem__ and __setitem__ operations
            to ensure consistent indexing behavior across all tensors in the container.
        """
        # Step 1: Count indices that "consume" container dimensions
        # - Ellipsis (...) and None don't consume dims (Ellipsis is placeholder, None adds new dim)
        # - int, slice, tensor indices consume 1 dim each (bool tensor consumes its ndim)
        # Example: (..., 0, :) has 2 consuming indices (0 and :), ellipsis doesn't count
        num_consuming_indices = sum(
            self.get_number_of_consuming_dims(item) for item in idx
        )

        # Step 2: Validate that we don't have more indices than container dimensions
        # Container shape (4, 3) has rank=2, so max 2 consuming indices allowed
        rank = len(shape)
        if num_consuming_indices > rank:
            raise IndexError(
                f"too many indices for container: container is {rank}-dimensional, "
                f"but {num_consuming_indices} were indexed"
            )

        # Step 3: Early return if no ellipsis - nothing to transform
        if Ellipsis not in idx:
            return idx

        # Step 4: Validate only one ellipsis exists (PyTorch/NumPy requirement)
        ellipsis_count = 0
        for item in idx:
            if item is Ellipsis:
                ellipsis_count += 1
        if ellipsis_count > 1:
            raise IndexError("an index can only have a single ellipsis ('...')")

        # Step 5: Core calculation - determine how many ':' slices ellipsis should expand to
        # Example: Container shape (4, 3), index (..., 0)
        # - rank=2, consuming_indices=1 -> ellipsis expands to 2-1=1 slice
        # - Result: (..., 0) becomes (:, 0)
        ellipsis_pos = idx.index(Ellipsis)
        num_slices_to_add = rank - num_consuming_indices

        # Step 6: Reconstruct index tuple by replacing ellipsis with explicit slices
        # Split around ellipsis: (a, ..., b) -> (a,) + (:, :, ...) + (b,)
        part_before_ellipsis = idx[:ellipsis_pos]  # Everything before ...
        part_after_ellipsis = idx[ellipsis_pos + 1 :]  # Everything after ...
        ellipsis_replacement = (
            slice(None),
        ) * num_slices_to_add  # (:, :, ...) - the ':' slices

        # Combine parts: before + replacement + after
        final_index = part_before_ellipsis + ellipsis_replacement + part_after_ellipsis

        return final_index

    def __repr__(self) -> str:
        # Use a consistent indent of 4 spaces, which is standard
        indent = "    "

        def _format_item(key, value):
            """Formats a key-value pair for representation."""
            key_repr = f"{str(key)}: "
            if isinstance(value, Tensor):
                # Custom, more informative representation for Tensors
                content = f"Tensor(shape={value.shape}, device={value.device}, dtype={value.dtype})"
            else:
                # For nested TensorDicts, repr() is called recursively.
                # The subsequent textwrap.indent handles the indentation of the nested structure.
                content = repr(value)

            return key_repr + content

        # Flatten the structure to get key-value pairs
        key_value_pairs, _ = self._pytree_flatten_with_keys_fn()

        # Create a string for all items, separated by newlines
        items_str = "\n".join(_format_item(k, v) for k, v in key_value_pairs)

        # Indent the entire block of items
        indented_items = textwrap.indent(items_str, indent)

        # Assemble the final, properly formatted representation string
        return (
            f"{self.__class__.__name__}(\n"
            f"{indent}shape={tuple(self.shape)},\n"
            f"{indent}device={self.device},\n"
            f"{indent}items=\n{textwrap.indent(indented_items, indent)}\n{indent}\n"
            f")"
        )

    def __getitem__(self: Self, key: IndexType) -> Self:
        """Index into the container along batch dimensions.

        Indexing operations are applied to the batch dimensions of all contained tensors.
        Event dimensions are preserved unchanged. Supports all PyTorch indexing patterns:

        - Integer indexing: reduces batch dimensions
        - Slice indexing: preserves batch structure
        - Boolean mask indexing: filters batch elements
        - Advanced indexing: tensor-based selection
        - Ellipsis (...): automatic dimension expansion

        Args:
            key: Index specification (int, slice, tensor, tuple, etc.)

        Returns:
            TensorContainer: New container with indexed tensors

        Raises:
            IndexError: If indexing a 0-dimensional container with non-tuple index
            IndexError: If ellipsis appears multiple times in index tuple

        Example:
            >>> container.shape == (4, 3)
            >>> # Integer indexing - reduces batch dimensions
            >>> sample = container[0]           # shape becomes (3,)
            >>> timestep = container[:, 0]      # shape becomes (4,)
            >>>
            >>> # Slice indexing - preserves structure
            >>> subset = container[1:3]         # shape becomes (2, 3)
            >>>
            >>> # Boolean mask - filters elements
            >>> mask = torch.tensor([True, False, True, False])
            >>> filtered = container[mask]      # shape becomes (2, 3)
            >>>
            >>> # Advanced indexing - tensor indices
            >>> indices = torch.tensor([0, 2, 1])
            >>> reordered = container[indices]  # shape becomes (3, 3)
        """
        if isinstance(key, tuple):
            key = self.transform_ellipsis_index(self.shape, key)
        elif self.ndim == 0:
            raise IndexError(
                "Cannot index a 0-dimensional TensorContainer with a single index. Use a tuple of indices matching the batch shape, or an empty tuple for a scalar."
            )

        return TensorContainer._tree_map(lambda x: x[key], self)

    def __setitem__(self: Self, index: IndexType, value: Self) -> None:
        """
        Sets the value of a slice of the container in-place.

        This method mimics the behavior of `torch.Tensor.__setitem__`. It requires
        that the `value` be broadcastable to the shape of the slice `self[index]`.

        This approach correctly handles advanced indexing (e.g., boolean masks) by
        relying on PyTorch's underlying shape-checking for the leaf-level assignments.

        Args:
            index: The index or slice to set. Supports basic and advanced
                 indexing, including Ellipsis (`...`).
            value: The value to set. If it's a `TensorContainer`, its leaves must be
                   broadcastable to the corresponding sliced leaves of `self`. If it's
                   a scalar or `torch.Tensor`, it must be broadcastable to all sliced
                   leaves of `self`.
        """

        if not isinstance(value, type(self)):
            raise ValueError(f"Invalid value. Expected value of type {type(self)}")

        processed_index = index
        if isinstance(index, tuple):
            processed_index = self.transform_ellipsis_index(self.shape, index)

        for k, v in self._pytree_flatten_with_keys_fn()[0]:
            try:
                v[processed_index] = k.get(value)
            except Exception as e:
                raise type(e)(
                    f"Issue with key {str(k)} and index {processed_index} for value of shape {v.shape} and type {type(v)} and assignment of shape {tuple(value.shape)}"
                ) from e

    def view(self: Self, *shape: int) -> Self:
        """Return a view with modified batch dimensions, preserving event dimensions.

        Creates a view of the container with new batch shape while preserving all
        event dimensions. The total number of elements in batch dimensions must remain
        the same (view constraint).

        Args:
            *shape: New batch shape dimensions

        Returns:
            TensorContainer: View with new batch shape

        Example:
            >>> container.shape == (4, 3)  # 12 batch elements
            >>> # Reshape batch dimensions while preserving event dims
            >>> viewed = container.view(2, 6)    # batch becomes (2, 6)
            >>> viewed = container.view(12)      # batch becomes (12,)
            >>> viewed = container.view(-1, 3)   # batch becomes (4, 3) - inferred
            >>>
            >>> # If tensors have event dims, they are preserved:
            >>> # Original: tensor.shape == (4, 3, 128)  # event dims (128,)
            >>> # After view(2, 6): tensor.shape == (2, 6, 128)
        """
        return TensorContainer._tree_map(
            lambda x: x.view(*shape, *x.shape[self.ndim :]), self
        )

    def reshape(self: Self, *shape: int) -> Self:
        """Return a reshaped container with modified batch dimensions.

        Reshapes the batch dimensions while preserving event dimensions. Unlike view(),
        reshape() can change the memory layout if needed and doesn't require the
        tensor to be contiguous.

        Args:
            *shape: New batch shape dimensions

        Returns:
            TensorContainer: Reshaped container

        Example:
            >>> container.shape == (4, 3)  # 12 batch elements
            >>> reshaped = container.reshape(2, 6)   # batch becomes (2, 6)
            >>> reshaped = container.reshape(-1)     # batch becomes (12,)
            >>>
            >>> # Handles non-contiguous tensors unlike view()
            >>> transposed = container.transpose(0, 1)  # Non-contiguous
            >>> reshaped = transposed.reshape(6, 2)     # Works (reshape can copy)
        """
        return TensorContainer._tree_map(
            lambda x: x.reshape(*shape, *x.shape[self.ndim :]), self
        )

    def to(self: Self, *args, **kwargs) -> Self:
        with TensorContainer.unsafe_construction():
            leaves, context = self._pytree_flatten()
            leaves = [leaf.to(*args, **kwargs) for leaf in leaves]
            tc = self._pytree_unflatten(leaves, context)

        device = self.device

        is_device_in_args = len(args) > 0 and isinstance(args[0], (str, torch.device))
        is_device_in_kwargs = len(kwargs) > 0 and "device" in kwargs

        if is_device_in_args or is_device_in_kwargs:
            device = pytree.tree_leaves(tc)[0].device

        tc.device = device

        return tc

    def detach(self: Self) -> Self:
        return TensorContainer._tree_map(lambda x: x.detach(), self)

    def clone(self: Self, *, memory_format: torch.memory_format | None = None) -> Self:
        """Create a deep copy of the container with optional memory format control.

        Creates a new container with cloned tensors. All tensor data is copied,
        but metadata (shape, device) is shallow-copied. Supports memory format
        specification for performance optimization.

        Args:
            memory_format: Memory layout for cloned tensors. Defaults to preserve_format.
                          Options: torch.contiguous_format, torch.channels_last, etc.

        Returns:
            TensorContainer: Deep copy of the container

        Example:
            >>> cloned = container.clone()  # Deep copy with preserved layout
            >>>
            >>> # Force contiguous memory layout for performance
            >>> contiguous = container.clone(memory_format=torch.contiguous_format)
            >>>
            >>> # Clone preserves independence
            >>> cloned[0] = new_data  # Original container unchanged
        """

        cloned_td = TensorContainer._tree_map(
            lambda x: x.clone(memory_format=memory_format), self
        )
        return cloned_td

    def expand(self: Self, *shape: int) -> Self:
        return TensorContainer._tree_map(
            lambda x: x.expand(*shape, *x.shape[self.ndim :]), self
        )

    def permute(self: Self, *dims: int) -> Self:
        """Permutes the batch dimensions of the container.

        This is equivalent to calling :meth:`torch.Tensor.permute` on each tensor
        in the container, but only for the batch dimensions.

        Args:
            *dims (int): The desired ordering of dimensions.

        Returns:
            A new container with the batch dimensions permuted.
        """
        if len(dims) != self.ndim:
            raise RuntimeError(
                f"permute() expected {self.ndim} dimensions but got {len(dims)}"
            )
        if len(set(dims)) != len(dims):
            raise RuntimeError("permute(): duplicate dimensions are not allowed")
        for dim in dims:
            if not 0 <= dim < self.ndim:
                raise RuntimeError(
                    f"permute(): dimension out of range (expected to be in range of [0, {self.ndim - 1}], but got {dim})"
                )
        return TensorContainer._tree_map(
            lambda x: x.permute(*dims, *range(self.ndim, x.ndim)), self
        )

    def squeeze(self: Self, dim: int | None = None) -> Self:
        """Squeezes the batch dimensions of the container.

        Args:
            dim (int, optional): The dimension to squeeze. If ``None``, all
                batch dimensions of size 1 are squeezed.

        Returns:
            A new container with the specified dimensions squeezed.
        """
        if dim is not None:
            if self.shape[dim] != 1:
                return self.clone()
            new_shape = list(self.shape)
            new_shape.pop(dim)
            return self.reshape(*new_shape)
        else:
            new_shape = [s for s in self.shape if s != 1]
            if len(new_shape) == len(self.shape):
                return self.clone()
            return self.reshape(*new_shape)

    def t(self: Self) -> Self:
        """Transposes the first two batch dimensions of the container.

        This is equivalent to ``self.transpose(0, 1)``.

        Returns:
            A new container with the first two batch dimensions transposed.
        """
        if self.ndim < 2:
            raise RuntimeError(
                "t() expects a tensor with at least 2 dimensions, but got a tensor with "
                f"{self.ndim} dimensions instead"
            )
        return self.transpose(0, 1)

    def transpose(self: Self, dim0: int, dim1: int) -> Self:
        """Transposes two batch dimensions of the container.

        Args:
            dim0 (int): The first dimension to transpose.
            dim1 (int): The second dimension to transpose.

        Returns:
            A new container with the specified dimensions transposed.
        """
        return TensorContainer._tree_map(lambda x: x.transpose(dim0, dim1), self)

    def unsqueeze(self: Self, dim: int) -> Self:
        """Unsqueezes a batch dimension of the container.

        Args:
            dim (int): The dimension to unsqueeze.

        Returns:
            A new container with the specified dimension unsqueezed.
        """
        new_shape = torch.empty(self.shape).unsqueeze(dim).shape
        return self.reshape(*new_shape)

    def size(self) -> torch.Size:
        """Returns the size of the batch dimensions."""
        return self.shape

    def dim(self) -> int:
        """Returns the number of batch dimensions."""
        return self.ndim

    def numel(self) -> int:
        """Returns the total number of elements in the batch dimensions."""
        return self.size().numel()

    def cpu(self: Self) -> Self:
        """Returns a new container with all tensors on the CPU."""
        return self.to("cpu")

    def cuda(self: Self, device=None, non_blocking: bool = False) -> Self:
        """Returns a new container with all tensors on the specified CUDA device."""
        return self.to(
            f"cuda:{device}" if device is not None else "cuda",
            non_blocking=non_blocking,
        )

    def float(self: Self) -> Self:
        """Casts all tensors to float type."""
        return TensorContainer._tree_map(lambda x: x.float(), self)

    def double(self: Self) -> Self:
        """Casts all tensors to double type."""
        return TensorContainer._tree_map(lambda x: x.double(), self)

    def half(self: Self) -> Self:
        """Casts all tensors to half type."""
        return TensorContainer._tree_map(lambda x: x.half(), self)

    def long(self: Self) -> Self:
        """Casts all tensors to long type."""
        return TensorContainer._tree_map(lambda x: x.long(), self)

    def int(self: Self) -> Self:
        """Casts all tensors to int type."""
        return TensorContainer._tree_map(lambda x: x.int(), self)

    def abs(self: Self) -> Self:
        """Computes the absolute value of each tensor in the container."""
        return TensorContainer._tree_map(lambda x: x.abs(), self)

    def add(self: Self, other) -> Self:
        """Adds a value to each tensor in the container."""
        return TensorContainer._tree_map(lambda x: x.add(other), self)

    def sub(self: Self, other) -> Self:
        """Subtracts a value from each tensor in the container."""
        return TensorContainer._tree_map(lambda x: x.sub(other), self)

    def mul(self: Self, other) -> Self:
        """Multiplies each tensor in the container by a value."""
        return TensorContainer._tree_map(lambda x: x.mul(other), self)

    def div(self: Self, other) -> Self:
        """Divides each tensor in the container by a value."""
        return TensorContainer._tree_map(lambda x: x.div(other), self)

    def pow(self: Self, exponent) -> Self:
        """Raises each tensor in the container to a power."""
        return TensorContainer._tree_map(lambda x: x.pow(exponent), self)

    def sqrt(self: Self) -> Self:
        """Computes the square root of each tensor in the container."""
        return TensorContainer._tree_map(lambda x: x.sqrt(), self)

    def log(self: Self) -> Self:
        """Computes the natural logarithm of each tensor in the container."""
        return TensorContainer._tree_map(lambda x: x.log(), self)

    def neg(self: Self) -> Self:
        """Negates each tensor in the container."""
        return TensorContainer._tree_map(lambda x: x.neg(), self)

    def clamp(self: Self, min, max) -> Self:
        """Clamps each tensor in the container to a range."""
        return TensorContainer._tree_map(lambda x: x.clamp(min, max), self)


# --- PyTree-aware implementations of torch functions ---
@implements(torch.stack)
def _stack(
    tensors: tuple[TensorContainer, ...] | list[TensorContainer], dim: int = 0
) -> TensorContainer:
    if not tensors:
        # Replicate PyTorch's error for an empty list
        raise RuntimeError("stack expects a non-empty TensorList")

    first_tc = tensors[0]
    batch_ndim = first_tc.ndim

    # Normalize dim to handle negative values; for stack, the new dim is added
    if dim < 0:
        dim = dim + batch_ndim + 1

    if dim < 0 or dim > batch_ndim:
        raise IndexError(
            f"Dimension {dim - batch_ndim - 1 if dim < 0 else dim} out of range "
            f"(expected 0 to {batch_ndim} for stack operation on shape {tuple(first_tc.shape)})"
        )

    # Pytree handles the stacking of individual tensors and metadata consistency
    result_td = TensorContainer._tree_map(lambda *x: torch.stack(x, dim), *tensors)

    return result_td


@implements(torch.cat)
def _cat(
    tensors: tuple[TensorContainer, ...] | list[TensorContainer], dim: int = 0
) -> TensorContainer:
    # Get the first tensor container to determine the base shape and type
    first_tc = tensors[0]
    batch_ndim = first_tc.ndim

    # Normalize dim to be positive
    if dim < 0:
        dim = dim + batch_ndim

    if dim < 0 or dim > batch_ndim - 1:
        raise IndexError(
            f"Dimension {dim - batch_ndim if dim < 0 else dim} out of range "
            f"(expected 0 to {batch_ndim - 1} for concatenation on shape {tuple(first_tc.shape)})"
        )

    # Create a new TensorContainer of the same type as the first one
    # and apply torch.cat to its internal tensors
    result_td = TensorContainer._tree_map(lambda *x: torch.cat(x, dim), *tensors)

    return result_td
