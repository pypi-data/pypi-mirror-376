import logging
from collections import defaultdict
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from deltalake import DeltaTable, write_deltalake
from deltalake.exceptions import TableNotFoundError

from orcapod.utils.lazy_module import LazyModule

if TYPE_CHECKING:
    import polars as pl
    import pyarrow as pa
    import pyarrow.compute as pc
else:
    pa = LazyModule("pyarrow")
    pl = LazyModule("polars")
    pc = LazyModule("pyarrow.compute")

# Module-level logger
logger = logging.getLogger(__name__)


class DeltaTableDatabase:
    """
    A Delta table database with clear insert vs update semantics.

    - insert(): Never overwrites existing records by default. Can skip duplicates if requested.
                Can be batched for performance. Supports composite keys.

    - update(): Always overwrites existing records. Executes immediately.
                Requires pending batches to be flushed first (or use force_flush=True).

    Supports both single column and composite (multi-column) record IDs.
    """

    # Class constants for internal column names
    ROW_INDEX_COLUMN = "__row_index"
    RECORD_ID_COLUMN = "__record_id"

    def __init__(
        self,
        base_path: str | Path,
        create_base_path: bool = True,
        batch_size: int = 1000,
        max_hierarchy_depth: int = 10,
        allow_schema_evolution: bool = True,
    ):
        self.base_path = Path(base_path)
        self.batch_size = batch_size
        self.max_hierarchy_depth = max_hierarchy_depth
        self.allow_schema_evolution = allow_schema_evolution

        if create_base_path:
            self.base_path.mkdir(parents=True, exist_ok=True)
        elif not self.base_path.exists():
            raise ValueError(
                f"Base path {self.base_path} does not exist and create_base_path=False"
            )

        # Cache for Delta tables to avoid repeated initialization
        self._delta_table_cache: dict[str, DeltaTable] = {}

        # Batch management
        self._pending_batches: dict[str, pa.Table] = {}
        self._pending_record_ids: dict[str, set[str]] = defaultdict(set)
        self._existing_ids_cache: dict[str, set[str]] = defaultdict(set)
        # TODO: reconsider this approach as this is NOT serializable
        self._cache_dirty: dict[str, bool] = defaultdict(lambda: True)

    def _clear_pending(self):
        """Clear all pending state."""
        self._pending_batches = {}
        self._pending_record_ids = defaultdict(set)
        # Note: next_row_index continues incrementing

    def _get_record_key(self, record_path: tuple[str, ...]) -> str:
        """Generate cache key for source storage."""
        return "/".join(record_path)

    def _get_table_path(self, record_path: tuple[str, ...]) -> Path:
        """Get the filesystem path for a given source path."""
        path = self.base_path
        for subpath in record_path:
            path = path / subpath
        return path

    def _validate_record_path(self, record_path: tuple[str, ...]) -> None:
        # TODO: consider removing this as path creation can be tried directly
        """
        Validate source path components.

        Args:
            record_path: Tuple of path components

        Raises:
            ValueError: If path is invalid
        """
        if not record_path:
            raise ValueError("Source path cannot be empty")

        if len(record_path) > self.max_hierarchy_depth:
            raise ValueError(
                f"Source path depth {len(record_path)} exceeds maximum {self.max_hierarchy_depth}"
            )

        # Validate path components
        for i, component in enumerate(record_path):
            if not component or not isinstance(component, str):
                raise ValueError(
                    f"Source path component {i} is invalid: {repr(component)}"
                )

            # Check for filesystem-unsafe characters
            unsafe_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "\0"]
            if any(char in component for char in unsafe_chars):
                raise ValueError(
                    f"Source path {record_path} component {component} contains invalid characters: {repr(component)}"
                )

    def _get_delta_table(self, record_path: tuple[str, ...]) -> DeltaTable | None:
        """
        Get an existing Delta table, either from cache or by loading it.

        Args:
            record_path: Tuple of path components

        Returns:
            DeltaTable instance or None if table doesn't exist
        """
        record_key = self._get_record_key(record_path)
        table_path = self._get_table_path(record_path)

        # Check cache first
        if dt := self._delta_table_cache.get(record_key):
            return dt

        try:
            # Try to load existing table
            delta_table = DeltaTable(str(table_path))
            self._delta_table_cache[record_key] = delta_table
            logger.debug(f"Loaded existing Delta table for {record_key}")
            return delta_table
        except TableNotFoundError:
            # Table doesn't exist
            return None
        except Exception as e:
            logger.error(f"Error loading Delta table for {record_key}: {e}")
            # Try to clear any corrupted cache
            if record_key in self._delta_table_cache:
                self._delta_table_cache.pop(record_key)
            raise

    def _ensure_record_id_column(
        self, arrow_data: "pa.Table", record_id: str
    ) -> "pa.Table":
        """Ensure the table has an record id column."""
        if self.RECORD_ID_COLUMN not in arrow_data.column_names:
            # Add record_id column at the beginning
            key_array = pa.array([record_id] * len(arrow_data), type=pa.large_string())
            arrow_data = arrow_data.add_column(0, self.RECORD_ID_COLUMN, key_array)
        return arrow_data

    def _remove_record_id_column(self, arrow_data: "pa.Table") -> "pa.Table":
        """Remove the record id column if it exists."""
        if self.RECORD_ID_COLUMN in arrow_data.column_names:
            arrow_data = arrow_data.drop([self.RECORD_ID_COLUMN])
        return arrow_data

    def _handle_record_id_column(
        self, arrow_data: "pa.Table", record_id_column: str | None = None
    ) -> "pa.Table":
        """
        Handle record_id column based on add_record_id_column parameter.

        Args:
            arrow_data: Arrow table with record id column
            record_id_column: Control entry ID column inclusion:

        """
        if not record_id_column:
            # Remove the record id column
            return self._remove_record_id_column(arrow_data)

        # Rename record id column
        if self.RECORD_ID_COLUMN in arrow_data.column_names:
            schema = arrow_data.schema
            new_names = [
                record_id_column if name == self.RECORD_ID_COLUMN else name
                for name in schema.names
            ]
            return arrow_data.rename_columns(new_names)
        else:
            raise ValueError(
                f"Record ID column '{self.RECORD_ID_COLUMN}' not found in the table and cannot be renamed."
            )

    def _create_record_id_filter(self, record_id: str) -> list:
        """
        Create a proper filter expression for Delta Lake.

        Args:
            record_id: The entry ID to filter by

        Returns:
            List containing the filter expression for Delta Lake
        """
        return [(self.RECORD_ID_COLUMN, "=", record_id)]

    def _create_record_ids_filter(self, record_ids: list[str]) -> list:
        """
        Create a proper filter expression for multiple entry IDs.

        Args:
            record_ids: List of entry IDs to filter by

        Returns:
            List containing the filter expression for Delta Lake
        """
        return [(self.RECORD_ID_COLUMN, "in", record_ids)]

    def _refresh_existing_ids_cache(self, record_path: tuple[str, ...]) -> None:
        """Refresh the cache of existing IDs in the Delta table."""
        record_key = self._get_record_key(record_path)

        delta_table = self._get_delta_table(record_path)

        if delta_table is None:
            self._existing_ids_cache[record_key] = set()
            self._cache_dirty[record_key] = False
            return

        try:
            # Get all existing IDs from Delta table using standard RECORD_ID_COLUMN
            # TODO: replace this with more targetted loading of only the target column and in batches
            arrow_table = delta_table.to_pyarrow_table()
            if arrow_table.num_rows == 0:
                self._existing_ids_cache[record_key] = set()
            elif self.RECORD_ID_COLUMN not in arrow_table.column_names:
                # TODO: replace this with proper checking of the table schema first!
                logger.warning(f"Delta table missing {self.RECORD_ID_COLUMN} column")
                self._existing_ids_cache[record_key] = set()
            else:
                existing_ids = cast(
                    set[str], set(arrow_table[self.RECORD_ID_COLUMN].to_pylist())
                )
                self._existing_ids_cache[record_key] = existing_ids

            self._cache_dirty[record_key] = False
            logger.debug(
                f"Refreshed existing IDs cache: {len(self._existing_ids_cache)} IDs"
            )

        except Exception as e:
            logger.error(f"Failed to refresh existing IDs cache: {e}")
            self._existing_ids_cache[record_key] = set()
            self._cache_dirty[record_key] = False
            raise

    def _get_existing_ids(self, record_path: tuple[str, ...]) -> set[str]:
        """Get the set of existing IDs in the Delta table, using cache when possible."""
        record_key = self._get_record_key(record_path)
        if (
            self._cache_dirty.get(record_key)
            or record_key not in self._delta_table_cache
        ):
            self._refresh_existing_ids_cache(record_path)
        return self._existing_ids_cache.get(record_key) or set()

    def _invalidate_cache(self, record_path: tuple[str, ...]) -> None:
        """Mark the existing IDs cache as dirty."""
        self._cache_dirty[self._get_record_key(record_path)] = True

    def add_record(
        self,
        record_path: tuple[str, ...],
        record_id: str,
        record: "pa.Table",
        skip_duplicates: bool = False,
        flush: bool = False,
        schema_handling: Literal["merge", "error", "coerce"] = "error",
    ) -> None:
        data_with_record_id = self._ensure_record_id_column(record, record_id)
        self.add_records(
            record_path=record_path,
            records=data_with_record_id,
            record_id_column=self.RECORD_ID_COLUMN,
            schema_handling=schema_handling,
            skip_duplicates=skip_duplicates,
            flush=flush,
        )

    def add_records(
        self,
        record_path: tuple[str, ...],
        records: pa.Table,
        record_id_column: str | None = None,
        skip_duplicates: bool = False,
        flush: bool = False,
        schema_handling: Literal["merge", "error", "coerce"] = "error",
    ) -> None:
        """
        Insert new records. By default, never overwrites existing records.

        Args:
            arrow_table: Arrow table to insert
            id_columns: Single column name or list of column names that form the record ID.
                       For composite keys, values are concatenated with '|' separator.
            schema_handling: How to handle schema differences
            skip_duplicates: If True, skip records with IDs that already exist.
                           If False, raise error on duplicates.
            flush: Whether to flush immediately after the insert

        Raises:
            ValueError: If any record IDs already exist and skip_duplicates=False
        """
        if records.num_rows == 0:
            return

        if record_id_column is None:
            record_id_column = records.column_names[0]

        # Step 1: Validate that record ID column exist
        if record_id_column not in records.column_names:
            raise ValueError(
                f"Specified record ID column {record_id_column} not found in input table {records.column_names}"
            )

        # rename record ID column to a standard name
        if record_id_column != self.RECORD_ID_COLUMN:
            rename_map = {record_id_column: self.RECORD_ID_COLUMN}
            total_name_map = {k: rename_map.get(k, k) for k in records.column_names}
            records = records.rename_columns(total_name_map)

        # Step 2: Deduplicate within input table (keep last occurrence)
        deduplicated_table = self._deduplicate_within_table(records)

        # Step 3: Handle conflicts based on skip_duplicates setting
        if skip_duplicates:
            filtered_table = self._filter_existing_records(
                record_path, deduplicated_table
            )
            if filtered_table.num_rows == 0:
                logger.debug("All records were duplicates, nothing to insert")
                return None
        else:
            # Check for conflicts - insert never allows duplicates when skip_duplicates=False
            # self._check_all_conflicts(record_path, deduplicated_table)
            filtered_table = deduplicated_table

        # Step 4: Handle schema compatibility
        schema_compatible_table = self._handle_schema_compatibility(
            record_path, filtered_table, schema_handling
        )

        # Step 5: Add to pending batch (no overwrite logic needed)
        self._add_to_pending_batch(record_path, schema_compatible_table)

        # Step 6: Auto-flush if needed
        if flush or self._should_auto_flush(record_path):
            self.flush()

    def _deduplicate_within_table(self, table: pa.Table) -> pa.Table:
        # TODO: consider erroring out if duplicates are found
        """Remove duplicates within the input table, keeping the last occurrence."""
        if table.num_rows <= 1:
            return table

        # Create row indices
        indices = pa.array(range(table.num_rows))

        # Add row index column temporarily
        table_with_indices = table.add_column(0, self.ROW_INDEX_COLUMN, indices)

        # Group by RECORD_ID_COLUMN and get the maximum row index for each group
        # This gives us the last occurrence of each ID
        grouped = table_with_indices.group_by([self.RECORD_ID_COLUMN]).aggregate(
            [(self.ROW_INDEX_COLUMN, "max")]
        )

        # Get the row indices to keep - the aggregated column name has "_max" suffix
        max_indices_column = f"{self.ROW_INDEX_COLUMN}_max"
        indices_to_keep = grouped[max_indices_column].to_pylist()

        # Filter original table to keep only these rows
        mask = pc.is_in(indices, pa.array(indices_to_keep))
        return table.filter(mask)

    def _filter_existing_records(
        self, record_path: tuple[str, ...], table: pa.Table
    ) -> pa.Table:
        """Filter out records that already exist (for skip_duplicates=True)."""
        input_ids = set(table[self.RECORD_ID_COLUMN].to_pylist())
        record_key = self._get_record_key(record_path)

        # Get IDs that already exist in pending batch or Delta table
        existing_in_pending = input_ids.intersection(
            self._pending_record_ids[record_key]
        )
        existing_in_delta = input_ids.intersection(self._get_existing_ids(record_path))
        all_existing = existing_in_pending.union(existing_in_delta)

        if not all_existing:
            return table  # No duplicates found

        # Filter out existing records
        mask = pc.invert(
            pc.is_in(table[self.RECORD_ID_COLUMN], pa.array(list(all_existing)))
        )
        filtered = table.filter(mask)

        logger.debug(f"Skipped {len(all_existing)} duplicate records")
        return filtered

    def _check_all_conflicts(
        self, record_path: tuple[str, ...], table: pa.Table
    ) -> None:
        """Check for conflicts with both pending batch and Delta table."""
        input_ids = set(table[self.RECORD_ID_COLUMN].to_pylist())
        record_key = self._get_record_key(record_path)
        # Check conflicts with pending batch
        pending_conflicts = input_ids.intersection(self._pending_record_ids[record_key])
        if pending_conflicts:
            raise ValueError(
                f"Cannot insert records with IDs that already exist in pending batch: {pending_conflicts}. "
                f"Use skip_duplicates=True to skip existing records or update() method to overwrite."
            )

        # Check conflicts with Delta table
        existing_ids = self._get_existing_ids(record_path)
        delta_conflicts = input_ids.intersection(existing_ids)
        if delta_conflicts:
            raise ValueError(
                f"Cannot insert records with IDs that already exist in Delta table: {delta_conflicts}. "
                f"Use skip_duplicates=True to skip existing records or update() method to overwrite."
            )

    def _handle_schema_compatibility(
        self, record_path: tuple[str, ...], table: pa.Table, schema_handling: str
    ) -> pa.Table:
        """Handle schema differences between input and pending batch."""
        record_key = self._get_record_key(record_path)
        pending_batch = self._pending_batches.get(record_key)
        if pending_batch is None:
            return table

        if pending_batch.schema.equals(table.schema):
            # TODO: perform more careful check
            return table

        if schema_handling == "error":
            raise ValueError(
                f"Schema mismatch between input {table.schema} and pending batch {pending_batch.schema}"
            )
        elif schema_handling == "merge":
            try:
                # Unify schemas and cast both input table and pending batch
                unified_schema = pa.unify_schemas([pending_batch.schema, table.schema])

                # Cast the pending batch to unified schema (excluding tracking columns)
                self._pending_batches[record_key] = pending_batch.cast(unified_schema)

                # Cast and return the input table
                return table.cast(unified_schema)
            except Exception as e:
                # TODO: perform more careful error check
                raise ValueError(f"Cannot merge schemas: {e}")
        elif schema_handling == "coerce":
            try:
                # Coerce input table to match existing pending batch schema
                return table.cast(pending_batch.schema)
            except Exception as e:
                raise ValueError(f"Cannot coerce schema: {e}")
        else:
            raise ValueError(f"Unknown schema handling: {schema_handling}")

    def _handle_delta_schema_compatibility(
        self, record_path: tuple[str, ...], table: pa.Table, schema_handling: str
    ) -> pa.Table:
        """Handle schema differences between input and Delta table for updates."""
        record_key = self._get_record_key(record_path)
        if self._delta_table_cache.get(record_key) is None:
            return table

        delta_table = self._delta_table_cache[record_key]

        try:
            # Get Delta table schema and convert from arro3 to pyarrow
            arro3_schema = delta_table.schema().to_arrow()
            delta_schema = pa.schema(arro3_schema)  # type: ignore
        except Exception as e:
            logger.warning(f"Could not get Delta table schema: {e}")
            return table

        if delta_schema.equals(table.schema):
            return table

        if schema_handling == "error":
            raise ValueError("Schema mismatch between input and Delta table")
        elif schema_handling == "merge":
            try:
                # Unify schemas - this might require adding null columns
                unified_schema = pa.unify_schemas([delta_schema, table.schema])
                return table.cast(unified_schema)
            except Exception as e:
                raise ValueError(f"Cannot merge schemas: {e}")
        elif schema_handling == "coerce":
            try:
                # Coerce input table to match Delta table schema
                return table.cast(delta_schema)
            except Exception as e:
                raise ValueError(f"Cannot coerce schema: {e}")
        else:
            raise ValueError(f"Unknown schema handling: {schema_handling}")

    def _add_to_pending_batch(self, record_path: tuple[str, ...], table: pa.Table):
        """Add table to pending batch."""
        # Add row index column for internal tracking
        record_key = self._get_record_key(record_path)
        pending_batch = self._pending_batches.get(record_key)
        if pending_batch is None:
            self._pending_batches[record_key] = table
        else:
            self._pending_batches[record_key] = pa.concat_tables([pending_batch, table])

        pending_ids = cast(list[str], table[self.RECORD_ID_COLUMN].to_pylist())
        self._pending_record_ids[record_key].update(pending_ids)

    def _should_auto_flush(self, record_path: tuple[str, ...]) -> bool:
        """Check if auto-flush should be triggered."""
        record_key = self._get_record_key(record_path)
        return (
            self._pending_batches.get(record_key) is not None
            and self._pending_batches[record_key].num_rows >= self.batch_size
        )

    def get_all_records(
        self,
        record_path: tuple[str, ...],
        record_id_column: str | None = None,
        retrieve_pending: bool = True,
    ) -> pa.Table | None:
        """
        Get all records from both pending batch and Delta table.

        Returns:
            Combined Arrow table with all records, or None if no records exist
        """
        record_key = self._get_record_key(record_path)

        tables_to_combine = []

        # Add Delta table data
        if (delta_table := self._get_delta_table(record_path)) is not None:
            try:
                delta_table_data = delta_table.to_pyarrow_dataset(
                    as_large_types=True
                ).to_table()
                if delta_table_data.num_rows > 0:
                    tables_to_combine.append(delta_table_data)
            except Exception as e:
                logger.warning(f"Error reading Delta table: {e}")

        # Add pending batch data
        if (
            retrieve_pending
            and (pending_batch := self._pending_batches.get(record_key)) is not None
        ):
            if pending_batch.num_rows > 0:
                tables_to_combine.append(pending_batch)

        if not tables_to_combine:
            return None

        if len(tables_to_combine) == 1:
            table_to_return = tables_to_combine[0]
        else:
            table_to_return = pa.concat_tables(tables_to_combine)

        # Handle record_id_column if specified
        return self._handle_record_id_column(table_to_return, record_id_column)

    def get_records_with_column_value(
        self,
        record_path: tuple[str, ...],
        column_values: Collection[tuple[str, Any]] | Mapping[str, Any],
        record_id_column: str | None = None,
        flush: bool = False,
    ) -> "pa.Table | None":
        if flush:
            self.flush_batch(record_path)
        # check if record_id is found in pending batches
        record_key = self._get_record_key(record_path)
        pending_batch = self._pending_batches.get(record_key)

        if isinstance(column_values, Mapping):
            # Convert Mapping to list of tuples
            pair_list = list(column_values.items())
        elif isinstance(column_values, Collection):
            # Ensure it's a list of tuples
            pair_list = cast(list[tuple[str, Any]], list(column_values))

        expressions = [pc.field(c) == v for c, v in pair_list]
        combined_expression = expressions[0]
        for next_expression in expressions[1:]:
            combined_expression = combined_expression & next_expression

        if pending_batch is not None:
            filtered_table = pending_batch.filter(combined_expression)
            return self._handle_record_id_column(filtered_table, record_id_column)

        # Now check the Delta table
        delta_table = self._get_delta_table(record_path)
        if delta_table is None:
            return None

        try:
            # Use schema-preserving read
            result = self._read_delta_table(delta_table, expression=combined_expression)

            if len(result) == 0:
                return None

            # Handle (remove/rename) the record id column before returning
            return self._handle_record_id_column(result, record_id_column)

        except Exception as e:
            logger.error(
                f"Error getting record with {column_values} from {'/'.join(record_path)}: {e}"
            )
            raise e

    def get_record_by_id(
        self,
        record_path: tuple[str, ...],
        record_id: str,
        record_id_column: str | None = None,
        flush: bool = False,
    ) -> "pa.Table | None":
        """
        Get a specific record by record_id with schema preservation.

        Args:
            record_path: Tuple of path components
            record_id: Unique identifier for the record

        Returns:
            Arrow table for the record or None if not found
        """

        if flush:
            self.flush_batch(record_path)

        # check if record_id is found in pending batches
        record_key = self._get_record_key(record_path)
        if record_id in self._pending_record_ids[record_key]:
            # Return the pending record after removing the entry id column
            pending_batch = self._pending_batches[record_key]
            assert pending_batch is not None, "Pending batch should not be None"
            filtered_table = pending_batch.filter(
                pc.field(self.RECORD_ID_COLUMN) == record_id
            )
            if filtered_table.num_rows != 1:
                raise ValueError(
                    f"Expected exactly one record in pending batch with record ID {record_id}, but found {filtered_table.num_rows}"
                )
            return self._handle_record_id_column(filtered_table, record_id_column)

        # Now check the Delta table
        delta_table = self._get_delta_table(record_path)
        if delta_table is None:
            return None

        try:
            # Use schema-preserving read
            filter_expr = self._create_record_id_filter(record_id)
            result = self._read_delta_table(delta_table, filters=filter_expr)

            if len(result) == 0:
                return None

            # Handle (remove/rename) the record id column before returning
            return self._handle_record_id_column(result, record_id_column)

        except Exception as e:
            logger.error(
                f"Error getting record {record_id} from {'/'.join(record_path)}: {e}"
            )
            raise e

    def get_records_by_ids(
        self,
        record_path: tuple[str, ...],
        record_ids: "Collection[str] | pl.Series | pa.Array",
        record_id_column: str | None = None,
        flush: bool = False,
    ) -> "pa.Table | None":
        """
        Retrieve records by entry IDs as a single table with schema preservation.

        Args:
            record_path: Tuple of path components
            record_ids: Entry IDs to retrieve
            add_record_id_column: Control entry ID column inclusion
            preserve_input_order: If True, return results in input order with nulls for missing

        Returns:
            Arrow table containing all found records with original schema, or None if no records found
        """
        _ = self._get_record_key(record_path)
        if flush:
            self.flush_batch(record_path)

        # Convert input to list of strings for consistency

        if isinstance(record_ids, pl.Series):
            record_ids_list = cast(list[str], record_ids.to_list())
        elif isinstance(record_ids, (pa.Array, pa.ChunkedArray)):
            record_ids_list = cast(list[str], record_ids.to_pylist())
        elif isinstance(record_ids, Collection):
            record_ids_list = list(record_ids)
        else:
            raise TypeError(
                f"record_ids must be list[str], pl.Series, or pa.Array, got {type(record_ids)}"
            )
        if len(record_ids) == 0:
            return None

        # check inside the batch
        delta_table = self._get_delta_table(record_path)
        if delta_table is None:
            return None
        try:
            # Use schema-preserving read with filters
            filter_expr = self._create_record_ids_filter(record_ids_list)
            result = self._read_delta_table(delta_table, filters=filter_expr)

            if len(result) == 0:
                return None

            # Handle record_id column based on parameter
            return self._handle_record_id_column(result, record_id_column)

        except Exception as e:
            logger.error(
                f"Error getting records by IDs from {'/'.join(record_path)}: {e}"
            )
            return None

    def _read_delta_table(
        self,
        delta_table: DeltaTable,
        filters: list | None = None,
        expression: "pc.Expression | None" = None,
    ) -> "pa.Table":
        """
        Read table using to_pyarrow_dataset with original schema preservation.

        Args:
            delta_table: The Delta table to read from
            filters: Optional filters to apply

        Returns:
            Arrow table with preserved schema
        """
        filter_expr = None
        # Use to_pyarrow_dataset with as_large_types for Polars compatible arrow table loading
        dataset = delta_table.to_pyarrow_dataset(as_large_types=True)
        if filters and expression is None:
            for filt in filters:
                if len(filt) == 3:
                    col, op, val = filt
                    if op == "=":
                        expr = pc.equal(pc.field(col), pa.scalar(val))  # type: ignore
                    elif op == "in":
                        expr = pc.is_in(pc.field(col), pa.array(val))  # type: ignore
                    else:
                        logger.warning(
                            f"Unsupported filter operation: {op}. Falling back to table-level filter application which may be less efficient."
                        )
                        # Fallback to table-level filtering
                        return dataset.to_table()(filters=filters)

                    if filter_expr is None:
                        filter_expr = expr
                    else:
                        filter_expr = pc.and_(filter_expr, expr)  # type: ignore
        elif expression is not None:
            filter_expr = expression

        if filter_expr is not None:
            return dataset.to_table(filter=filter_expr)

        return dataset.to_table()

    def flush(self) -> None:
        """Flush all pending batches."""
        # TODO: capture and re-raise exceptions at the end
        for record_key in list(self._pending_batches.keys()):
            record_path = tuple(record_key.split("/"))
            try:
                self.flush_batch(record_path)
            except Exception as e:
                logger.error(f"Error flushing batch for {record_key}: {e}")

    def flush_batch(self, record_path: tuple[str, ...]) -> None:
        """
        Flush pending batch for a specific source path.

        Args:
            record_path: Tuple of path components
        """
        logger.debug("Flushing triggered!!")
        record_key = self._get_record_key(record_path)

        if (
            record_key not in self._pending_batches
            or not self._pending_batches[record_key]
        ):
            return

        # Get all pending records
        pending_batch = self._pending_batches.pop(record_key)
        pending_ids = self._pending_record_ids.pop(record_key)

        try:
            # Combine all tables in the batch
            combined_table = pending_batch.combine_chunks()

            table_path = self._get_table_path(record_path)
            table_path.mkdir(parents=True, exist_ok=True)

            # Check if table exists
            delta_table = self._get_delta_table(record_path)

            if delta_table is None:
                # TODO: reconsider mode="overwrite" here
                write_deltalake(
                    table_path,
                    combined_table,
                    mode="overwrite",
                    schema_mode="merge" if self.allow_schema_evolution else "overwrite",
                )
                logger.debug(
                    f"Created new Delta table for {record_key} with {len(combined_table)} records"
                )
            else:
                delta_table.merge(
                    source=combined_table,
                    predicate=f"target.{self.RECORD_ID_COLUMN} = source.{self.RECORD_ID_COLUMN}",
                    source_alias="source",
                    target_alias="target",
                    merge_schema=self.allow_schema_evolution,
                ).when_not_matched_insert_all().execute()

                logger.debug(
                    f"Appended batch of {len(combined_table)} records to {record_key}"
                )

            # Update cache
            self._delta_table_cache[record_key] = DeltaTable(str(table_path))

            # invalide record id cache
            self._invalidate_cache(record_path)

        except Exception as e:
            logger.error(f"Error flushing batch for {record_key}: {e}")
            # Put the tables back in the pending queue
            self._pending_batches[record_key] = pending_batch
            self._pending_record_ids[record_key] = pending_ids
            raise
