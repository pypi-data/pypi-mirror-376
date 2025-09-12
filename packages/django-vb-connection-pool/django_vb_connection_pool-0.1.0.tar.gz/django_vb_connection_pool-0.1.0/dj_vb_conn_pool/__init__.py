__version__ = '0.1.0'
__author__ = 'wangxiaoyang'
__author_email__ = 'yayaxxww@163.com'
__description__ = 'Persistent vastbase connection backends for Django'

def setup(**kwargs):
    from dj_db_conn_pool.core import pool_container

    for key, value in kwargs.items():
        if key in pool_container.pool_default_params:
            pool_container.pool_default_params[key] = value