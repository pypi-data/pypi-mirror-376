# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from polaris.utils.database.db_utils import add_column_unless_exists


def migrate(conn):
    add_column_unless_exists(conn, "Location", "walk_setback", "REAL")
    add_column_unless_exists(conn, "Location", "bike_setback", "REAL")
    add_column_unless_exists(conn, "Parking", "walk_setback", "REAL")
    add_column_unless_exists(conn, "Parking", "bike_setback", "REAL")
