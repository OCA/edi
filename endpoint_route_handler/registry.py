# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import importlib
import json
from functools import partial

from psycopg2 import sql
from psycopg2.extras import execute_values

from odoo import http, tools
from odoo.tools import DotDict

from odoo.addons.base.models.ir_model import query_insert

from .exceptions import EndpointHandlerNotFound


def query_multi_update(cr, table_name, rows, cols):
    """Update multiple rows at once.

    :param `cr`: active db cursor
    :param `table_name`: sql table to update
    :param `rows`: list of dictionaries with write-ready values
    :param `cols`: list of keys representing columns' names
    """
    # eg: key=c.key, route=c.route
    keys = sql.SQL(",").join([sql.SQL("{0}=c.{0}".format(col)) for col in cols])
    col_names = sql.SQL(",").join([sql.Identifier(col) for col in cols])
    template = (
        sql.SQL("(")
        + sql.SQL(",").join([sql.SQL("%({})s".format(col)) for col in cols])
        + sql.SQL(")")
    )
    query = sql.SQL(
        """
    UPDATE {table} AS t SET
        {keys}
    FROM (VALUES {values})
        AS c({col_names})
    WHERE c.key = t.key
    RETURNING t.key
    """
    ).format(
        table=sql.Identifier(table_name),
        keys=keys,
        col_names=col_names,
        values=sql.Placeholder(),
    )
    execute_values(
        cr,
        query.as_string(cr._cnx),
        rows,
        template=template.as_string(cr._cnx),
    )


class EndpointRegistry:
    """Registry for endpoints.

    Used to:

    * track registered endpoints
    * retrieve routing rules to load in ir.http routing map
    """

    __slots__ = "cr"
    _table = "endpoint_route"
    _columns = (
        # name, type, comment
        ("key", "VARCHAR", ""),
        ("route", "VARCHAR", ""),
        ("opts", "text", ""),
        ("routing", "text", ""),
        ("endpoint_hash", "VARCHAR(32)", ""),
        ("route_group", "VARCHAR(32)", ""),
        ("updated_at", "TIMESTAMP NOT NULL DEFAULT NOW()", ""),
    )

    @classmethod
    def registry_for(cls, cr):
        return cls(cr)

    @classmethod
    def wipe_registry_for(cls, cr):
        cr.execute("TRUNCATE endpoint_route")

    @classmethod
    def _setup_table(cls, cr):
        if not tools.sql.table_exists(cr, cls._table):
            tools.sql.create_model_table(cr, cls._table, columns=cls._columns)
            tools.sql.create_unique_index(
                cr,
                "endpoint_route__key_uniq",
                cls._table,
                [
                    "key",
                ],
            )
            tools.sql.add_constraint(
                cr,
                cls._table,
                "endpoint_route__endpoint_hash_uniq",
                "unique(endpoint_hash)",
            )

            cr.execute(
                """
                CREATE OR REPLACE FUNCTION endpoint_route_set_timestamp()
                    RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """
            )
            cr.execute(
                """
                CREATE TRIGGER trigger_endpoint_route_set_timestamp
                BEFORE UPDATE ON endpoint_route
                FOR EACH ROW
                EXECUTE PROCEDURE endpoint_route_set_timestamp();
            """
            )

    def __init__(self, cr):
        self.cr = cr

    def get_rules(self, keys=None, where=None):
        for row in self._get_rules(keys=keys, where=where):
            yield EndpointRule.from_row(self.cr.dbname, row)

    def _get_rules(self, keys=None, where=None, one=False):
        query = "SELECT * FROM endpoint_route"
        pargs = ()
        if keys and not where:
            query += " WHERE key IN %s"
            pargs = (tuple(keys),)
        elif where:
            query += " " + where
        self.cr.execute(query, pargs)
        return self.cr.fetchone() if one else self.cr.fetchall()

    def _get_rule(self, key):
        row = self._get_rules(keys=(key,), one=True)
        if row:
            return EndpointRule.from_row(self.cr.dbname, row)

    def _lock_rows(self, keys):
        sql = "SELECT id FROM endpoint_route WHERE key IN %s FOR UPDATE"
        self.cr.execute(sql, (tuple(keys),), log_exceptions=False)

    def _update(self, rows_mapping):
        self._lock_rows(tuple(rows_mapping.keys()))
        return query_multi_update(
            self.cr,
            self._table,
            tuple(rows_mapping.values()),
            EndpointRule._ordered_columns(),
        )

    def _create(self, rows_mapping):
        return query_insert(self.cr, self._table, list(rows_mapping.values()))

    def get_rules_by_group(self, group):
        rules = self.get_rules(where=f"WHERE route_group='{group}'")
        return rules

    def update_rules(self, rules, init=False):
        """Add or update rules.

        :param rule: list of instances of EndpointRule
        :param force: replace rules forcedly
        :param init: given when adding rules for the first time
        """
        keys = [x.key for x in rules]
        existing = {x.key: x for x in self.get_rules(keys=keys)}
        to_create = {}
        to_update = {}
        for rule in rules:
            if rule.key in existing:
                to_update[rule.key] = rule.to_row()
            else:
                to_create[rule.key] = rule.to_row()
        res = False
        if to_create:
            self._create(to_create)
            res = True
        if to_update:
            self._update(to_update)
            res = True
        return res

    def drop_rules(self, keys):
        self.cr.execute("DELETE FROM endpoint_route WHERE key IN %s", (tuple(keys),))
        return True

    def make_rule(self, *a, **kw):
        return EndpointRule(self.cr.dbname, *a, **kw)

    def last_update(self):
        self.cr.execute(
            """
            SELECT updated_at
            FROM endpoint_route
            ORDER BY updated_at DESC
            LIMIT 1
        """
        )
        res = self.cr.fetchone()
        if res:
            return res[0].timestamp()
        return 0.0


