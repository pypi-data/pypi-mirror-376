import hashlib
import statistics
from typing import List

from sqlalchemy import (
    Index,
    and_,
    inspect,
    select,
    true,
    update,
)

from seshat.data_class import SFrame
from seshat.general.exceptions import InvalidArgumentsError
from seshat.source.mixins import SQLMixin
from seshat.source.saver import Saver
from seshat.source.saver.base import POSTGRES, SaveConfig
from seshat.source.saver.utils import PostgresUtils
from seshat.transformer.schema import Schema
from seshat.transformer.schema.base import UpdateFuncs
from seshat.transformer.trimmer.base import NaNTrimmer


class SQLDBSaver(SQLMixin, Saver):
    def save(self, sf: SFrame, *args, **kwargs):

        for config in self.save_configs:
            self.fill_cols_to_field(config.schema)
            self.ensure_table_exists(config.table, config.schema)
            self.create_index(config)

            selected_sf = sf.get(config.sf_key)
            has_id = False
            for col in config.schema.cols:
                if col.is_id:
                    has_id = True
                break
            if has_id:
                selected_sf = self.drop_nan_ids(selected_sf, config.schema)

            if config.clear_table:
                self.delete(config.table)
            if config.strategy == "update":
                self.update(selected_sf, config)
            elif config.strategy == "copy":
                self.copy(selected_sf, config)
            else:
                self.insert(selected_sf, config)

    def delete(self, table_name):
        table, _ = self.get_table(table_name, autoload=True)
        self.write_on_db(table.delete())

    def drop_table(self, table_name):
        db_schema, actual_table_name = self._parse_table_name(table_name)
        engine = self.get_engine()
        inspector = inspect(engine)

        # Check if table exists in the specific schema
        existing_tables = inspector.get_table_names(schema=db_schema)

        if actual_table_name in existing_tables:
            table, _ = self.get_table(table_name, autoload=True)
            table.drop(engine)

    def insert(self, selected_sf: SFrame, config: SaveConfig):
        values = self.prepare_sf_to_insert(selected_sf, config).to_dict()
        table, _ = self.get_table(config.table, autoload=True)
        self.write_on_db(table.insert(), values)

    def copy(self, selected_sf: SFrame, config: SaveConfig):
        selected_sf = self.prepare_sf_to_insert(selected_sf, config)
        PostgresUtils.copy(self.get_engine(), config.table, selected_sf.to_raw())

    def update(self, selected_sf: SFrame, config: SaveConfig):
        table, _ = self.get_table(config.table, autoload=True)
        values = selected_sf.to_dict()
        id_cols_schema = config.schema.get_id(return_first=False)

        if self.db_type == POSTGRES:
            try:
                PostgresUtils.ensure_unique_constraint(
                    self.get_engine(), table, config.schema
                )
                stmt = PostgresUtils.generate_upsert_stmt(table, values, config)
                self.write_on_db(stmt)
                return
            except Exception:
                pass

        rows_to_update = self._get_existing_rows(table, values, config.schema)
        rows_to_create = []
        self._update_rows_list(rows_to_update, rows_to_create, values, config.schema)

        if rows_to_create:
            self.write_on_db(table.insert(), rows_to_create)
        db_id_cols = tuple(getattr(table.c, id_col.to) for id_col in id_cols_schema)
        for row in rows_to_update:
            condition = None
            for db_id in db_id_cols:
                new_condition = db_id == row.pop(db_id.key)
                if condition is None:
                    condition = new_condition
                else:
                    condition = and_(condition, new_condition)
            update_query = update(table).where(condition).values(row)
            self.write_on_db(update_query)

    def create_index(self, config):
        table, metadata = self.get_table(config.table, autoload=True)
        current_indexes = set()
        for index in table.indexes:
            hashed_cols = self.hash_columns([col.key for col in index.columns])
            current_indexes.add(hashed_cols)

        # Parse table name to get the actual table name without schema
        _, actual_table_name = self._parse_table_name(config.table)

        for index in config.indexes:
            index_cols = [index] if isinstance(index, str) else index
            index_hash = self.hash_columns(index_cols)
            if index_hash in current_indexes:
                continue

            # Use the actual table name (without schema) for index naming
            index_name = f"{'_'.join(index_cols)}_index_{actual_table_name}"
            index_obj = Index(
                index_name,
                *[getattr(table.c, index_col) for index_col in index_cols],
            )
            index_obj.create(self.get_engine())
            current_indexes.add(index_hash)

    def _update_rows_list(self, rows_to_update, rows_to_create, values, schema):
        col_to_func_map = {
            col.original: col.update_func or "replace"
            for col in schema.cols
            if not col.is_id
        }
        id_cols = schema.get_id(return_first=False)

        id_to_db_records_map = {
            tuple(row[id_col.to] for id_col in id_cols): row for row in rows_to_update
        }

        for col in schema.cols:
            if col.is_id:
                continue
            func = self.get_func(col_to_func_map[col.original])
            for row in values:
                db_records_key = tuple(row[id_col.original] for id_col in id_cols)
                db_result = id_to_db_records_map.get(db_records_key)
                if db_result is None:
                    id_to_db_records_map[db_records_key] = db_result = {
                        id_col.to: row[id_col.original] for id_col in id_cols
                    }
                    rows_to_create.append(db_result)
                new_value = row[col.original]
                if isinstance(new_value, str) and new_value.isdigit():
                    new_value = float(new_value)
                db_result[col.to] = func((db_result.get(col.to, 0), new_value))

    def _get_existing_rows(self, table, values, schema):
        id_cols = schema.get_id(return_first=False)
        condition_values = {id_col.to: [] for id_col in id_cols}
        for row in values:
            for id_col in id_cols:
                condition_values[id_col.to].append(row[id_col.original])
        condition = true()
        for to, vals in condition_values.items():
            condition = and_(condition, getattr(table.c, to).in_(vals))

        query = select(*[getattr(table.c, col.to) for col in schema.cols]).where(
            condition
        )
        return self.get_from_db(query)

    def get_from_db(self, query):
        with self.get_engine().connect() as conn:
            result = conn.execute(query)
            dict_result = []
            for row in result.mappings():
                dict_result.append(dict(row))
            return dict_result

    @staticmethod
    def fill_cols_to_field(schema):
        for col in schema.cols:
            col.to = col.to or col.original

    @classmethod
    def prepare_sf_to_insert(cls, selected_sf: SFrame, config: SaveConfig):
        if config.schema:
            config.schema.convert_type = False
            selected_sf = config.schema(selected_sf)
        return selected_sf

    @staticmethod
    def get_func(func_name):
        if func_name not in (valid_fns := UpdateFuncs.__args__):
            raise InvalidArgumentsError(
                "function %s is not valid. Choose on these: %s"
                % (func_name, " - ".join(valid_fns))
            )

        if func_name == "sum":
            return sum
        elif func_name == "mean":
            return statistics.mean
        else:
            return lambda vals: vals[1]

    @staticmethod
    def hash_columns(columns: List[str]):
        joined_cols = "-".join(set(columns))
        return hashlib.sha256(joined_cols.encode("utf-8")).hexdigest()

    def drop_nan_ids(self, sf: SFrame, schema: Schema):
        seen = set()
        for col in schema.get_id(return_first=False):
            if col.original in seen:
                continue
            seen.add(col.original)
            trimmer = NaNTrimmer(subset=[col.original])
            sf = trimmer(sf)
        return sf

    def calculate_complexity(self):
        return 60
