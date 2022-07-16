from __future__ import absolute_import
import hashlib
from pip._vendor.six import iteritems, iterkeys, itervalues
from pip._internal.exceptions import (
    HashMismatch, HashMissing, InstallationError,
)
from pip._internal.utils.misc import read_chunks
FAVORITE_HASH = 'sha256'
STRONG_HASHES = ['sha256', 'sha384', 'sha512']
class Hashes(object):
    def __init__(self, hashes=None):
        self._allowed = {} if hashes is None else hashes
    def check_against_chunks(self, chunks):
        gots = {}
        for hash_name in iterkeys(self._allowed):
            try:
                gots[hash_name] = hashlib.new(hash_name)
            except (ValueError, TypeError):
                raise InstallationError('Unknown hash name: %s' % hash_name)
        for chunk in chunks:
            for hash in itervalues(gots):
                hash.update(chunk)
        for hash_name, got in iteritems(gots):
            if got.hexdigest() in self._allowed[hash_name]:
                return
        self._raise(gots)
    def _raise(self, gots):
        raise HashMismatch(self._allowed, gots)
    def check_against_file(self, file):
        return self.check_against_chunks(read_chunks(file))
    def check_against_path(self, path):
        with open(path, 'rb') as file:
            return self.check_against_file(file)
    def __nonzero__(self):
        return bool(self._allowed)
    def __bool__(self):
        return self.__nonzero__()
class MissingHashes(Hashes):
    def __init__(self):
        super(MissingHashes, self).__init__(hashes={FAVORITE_HASH: []})
    def _raise(self, gots):
        raise HashMissing(gots[FAVORITE_HASH].hexdigest())