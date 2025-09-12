# django-vb-connection-pool

:star: If this project is helpful to you, please light up the star, Thank you:smile:

Vastbase connection pool components for Django,
Be based on [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy).
Works fine in multiprocessing and multithreading django project.

* [中文版](README_CN.md)

## Quickstart

### Installation

Install with `pip`:

```bash
$ pip install django-vb-connection-pool
```

### Update settings.DATABASES

#### PostgreSQL

change `django.db.backends.postgresql` to `dj_vb_conn_pool.backends.vastbase`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'dj_vb_conn_pool.backends.vastbase'
    }
}
```

#### Pool options(optional)

you can provide additional options to pass to SQLAlchemy's pool creation, key's name is `POOL_OPTIONS`:

```python
DATABASES = {
    'default': {
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 10,
            'RECYCLE': 24 * 60 * 60
        }
    }
}
```

`django-db-connection-pool` has more configuration options
here: [PoolContainer.pool_default_params](https://github.com/altairbow/django-db-connection-pool/blob/master/dj_db_conn_pool/core/__init__.py#L13-L20)

Here's the explanation of these options(from SQLAlchemy's Doc):

* **pool_size**: The size of the pool to be maintained,
  defaults to 5. This is the largest number of connections that
  will be kept persistently in the pool. Note that the pool
  begins with no connections; once this number of connections
  is requested, that number of connections will remain.
  `pool_size` can be set to 0 to indicate no size limit; to
  disable pooling, use a :class:`~sqlalchemy.pool.NullPool`
  instead.

* **max_overflow**: The maximum overflow size of the
  pool. When the number of checked-out connections reaches the
  size set in pool_size, additional connections will be
  returned up to this limit. When those additional connections
  are returned to the pool, they are disconnected and
  discarded. It follows then that the total number of
  simultaneous connections the pool will allow is pool_size +
  `max_overflow`, and the total number of "sleeping"
  connections the pool will allow is pool_size. `max_overflow`
  can be set to -1 to indicate no overflow limit; no limit
  will be placed on the total number of concurrent
  connections. Defaults to 10.

* **recycle**: If set to a value other than -1, number of seconds
  between connection recycling, which means upon checkout,
  if this timeout is surpassed the connection will be closed
  and replaced with a newly opened connection.
  Defaults to -1.

Or, you can use dj_db_conn_pool.setup to change default arguments(for each pool's creation), before using database pool:

```python
import dj_vb_conn_pool

dj_vb_conn_pool.setup(pool_size=100, max_overflow=50)
```

#### multiprocessing environment

In a multiprocessing environment, such as uWSGI, each process will have its own `dj_db_conn_pool.core:pool_container`
object,
It means that each process has an independent connection pool, for example:
The `POOL_OPTIONS` configuration of database `db1` is`{ 'POOL_SIZE': 10, 'MAX_OVERFLOW': 20 }`,
If uWSGI starts 8 worker processes, then the total connection pool size of `db1`  is `8 * 10`,
The maximum number of connections will not exceed `8 * 10 + 8 * 20`
