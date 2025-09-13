import string

import pytest
import base58
from hypothesis import (
    given,
    strategies as st,
)
from morphys import ensure_unicode
import multibase
from multibase.multibase import ENCODINGS
import multicodec
import multihash

from cid import CIDv0, CIDv1, from_string, is_cid, make_cid

ALLOWED_ENCODINGS = [encoding for encoding in ENCODINGS if encoding.code != b"\x00"]


@pytest.fixture(scope="session")
def test_hash():
    data = b"hello world"
    return multihash.digest(data, "sha2-256").encode()


class TestCIDv0:
    @pytest.fixture
    def cid(self, test_hash):
        return CIDv0(test_hash)

    def test_init(self, cid, test_hash):
        """#__init__: initializes all the attributes correctly"""
        assert cid.version == 0
        assert cid.codec == CIDv0.CODEC
        assert cid.multihash == test_hash

    def test_buffer(self, cid, test_hash):
        """.buffer: is computed properly"""
        assert cid.buffer == test_hash

    def test_encode(self, cid):
        """#encode: base58 encodes the buffer by default"""
        assert cid.encode() == b"QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4"

    def test_str(self, cid):
        assert str(cid) == ensure_unicode(cid.encode())


class TestCIDv1:
    TEST_CODEC = "dag-pb"

    @pytest.fixture
    def cid(self, test_hash):
        return CIDv1(self.TEST_CODEC, test_hash)

    def test_init(self, cid, test_hash):
        """#__init__: attributes are set properly"""
        assert cid.version == 1
        assert cid.codec == self.TEST_CODEC
        assert cid.multihash == test_hash

    def test_buffer(self, cid):
        """.buffer: buffer is computed properly"""
        buffer = cid.buffer
        assert buffer[0] == 1
        assert buffer[1:] == multicodec.add_prefix(self.TEST_CODEC, cid.multihash)

    def test_encode_default(self, cid):
        """#encode defaults to base58btc encoding"""
        assert cid.encode() == b"zdj7WhuEjrB52m1BisYCtmjH1hSKa7yZ3jEZ9JcXaFRD51wVz"

    @pytest.mark.parametrize("codec", ENCODINGS)
    def test_encode_encoding(self, cid, codec):
        """#encode uses the encoding provided for encoding"""
        assert cid.encode(codec.encoding) == multibase.encode(codec.encoding, cid.buffer)

    def test_str(self, cid):
        assert str(cid) == ensure_unicode(cid.encode())


class TestCID:
    def test_cidv0_eq_cidv0(self, test_hash):
        """Check for equality for CIDv0 for same hash"""
        assert CIDv0(test_hash) == make_cid(CIDv0(test_hash).encode())

    def test_cidv0_neq(self):
        """Check for inequality for CIDv0 for different hashes"""
        assert CIDv0(b"QmdfTbBqBPQ7VNxZEYEj14VmRuZBkqFbiwReogJgS1zR1n") != CIDv0(
            b"QmdfTbBqBPQ7VNxZEYEj14VmRuZBkqFbiwReogJgS1zR1o",
        )

    def test_cidv0_eq_cidv1(self, test_hash):
        """Check for equality between converted v0 to v1"""
        assert CIDv0(test_hash).to_v1() == CIDv1(CIDv0.CODEC, test_hash)

    def test_cidv1_eq_cidv0(self, test_hash):
        """Check for equality between converted v1 to v0"""
        assert CIDv1(CIDv0.CODEC, test_hash).to_v0() == CIDv0(test_hash)

    def test_cidv1_to_cidv0_no_dag_pb(self, test_hash):
        """Converting non dag-pb CIDv1 should raise an exception"""
        with pytest.raises(ValueError, match="can only be converted for codec"):
            CIDv1("base2", test_hash).to_v0()

    @pytest.mark.parametrize(
        "test_cidv0",
        [
            "QmbWqxBEKC3P8tqsKc98xmWNzrzDtRLMiMPL8wBuTGsMnR",
            "QmUNLLsPACCz1vLxQVkXqqLX5R1X345qqfHbsf67hvA3Nn",
        ],
    )
    def test_is_cidv0_valid(self, test_cidv0):
        assert is_cid(test_cidv0)
        assert is_cid(make_cid(test_cidv0).encode())

    @given(hash_str=st.text(alphabet=list(string.ascii_letters + string.digits)))
    def test_make_cid(self, hash_str):
        # This test generates random text that may not be valid CIDs
        # We expect it to either be a valid CID or fail gracefully
        from contextlib import suppress

        with suppress(ValueError, KeyError):
            is_cid(hash_str)

    @pytest.mark.parametrize(
        "test_cidv1",
        [
            "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
            "bafkreigh2akiscaildcqabsyg3dfr6chu3fgpregiymsck7e7aqa4s52zy",
            "zb2rhk6GMPQF3hfzwXTaNYFLKomMeC6UXdUt6jZKPpeVirLtV",
        ],
    )
    def test_is_cidv1_valid(self, test_cidv1):
        assert is_cid(test_cidv1)
        assert is_cid(make_cid(test_cidv1).encode())

    @pytest.mark.parametrize(
        "test_data",
        [
            "!",
            "a",
            "1",
            "foobar",
            b"foobar",
            multibase.encode("base58btc", b"foobar"),
        ],
    )
    def test_is_cid_invalid(self, test_data):
        assert not is_cid(test_data)


