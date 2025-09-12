from django_vastbase_backend import base

from dj_vb_conn_pool.backends.vastbase.mixins import PGDatabaseWrapperMixin


class DatabaseWrapper(PGDatabaseWrapperMixin, base.DatabaseWrapper):
    pass
