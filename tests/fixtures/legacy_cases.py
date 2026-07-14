"""The legacy parser/evaluator records, without translating their oracle.

The objects are deliberately re-exported rather than serialized: this keeps the
original AST instances and exception classes authoritative while pytest proves
that the extracted case boundaries still agree with the legacy harness.
"""

from tests.fixtures.legacy_harness import t_eval_kit, t_parse_kit


PARSER_CASES = tuple(t_parse_kit)
EVALUATOR_CASES = tuple(t_eval_kit[:-1])
EVALUATOR_SENTINEL = t_eval_kit[-1]

# SHA-256 of the AST repr produced by CPython 3.11.15 before evaluation.  The
# legacy equality implementation intentionally aliases a few node subclasses,
# so these digests make that otherwise-loose oracle structurally exact.
PARSER_AST_SHA256 = (
    "4cdac37b09b5fd6652c6b637851e7591de047e4556080b81a710773f98d78e17",
    "c3b7e69567f9756de90fe42cd2bba2cd8c943f413359e565e5d50b5d9933e08e",
    "93a04d346fe0b8b519a13ff8f714483a630e2ee453ac44a8674c74872c478df6",
    "0381308da592e5f949a89832ec9aab053b0116967a4293b6dc55909bbd76f25b",
    "9413a7d4a27918b97486b3ac2cb4cb8136e6a3f88c30414f67500b246ef1a057",
    "3cd21ef3aa24726f33c695bfec8baf4a8c01ff441a84c5d8e3f521fccf9d2abc",
    "d879849b3727a80cdb388d3921460ce48cd3633bbd6ae4606f436b09c4316c0f",
    "a4babf89671040275d0e0d5715f470ceddd64ba78be449ca92f53efefadbd6ed",
)

EVALUATOR_AST_SHA256 = (
    "e53e9a6a5b0e2c9abb034196035e08149d91d3610ba8fb139e0480abb2ff07cb",
    "f85cab8a95ac101abe4c3435bb9bb1beb3c547290ae99a2b11fdc9a0f1b734f0",
    "c47cfbae0e4403b261eece3833b8e56f1fdd88bb788d87c078a5ca9055098334",
    "b973f9d38e7bba8af719d14a19dc5a4dc5ad260d42cd2eee8c4b847aecd4c1ff",
    "95da040f9f772d38549b1e6bd0e930cb37204e7ec35f40f210eb239e6498cba9",
    "1eac43c6fecc5071fe73f065313033afe2f72c8c0a8abf4114afd0a202ecf7fc",
    "ca10c6517a1e48b733a890a6e6545f39ddf636a4959538d9d6b8a86ec3d13528",
    "e3389923a238cdff0dceeda24f2817604340d2207a7cad7de207cf46f12ad7fb",
    "ae7da01a04f87332e139bf9f061c94e4f5edaf9fcd2fc86e3642b2ae0481667c",
    "7a259922f891e6828e73a52273f5bdb477815e6f8d3c4ce7b8dd64f84a027673",
    "e80a7217b804348a1159a7b8642b65eb926fcf80a3039350e9bd53f97dd530dc",
    "dec65db5f54fc205f1b3539e46ddd17a4dd54a3c5bbfb551b8d0a31114419f0e",
    "c55f8bf92a064713a113a536f84e1108075cc26c8a83001002f5accc5317203b",
)

assert len(PARSER_CASES) == 8
assert len(EVALUATOR_CASES) == 13
assert not EVALUATOR_SENTINEL[1].strip()
