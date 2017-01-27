"""
PrivateData is the model that backs .nebs data.

This provides an abstraction layer on top of otherwise plain .json data
"""
import base64
import uuid

from common_util import mylog, ResultAndData, get_path_elements
import os
import json

# Fuck all this versioning shit, it's trash and I hate that I even started it
CURRENT_MAJOR_VERSION = 0
CURRENT_MINOR_VERSION = 0

MAJ_VER_KEY = 'major_version'
MIN_VER_KEY = 'minor_version'
LINKS_KEY = 'links'
GROUPS_KEY = 'groups'
FILES_KEY = 'files'

NO_ACCESS = 0
READ_ACCESS = 1
WRITE_ACCESS = 2
RDWR_ACCESS = READ_ACCESS | WRITE_ACCESS
SHARE_ACCESS = 4
FULL_ACCESS = SHARE_ACCESS | WRITE_ACCESS | READ_ACCESS

PUBLIC_ID = 0
OWNERS_ID = 1
FIRST_GROUP_ID = 2

class Group(object):
    def __init__(self, id, name, user_ids):
        self.id = id
        self._user_ids = user_ids
        self.name = name

    def has_user(self, user_id):
        # type: (int) -> bool
        return user_id in self._user_ids

    def add_user(self, user_id):
        if not self.has_user(user_id):
            self._user_ids.append(user_id)

    def is_public(self):
        return self._user_ids == []

    def to_serializable(self):
        return {
            'id': self.id
            , 'name': self.name
            , 'user_ids': self._user_ids
        }

    def from_serializable(self, obj):
        self.id = obj['id']
        self._user_ids = obj['user_ids']
        self.name = obj['name']


def make_public_group():
    return Group(PUBLIC_ID, 'public', [])


def make_owners_group(owner_ids):
    # type: ([int]) -> Group
    return Group(OWNERS_ID, 'owners', owner_ids)


class Link(object):
    def __init__(self, path, user_ids, access):
        self._path = path
        self._user_ids = user_ids
        self._access = access
        guid = uuid.uuid4()
        guid64 = base64.urlsafe_b64encode(guid.bytes)
        self.id = guid64

    def has_user(self, user_id):
        return self.is_public() or (user_id in self._user_ids)

    # fixme no user.id, only user_id
    def add_user(self, user_id):
        if not self.has_user(user_id):
            self._user_ids.append(user_id)

    def is_public(self):
        return self._user_ids == []

    def to_serializable(self):
        return {
            'path': self._path
            , 'user_ids': self._user_ids
            , 'access': self._access
            , 'id': self.id
        }

    def from_serializable(self, obj):
        self._path = obj['path']
        self._user_ids = obj['user_ids']
        self._access = obj['access']
        self.id = obj['id']


class FilePermissions(object):
    def __init__(self, path):
        self._groups = {}  # gid->permission mappings
        self._users = {}  # uid->permission mappings
        self._filepath = path  # the cloud relative path

    def add_user(self, user_id, permissions):
        # type: (int, int) -> ResultAndData
        rd = ResultAndData(False, None)
        if user_id in self.get_user_ids():
            old_perm = self._users[str(user_id)]
            self._users[str(user_id)] = permissions
            rd = ResultAndData(True, old_perm)
        else:
            self._users[str(user_id)] = permissions
            rd = ResultAndData(True, None)
        return rd

    def add_group(self, group_id, permissions):
        # type: (int, int) -> ResultAndData
        rd = ResultAndData(False, None)
        if group_id in self.get_group_ids():
            old_perm = self._groups[str(group_id)]
            self._groups[str(group_id)] = permissions
            rd = ResultAndData(True, old_perm)
        else:
            self._groups[str(group_id)] = permissions
            rd = ResultAndData(True, None)
        return rd

    def get_group_ids(self):
        # type: () -> [int]
        return [int(gid) for gid in self._groups.keys()]

    def get_user_ids(self):
        # type: () -> [int]
        return [int(uid) for uid in self._users.keys()]

    def get_user_permissions(self, user_id):
        # type: (int) -> int
        if user_id in self.get_user_ids():
            return self._users[str(user_id)]
        return NO_ACCESS

    def get_group_permissions(self, group_id):
        # type: (int) -> int
        if group_id in self.get_group_ids():
            return self._groups[str(group_id)]
        return NO_ACCESS

    def to_serializable(self):
        return {
            'path': self._filepath
            , 'groups': self._groups
            , 'users': self._users
        }

    def from_serializable(self, obj):
        self._filepath = obj['path']
        self._groups = obj['groups']
        self._users = obj['users']