class TestMakeCID:
    def test_base_encoded_hash(self, test_hash):
        """make_cid: make_cid works with base-encoded hash"""
        assert make_cid(base58.b58encode(test_hash)) == CIDv0(test_hash)

    def test_multibase_hash(self, test_hash):
        """make_cid: make_cid works with multibase-encoded hash"""
        cidstr = CIDv1("dag-pb", test_hash).encode()
        assert make_cid(cidstr) == CIDv1("dag-pb", test_hash)

    @pytest.mark.parametrize(
        "value",
        [
            1,
            1.0,
            object(),
            3 + 2j,
            [],
        ],
    )
    def test_hash_invalid_type(self, value):
        """make_cid: make_cid does not work if first argument is not a str or byte"""
        with pytest.raises(ValueError, match="expected: str or byte"):
            make_cid(value)

    @pytest.mark.parametrize("version", list(range(2, 5)))
    def test_version_invalid(self, version):
        """make_cid: make_cid does not work if version is not 0 or 1"""
        with pytest.raises(ValueError, match="version should be 0 or 1"):
            make_cid(version, "dag-pb", b"multihash")

    def test_codec_invalid(self):
        """make_cid: make_cid does not work if codec is invalid"""
        with pytest.raises(ValueError, match="invalid codec"):
            make_cid(1, "some-random-codec", b"multihash")

    @pytest.mark.parametrize(
        "value",
        [
            1,
            1.0,
            object(),
            3 + 2j,
            [],
        ],
    )
    def test_multihash_invalid(self, value):
        """make_cid: make_cid does not work if multihash type is invalid"""
        with pytest.raises(ValueError, match="invalid type for multihash"):
            make_cid(1, "dag-pb", value)

    def test_version_0_invalid_codec(self):
        """make_cid: make_cid does not work if version 0 has incorrect codec"""
        with pytest.raises(ValueError, match="codec for version 0"):
            make_cid(0, "raw", b"multihash")

    def test_invalid_arguments(self):
        """make_cid: make_cid does not work if bad arguments are passed"""
        with pytest.raises(ValueError, match="invalid number of arguments"):
            make_cid(1, 2, 3, 4)


class TestFromString:
    @pytest.fixture
    def cidv0(self, test_hash):
        return CIDv0(test_hash)

    @pytest.fixture
    def cidv1(self, test_hash):
        return CIDv1("dag-pb", test_hash)

    @pytest.mark.parametrize("codec", ALLOWED_ENCODINGS)
    def test_multibase_encoded_hash(self, cidv1, codec):
        """from_string: works for multibase-encoded strings"""
        assert from_string(cidv1.encode(codec.encoding)) == cidv1

    def test_cid_raw(self, cidv1):
        """from_string: works for raw cidbytes"""
        assert from_string(cidv1.buffer) == cidv1

    def test_base58_encoded_hash(self, cidv0):
        """from_string: works for base58-encoded strings"""
        assert from_string(cidv0.encode()) == cidv0

    def test_invalid_base58_encoded_hash(self):
        with pytest.raises(ValueError, match="multihash is not a valid base58 encoded multihash"):
            from_string("!!!!")

    @pytest.mark.parametrize("value", ["", "a"])
    def test_invalid_length_zero(self, value):
        with pytest.raises(ValueError, match="argument length can not be zero"):
            from_string(value)

    def test_invalid_cid_length(self):
        with pytest.raises(ValueError, match="cid length is invalid"):
            from_string("011111111")
