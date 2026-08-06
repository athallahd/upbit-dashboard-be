import ssl
import os
# from django.conf import settings
import MySQLdb
import logging
import pandas as pd
# from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

class db_access():
    def __init__(self, server):
        if server == 'kyc':
            self.user = 'KYC_USER'
            self.pw = 'KYC_PASSWORD'
            self.host = 'KYC_HOST'
            self.db = 'KYC_DATABASE'
            self.readcommit = False
        elif server == 'ccx':
            self.user = 'MYSQL_USER'
            self.pw = 'MYSQL_PASSWORD'
            self.host = 'MYSQL_HOST'
            self.db = 'MYSQL_DATABASE'
            self.readcommit = False
        elif server == 'cuma':
            self.user = 'CUMA_USER'
            self.pw = 'CUMA_PW'
            self.host = 'CUMA_HOST'
            self.db = 'CUMA_DB_PRO'
            self.readcommit = False
        elif server == 'django':
            self.user = 'SEC_USER'
            self.pw = 'SEC_PASSWORD'
            self.host = 'SEC_HOST'
            self.db = 'SEC_DATABASE'
            self.readcommit = False
            # self.port = 'SEC_PORT'

    def get_connection_mysqldb(self):

        conn= MySQLdb.connect(
            user=os.getenv(self.user),
            passwd=os.getenv(self.pw),
            host=os.getenv(self.host),
            db=os.getenv(self.db),
            # port=int(os.getenv(self.port)),
            # ssl={'verify_cert': False},
            ssl_mode='REQUIRED',
        )

        set_readcommit(conn, self.readcommit)
        return conn


#     def get_connection_sqlalchemy(self):
#         path = f"mysql+pymysql://{os.getenv(self.user)}:{os.getenv(self.pw)}@{os.getenv(self.host)}/{os.getenv(self.db)}"
#         ssl_context = ssl.create_default_context()
#         ssl_context.check_hostname = False
#         ssl_context.verify_mode = ssl.CERT_NONE
#         db_conn = create_engine(path, connect_args={"ssl": ssl_context})
#         conn = db_conn.connect()
#         set_readcommit(conn, self.readcommit)
#         return conn
    
#     def get_connection_sqlalchemy_engine(self):
#         path = f"mysql+pymysql://{os.getenv(self.user)}:{os.getenv(self.pw)}@{os.getenv(self.host)}/{os.getenv(self.db)}"
#         ssl_context = ssl.create_default_context()
#         ssl_context.check_hostname = False
#         ssl_context.verify_mode = ssl.CERT_NONE
#         db_conn = create_engine(path, connect_args={"ssl": ssl_context})
#         return db_conn 


# def exe_pd_insert(server, df, tablename):
#     conn = db_access(server).get_connection_sqlalchemy()
#     res = df.to_sql(tablename, con=conn, if_exists='append', index=False, chunksize = 10000)
#     conn.commit()
#     conn.close()
#     logger.info(f'Success insert table: {tablename}, rowCount: {str(res)}')
#     return res

# def exe_pd_insert_engine(server, df, tablename):
#     engine = db_access(server).get_connection_sqlalchemy_engine()
#     with engine.connect() as conn:
#         with conn.begin():
#             res = df.to_sql(tablename, con=conn, if_exists='append', index=False, chunksize=10000)
#     logger.info(f'Success insert table: {tablename}, rowCount: {str(res)}')
#     return res

# def exe_pd_sqlquery(conn, query):
#     df = pd.read_sql_query(query, conn, index_col=None, coerce_float=False)
#     conn.close()
#     return df


def exe_query(server, query):
    conn = db_access(server).get_connection_mysqldb()
    df = pd.read_sql_query(query, conn, index_col=None, coerce_float=False)
    conn.close()
    return df


def exe_update(server, query):
    conn = db_access(server).get_connection_mysqldb()
    cur = conn.cursor()
    res = cur.execute(query)
    conn.commit()
    conn.close()
    logger.info(f'Success update rowCount: {str(res)}')
    return res
    

def set_readcommit(conn, readcommit):
    if readcommit:
        curs = conn.cursor()
        curs.execute('set session aurora_read_replica_read_committed = ON')
        curs.execute('set session transaction isolation level read committed')
        curs.close()

        # conn.query('set session aurora_read_replica_read_committed = ON')
        # conn.query('set session transaction isolation level read committed')
