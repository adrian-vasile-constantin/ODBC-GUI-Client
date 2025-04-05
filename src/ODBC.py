import platform
from ctypes import (
        cdll,
        CDLL,
        POINTER,
        windll,
        sizeof,
        c_ubyte,
        c_wchar,
        c_short,
        c_ushort,
        c_int,
        c_uint,
        c_long,
        c_ulong,
        c_longlong,
        c_ulonglong,
        c_double,
        c_float,
        c_size_t,
        c_ssize_t,
        c_void_p,
        c_wchar_p)

class ODBC:
    SQL_FETCH_NEXT = 1
    SQL_FETCH_FIRST = 2
    SQL_FETCH_FIRST_USER = 31
    SQL_FETCH_FIRST_SYSTEM = 32

    SQL_NULL_HANDLE = 0
    SQL_HANDLE_ENV = 1
    SQL_HANDLE_DBC = 2
    SQL_HANDLE_STMT = 3
    SQL_HANDLE_DESC = 4

    SQL_NULL_HENV = None
    SQL_NULL_HDBC = None
    SQL_NULL_HSTMT = None
    SQL_NULL_HDESC = None

    SQLCHAR = c_ubyte
    SQLSMALLINT = c_short
    SQLINTEGER = c_long

    SQLUSMALLINT = c_ushort
    SQLUINTEGER = c_ulong

    SQLDOUBLE = c_double
    SQLFLOAT = c_double
    SQLREAL = c_float

    if sizeof(c_void_p) == 8:
        SQLLEN  = c_longlong
        SQLULEN = c_ulonglong
        SQLSETPOSIROW = c_ulonglong
    else:
        SQLLEN  = SQLINTEGER
        SQLULEN = SQLUINTEGER
        SQLSETPOSIROW = SQLUSMALLINT

    SQLRETURN = SQLSMALLINT
    SQLPOINTER = c_void_p
    SQLHANDLE = c_void_p
    SQLHENV = SQLHANDLE
    SQLHDBC = SQLHANDLE
    SQLHSTMT = SQLHANDLE
    SQLHDESC = SQLHANDLE

    odbcInst = None
    SQLAllocHandle = None
    SQLFreeHandle = None
    SQLDataSources = None

    SQL_INVALID_HANDLE = -2
    SQL_ERROR = -1
    SQL_SUCCESS = 0
    SQL_SUCCESS_WITH_INFO = 1
    SQL_STILL_EXECUTING = 2
    SQL_NEED_DATA = 99
    SQL_NO_DATA = 100
    SQL_PARAM_DATA_AVAILABLE = 101

    SQL_ATTR_ODBC_VERSION = 200
    SQL_OV_ODBC2 = 2
    SQL_OV_ODBC3 = 3
    SQL_OV_ODBC3_80 = 380

    SQL_ATTR_CONNECTION_POOLING = 201
    SQL_CP_OFF = 0
    SQL_CP_ONE_PER_DRIVER = 1
    SQL_CP_ONE_PER_HENV = 2
    SQL_CP_DRIVER_AWARE = 3
    SQL_CP_DEFAULT = SQL_CP_OFF

    SQL_ATTR_CP_MATCH = 202
    SQL_CP_STRICT_MATCH = 0
    SQL_CP_RELAXED_MATCH = 1
    SQL_CP_MATCH_DEFAULT = SQL_CP_STRICT_MATCH

    @classmethod
    def Init(cls):
        if cls.odbcInst is None:
            if platform.system() == 'Windows':
                cls.odbcInst = windll.odbc32
            else:
                cls.odbcInst = CDLL('libodbc.so.2')

            # SQLRETURN SQL_API SQLAllocHandle(SQLSMALLINT handleType, SQLHANDLE inputHandle, SQLHANDLE *outputHandlePtr);

            cls.SQLAllocHandle = cls.odbcInst.SQLAllocHandle
            cls.SQLAllocHandle.argtypes = [ cls.SQLSMALLINT, cls.SQLHANDLE, POINTER(cls.SQLHANDLE) ]
            cls.SQLAllocHandle.restype = cls.SQLRETURN

            # SQLRETURN SQL_API SQLFreeHandle(SQLSMALLINT handleType, SQLHANDLE handle);

            cls.SQLFreeHandle = cls.odbcInst.SQLFreeHandle
            cls.SQLFreeHandle.argtypes = [ cls.SQLSMALLINT, cls.SQLHANDLE ]
            cls.SQLFreeHandle.restype = cls.SQLRETURN

            # SQLRETURN SQLSetEnvAttr(SQLHENV environmentHandle, SQLINTEGER attribute, SQLPOINTER valuePtr, SQLINTEGER strlen);

            cls.SQLSetEnvAttr = cls.odbcInst.SQLSetEnvAttr
            cls.SQLSetEnvAttr.argtypes = [ cls.SQLHENV, cls.SQLINTEGER, cls.SQLPOINTER, cls.SQLINTEGER ]
            cls.SQLSetEnvAttr.restype = cls.SQLRETURN

            # SQLRETURN SQL_API SQLDataSourcesW
            #   (
            #       SQLHENV          environmentHandle,
            #       SQLUSMALLINT     direction,
            #       SQLCHAR         *dataSourceNameBuffer,
            #       SQLSMALLINT      dataSourceNameBufferSize,
            #       SQLSMALLINT     *dataSourceNameLength,
            #       SQLCHAR         *descriptionBuffer,
            #       SQLSMALLINT      descriptionBufferSize,
            #       SQLSMALLINT     *descriptionLength
            #   )

            cls.SQLDataSources = cls.odbcInst.SQLDataSourcesW
            cls.SQLDataSources.argtypes = [ cls.SQLHENV, cls.SQLUSMALLINT, c_wchar_p, cls.SQLSMALLINT, POINTER(cls.SQLSMALLINT),
                                           c_wchar_p, cls.SQLSMALLINT, POINTER(cls.SQLSMALLINT) ]
            cls.SQLDataSources.restype = cls.SQLRETURN

ODBC.Init()
