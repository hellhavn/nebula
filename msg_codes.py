# last generated 2016-08-30 02:47:27.029000
INVALID_PERMISSIONS = -11
NO_ACTIVE_HOST = -10
INVALID_STATE = -9
CLIENT_AUTH_ERROR = -8
HOST_VERIFY_CLIENT_FAILURE = -7
FILE_DOES_NOT_EXIST_ERROR = -6
FILE_IS_NOT_DIR_ERROR = -5
FILE_IS_DIR_ERROR = -4
UNPREPARED_HOST_ERROR = -3
AUTH_ERROR = -2
GENERIC_ERROR = -1
NEW_HOST = 0
ASSIGN_HOST_ID = 1
HOST_HANDSHAKE = 2
REMOTE_HANDSHAKE = 3
REM_HANDSHAKE_GO_FETCH = 4
REQUEST_CLOUD = 5
GO_RETRIEVE_HERE = 6
PREPARE_FOR_FETCH = 7
HOST_HOST_FETCH = 8
HOST_FILE_TRANSFER = 9
MAKE_CLOUD_REQUEST = 10
MAKE_CLOUD_RESPONSE = 11
MAKE_USER_REQUEST = 12
MAKE_USER_RESPONSE = 13
MIRRORING_COMPLETE = 14
GET_HOSTS_REQUEST = 15
GET_HOSTS_RESPONSE = 16
REMOVE_FILE = 18
HOST_FILE_PUSH = 19
STAT_FILE_REQUEST = 20
STAT_FILE_RESPONSE = 21
LIST_FILES_REQUEST = 22
LIST_FILES_RESPONSE = 23
READ_FILE_REQUEST = 24
READ_FILE_RESPONSE = 25
CLIENT_SESSION_REQUEST = 26
CLIENT_SESSION_ALERT = 27
CLIENT_SESSION_RESPONSE = 28
CLIENT_FILE_PUT = 29
CLIENT_FILE_TRANSFER = 30
CLIENT_GET_CLOUDS_REQUEST = 31
CLIENT_GET_CLOUDS_RESPONSE = 32
CLIENT_GET_CLOUD_HOST_REQUEST = 33
CLIENT_GET_CLOUD_HOST_RESPONSE = 34
GET_ACTIVE_HOSTS_REQUEST = 35
GET_ACTIVE_HOSTS_RESPONSE = 36
CLIENT_MIRROR = 37
CLIENT_GET_CLOUD_HOSTS_REQUEST = 38
CLIENT_GET_CLOUD_HOSTS_RESPONSE = 39
HOST_VERIFY_CLIENT_REQUEST = 40
HOST_VERIFY_CLIENT_SUCCESS = 41


def send_unprepared_host_error_and_close(socket):
    pass
    # FIXME


def send_generic_error_and_close(socket):
    pass
    # FIXME
