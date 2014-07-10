import datetime
import hashlib
import pickle

from familytree import storage


########################################################################
# generate_hash
########################################################################

OBJECT_TYPE = 'Object Type'


def _hash_object(normalized):
    return hashlib.sha1(
        pickle.dumps((OBJECT_TYPE.lower(), normalized))).hexdigest()


def should_hash_lowercase_string():
    hashed = storage.generate_hash(OBJECT_TYPE, {'STRING': 'Value'})
    assert hashed == _hash_object({'STRING': 'value'})


def should_descend_into_embedded_dictionaries():
    hashed = storage.generate_hash(
        OBJECT_TYPE, {'SomeDict': {'Second': 'BEEF', 'First': 'DeaD'}})
    assert hashed == _hash_object({
        'SomeDict': {'Second': 'beef', 'First': 'dead'}})


def should_hash_elements_of_a_list():
    hashed = storage.generate_hash(OBJECT_TYPE, {'blah': ['one', 2, 'Three']})
    assert hashed == _hash_object({'blah': ['one', 2, 'three']})


def should_hash_normalized_datetimes():
    now = datetime.datetime.utcnow()
    hashed = storage.generate_hash(OBJECT_TYPE, {'now': now})
    assert hashed == _hash_object({'now': now.replace(microsecond=0)})
