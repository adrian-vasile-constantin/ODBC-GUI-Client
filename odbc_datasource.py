import platform
from ctypes import (
        cdll,
        windll,
        c_bool,
        c_char,
        c_wchar,
        c_byte,
        c_ubyte,
        c_short,
        c_ushort,
        c_int,
        c_uint,
        c_long,
        c_ulong,
        c_size_t,
        c_ssize_t,
        c_float,
        c_double,
        c_longdouble,
        c_char_p,
        c_wchar_p,
        c_void_p)
import ctypes.util
from PySide6.QtWidgets import QMainWindow

class ODBCInst:
    ODBC_ADD_DSN = 1
    ODBC_CONFIG_DSN = 2
    ODBC_REMOVE_DSN = 3

    ODBC_ADD_SYS_DSN = 4
    ODBC_CONFIG_SYS_DSN = 5
    ODBC_REMOVE_SYS_DSN = 6

    ODBC_REMOVE_DEFAULT_DSN = 7

    odbcInst = None
    SQLConfigDataSource = None

    @classmethod
    def Init(cls):
        if cls.odbcInst is None:
            if platform.system() == 'Windows':
                cls.odbcInst = windll.odbccp32
            else:
                cls.odbcInst = CDLL('libodbcinst.so.2')

            # BOOL INSTAPI SQLConfigDataSourceW(HWND hwndParent, WORD fRequest, LPCWSTR lpszDriver, LPCWSTR lpszAttributes);

            cls.SQLConfigDataSource = cls.odbcInst.SQLConfigDataSourceW
            cls.SQLConfigDataSource.argtypes = [ c_void_p, c_ushort, c_wchar_p, c_wchar_p ]
            cls.SQLConfigDataSource.restype = c_int