class PrivateData(object):
    def __init__(self, cloud, owner_ids):
        # self._cloud = cloud
        self._cloud_id = cloud.id
        self._cloud_root = cloud.root_directory
        self._version = (CURRENT_MAJOR_VERSION, CURRENT_MINOR_VERSION)
        self._links = []
        self._groups = [make_public_group(), make_owners_group(owner_ids)]
        self._files = {}
        self._next_group_id = FIRST_GROUP_ID
        # try reading the .nebs from the cloud.
        # if it doesn't exist, then write out the defaults.
        if self._file_exists():
            mylog('Reading .nebs for cloud: '
                  '[{}]"{}"'.format(cloud.my_id_from_remote, cloud.name))
            rd = self.read_backend()
            if rd.success:
                mylog('read backend data')
                self.read_json(rd.data)
            else:
                mylog('Error reading backend data: {}'.format(rd.data))
                raise Exception  # todo:fixme
        else:
            if owner_ids is None:
                mylog('We\'re creating the .nebs for the cloud, but we '
                      'specified no owners. \n'
                      'This will prevent anyone from accessing this cloud. \n'
                      'This is likely a programming error. \n'
                      'Make sure when the cloud is mirrored, we gave it \n'
                      'owner_ids, and that if this file accidentally gets \n'
                      'deleted, we recover it intelligently.', '31')
                # assert?
            mylog('Creating .nebs for cloud: '
                  '[{}]"{}"'.format(cloud.my_id_from_remote, cloud.name))
            root_path = os.path.join(cloud.root_directory, './')

            root_path = os.path.normpath(root_path)
            root_path = os.path.relpath(root_path, cloud.root_directory)
            root_perms = FilePermissions(root_path)
            root_perms.add_group(OWNERS_ID, FULL_ACCESS)
            self._files[root_path] = root_perms
            self.commit()

    def get_group(self, group_id):
        for g in self._groups:
            if g.id == group_id:
                return g
        return None

    def get_permissions(self, user_id, filepath):
        """
        HEY DUMBASS. Make sure you normalize the path before here.
        Get rid of trailing slashes on dirs. Make sure it's actually in the
        cloud's tree. stuff like that.
        Don't pass in the full local path. Pass in the corrected, relative path.
        :param user_id:
        :param filepath:
        :return:
        """
        # break the path into elements, start from the root, work down
        path_elems = get_path_elements(filepath)
        # make sure to always use the cloud root.
        if path_elems[0] != '.':
            path_elems.insert(0, '.')
        i = 0
        curr_path = '.' # self._cloud.root_directory
        current_perms = NO_ACCESS
        while i < len(path_elems) and current_perms < RDWR_ACCESS:
            curr_path = os.path.join(curr_path, path_elems[i])
            curr_path = os.path.normpath(curr_path)
            mylog('checking {}\'s perms for {}'.format(user_id, curr_path))
            if curr_path in self._files:
                file_perms = self._files[curr_path]
                new_perms = self._file_get_permissions(user_id, file_perms)
                current_perms |= new_perms
            i += 1
        return current_perms

    def has_owner(self, user_id):
        owners_group = self.get_group(OWNERS_ID)
        if owners_group is not None:
            return owners_group.has_user(user_id)
        else:
            mylog('There is no owners group for this cloud. This is likely a programming error', '31')
        return False

    def add_owner(self, user_id):
        if not self.has_owner(user_id):
            owners_group = self.get_group(OWNERS_ID)
            if owners_group is not None:
                owners_group.add_user(user_id)
            else:
                mylog('There is no owners group for this cloud. This is likely a programming error', '31')

    def add_user_permission(self, new_user_id, rel_path, new_perms):
        mylog('add_user_permission')
        mylog('{}'.format(self._files))
        if rel_path in self._files:
            file_perms = self._files[rel_path]
        else:
        # if file_perms is None:
            mylog('Making new FilePermissions object')
            file_perms = FilePermissions(rel_path)
        mylog(file_perms.__dict__)
        file_perms.add_user(new_user_id, new_perms)
        mylog(file_perms.__dict__)
        self._files[rel_path] = file_perms
        mylog('{}'.format(self._files))

    def _file_get_permissions(self, user_id, file_permissions):
        # type: (int, FilePermissions) -> int
        perms = NO_ACCESS
        for gid in file_permissions.get_group_ids():
            group = self.get_group(gid)
            if group is not None:
                if group.has_user(user_id):
                    group_perms = file_permissions.get_group_permissions(gid)
                    perms |= group_perms
                    if perms == RDWR_ACCESS:
                        return perms

        if user_id in file_permissions.get_user_ids():
            perms |= file_permissions.get_user_permissions(user_id)

        return perms

    def delete_paths(self, paths):
        result = False
        for path in paths:
            if path in self._files.keys():
                result = True
                self._files.pop(path)
        return result

    def commit(self):
        """
        Writes out the PrivateData to the .nebs backing.
        Similar to db.session.commit(), so that a series of changes chan be
        saved atomically, if any subset of those changes would be invalid.
        """
        # this probably will have more logic in the future.
        rd = self.write_backend(self.export_v0())
        return rd

    def read_json(self, json_string):
        rd = ResultAndData(False, None)
        try:
            json_obj = json.loads(json_string)
            if MAJ_VER_KEY not in json_string:
                raise ValueError

            maj_ver = json_obj[MAJ_VER_KEY]
            if maj_ver == 0:
                rd = self.read_v0(json_obj)
            else:
                message = 'Failed to decode .nebs data with invalid version ' \
                          '{}'.format(maj_ver)
                mylog(message, '31')
                rd = ResultAndData(False, message)

        except ValueError, e:
            mylog('ERROR: Failed to decode json data', '31')
            rd = ResultAndData(False, e)

        return rd

    def read_v0(self, json_obj):
        """
        Reads v0 json data into this structure.
        :return:
        """
        rd = ResultAndData(False, None)

        new_links = []
        for link in json_obj[LINKS_KEY]:
            new_link = Link(None, [], NO_ACCESS)
            new_link.from_serializable(link)
            new_links.append(new_link)
        self._links = new_links

        new_groups = []
        for group in json_obj[GROUPS_KEY]:
            new_group = Group(0, '', [])
            new_group.from_serializable(group)
            new_groups.append(new_group)
            if new_group.id > self._next_group_id:
                self._next_group_id = new_group.id + 1
        self._groups = new_groups

        new_files = {}
        for file in json_obj[FILES_KEY]:
            new_file = FilePermissions(None)
            new_file.from_serializable(file)
            new_files[new_file._filepath] = new_file
        self._files = new_files

        rd = ResultAndData(True, None)
        return rd

    def write_backend(self, data):
        rd = ResultAndData(False, None)
        try:
            path = self._file_location()
            out_file = open(path, mode='w')
            out_file.write(data)
            out_file.close()
            # mylog('Wrote backend for [{}]"{}"'.format(
            #     self._cloud.my_id_from_remote, self._cloud.name), '32')
            rd = ResultAndData(True, None)
        except IOError, e:
            rd = ResultAndData(False, e)
            mylog(e)
        return rd

    def read_backend(self):
        rd = ResultAndData(False, None)
        try:
            path = self._file_location()
            in_file = open(path, mode='r')
            data = in_file.read()
            rd = ResultAndData(True, data)
        except IOError, e:
            rd = ResultAndData(False, e)
        return rd

    def export_v0(self):
        obj = {
            MAJ_VER_KEY: self._version[0]
            , MIN_VER_KEY: self._version[1]
            , LINKS_KEY: [link.to_serializable() for link in self._links]
            , GROUPS_KEY: [group.to_serializable() for group in self._groups]
            , FILES_KEY: [file.to_serializable() for file in self._files.values()]
        }
        return json.dumps(obj, indent=2)

    def _file_location(self):
        cloud_root = self._cloud_root
        return os.path.join(cloud_root, '.nebs')

    def _file_exists(self):
        path = self._file_location()
        return os.path.exists(path)

    def get_next_group_id(self):
        id = self._next_group_id
        self._next_group_id += 1
        return id