class EndpointRule:
    """Hold information for a custom endpoint rule."""

    __slots__ = (
        "_dbname",
        "key",
        "route",
        "opts",
        "endpoint_hash",
        "routing",
        "route_group",
    )

    def __init__(
        self, dbname, key, route, options, routing, endpoint_hash, route_group=None
    ):
        self._dbname = dbname
        self.key = key
        self.route = route
        self.options = options
        self.routing = routing
        self.endpoint_hash = endpoint_hash
        self.route_group = route_group

    def __repr__(self):
        # FIXME: use class name, remove key
        return (
            f"<{self.__class__.__name__}: {self.key}"
            + (f" #{self.route_group}" if self.route_group else "nogroup")
            + ">"
        )

    @classmethod
    def _ordered_columns(cls):
        return [k for k in cls.__slots__ if not k.startswith("_")]

    @property
    def options(self):
        return DotDict(self.opts)

    @options.setter
    def options(self, value):
        """Validate options.

        See `_get_handler` for more info.
        """
        assert "klass_dotted_path" in value["handler"]
        assert "method_name" in value["handler"]
        self.opts = value

    @classmethod
    def from_row(cls, dbname, row):
        key, route, options, routing, endpoint_hash, route_group = row[1:-1]
        # TODO: #jsonb-ref
        options = json.loads(options)
        routing = json.loads(routing)
        init_args = (
            dbname,
            key,
            route,
            options,
            routing,
            endpoint_hash,
            route_group,
        )
        return cls(*init_args)

    def to_dict(self):
        return {k: getattr(self, k) for k in self._ordered_columns()}

    def to_row(self):
        row = self.to_dict()
        for k, v in row.items():
            if isinstance(v, (dict, list)):
                row[k] = json.dumps(v)
        return row

    @property
    def endpoint(self):
        """Lookup http.Endpoint to be used for the routing map."""
        handler = self._get_handler()
        pargs = self.handler_options.get("default_pargs", ())
        kwargs = self.handler_options.get("default_kwargs", {})
        method = partial(handler, *pargs, **kwargs)
        return http.EndPoint(method, self.routing)

    @property
    def handler_options(self):
        return self.options.handler

    def _get_handler(self):
        """Resolve endpoint handler lookup.

        `options` must contain `handler` key to provide:

            * the controller's klass via `klass_dotted_path`
            * the controller's method to use via `method_name`

        Lookup happens by:

            1. importing the controller klass module
            2. loading the klass
            3. accessing the method via its name

        If any of them is not found, a specific exception is raised.
        """
        mod_path, klass_name = self.handler_options.klass_dotted_path.rsplit(".", 1)
        try:
            mod = importlib.import_module(mod_path)
        except ImportError as exc:
            raise EndpointHandlerNotFound(f"Module `{mod_path}` not found") from exc
        try:
            klass = getattr(mod, klass_name)
        except AttributeError as exc:
            raise EndpointHandlerNotFound(f"Class `{klass_name}` not found") from exc
        method_name = self.handler_options.method_name
        try:
            method = getattr(klass(), method_name)
        except AttributeError as exc:
            raise EndpointHandlerNotFound(
                f"Method name `{method_name}` not found"
            ) from exc
        return method
