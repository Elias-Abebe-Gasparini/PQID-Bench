# PQID-Bench Stochastic Repeatability Augmentation

- schema: `pqid-bench-stochastic-repeatability-augmentation-v1`
- selection seed: `13523d72ec07fde91188178f214ae9c9558ae6d8f07baa097dd89a53c14e048b`
- seed derivation: `sha256('pqid-bench-stochastic-repeatability-augmentation-v1' + NUL + base_panel_sha256)`
- original panel prompts: `36`
- augmentation prompts: `36`
- combined prompts: `72`
- combined unique reference signatures: `72`
- augmentation SHA-256: `9f36bdfabbfe53d0b719e95961d84cf50bb38c21a8dbbaf01d047416dfe241b0`
- combined SHA-256: `3e242bf2d8db9e4deda76a1a62c06484949ff245e8aa6284c64948e51c4049ed`

The augmentation was selected without consulting any model outcome. It excludes
the original panel's reference signatures and the four prespecified
prompt-identifiability exceptions. A deterministic seeded allocation adds 12
prompts per gate-diversity band and 18 prompts per benchmark cohort. Cross-stratum
counts are kept as close to six as the remaining unique-signature pool permits,
and barrier representation is balanced against the original panel whenever the
candidate pool permits.

## Combined Margins

| margin | count |
| --- | ---: |
| gate types `1-2` | 24 |
| gate types `3-4` | 24 |
| gate types `5+` | 24 |
| cohort `pilot` | 36 |
| cohort `extension` | 36 |

## Augmentation Strata

| gate-type bin | cohort | available | selected | barrier | no barrier |
| --- | --- | ---: | ---: | ---: | ---: |
| `1-2` | `pilot` | 11 | 7 | 0 | 7 |
| `1-2` | `extension` | 17 | 5 | 0 | 5 |
| `3-4` | `pilot` | 25 | 6 | 3 | 3 |
| `3-4` | `extension` | 37 | 6 | 3 | 3 |
| `5+` | `pilot` | 5 | 5 | 5 | 0 |
| `5+` | `extension` | 9 | 7 | 4 | 3 |

## Added Prompts

| prompt | cohort | gate-type bin | barrier | signature SHA-256 |
| --- | --- | --- | --- | --- |
| `pqid_bench_external_gen_0002` | `pilot` | `5+` | yes | `8203e9f0d1177c3b1498aab7097a4f372fbad61b9113fe656a1f5caf5fd0ceef` |
| `pqid_bench_external_gen_0006` | `pilot` | `1-2` | no | `bde1f8a42be0d3de9102ef2959cff9b11da52aed0e39f3ed75f2c3ca92523dab` |
| `pqid_bench_external_gen_0012` | `pilot` | `3-4` | no | `60aa698a4e3538f6f60431e932469a8a682aa072bc49776bedee9a28b6372e42` |
| `pqid_bench_external_gen_0013` | `pilot` | `1-2` | no | `cee59e0188dc348b5ce778e91f0bbc722892a67eedf264d7672b9c4f68d16ea2` |
| `pqid_bench_external_gen_0017` | `pilot` | `1-2` | no | `7dd1c8eaf6e455cc3e4a5e6ab6268dc03ceee7c2f82d170c30eaf72bdf70a2e5` |
| `pqid_bench_external_gen_0019` | `pilot` | `3-4` | no | `8d99cab7c7e0176a0ff89f38f96991e2699918d7328c5e77128ec715bf6d174e` |
| `pqid_bench_external_gen_0023` | `pilot` | `3-4` | yes | `885057498f6a155035a30cd60e2fa19d90dd86ad01bb61da2392753f88095595` |
| `pqid_bench_external_gen_0024` | `pilot` | `3-4` | yes | `e87ab55ad5e69a511933bc889232d5d6141e46fd5bf61322a9dd3532707336c1` |
| `pqid_bench_external_gen_0027` | `pilot` | `1-2` | no | `1718b3912eecdc32c906f3df8cec55dda32c892c8481873a14551756ffdf7d19` |
| `pqid_bench_external_gen_0031` | `pilot` | `3-4` | yes | `6d6a8628f07facbf0ac189b963f2cd3bfd4a6815d6f52813b3b7862bb0f6c2ce` |
| `pqid_bench_external_gen_0037` | `pilot` | `1-2` | no | `586e9a26093d0f808ee86c156eea793ac98607586b32d1a91e752b66c4c36fe4` |
| `pqid_bench_external_gen_0038` | `pilot` | `5+` | yes | `c01f19ab461cd8b2c662306182d25e707ae1a323b096c963906bc3f635d198e4` |
| `pqid_bench_external_gen_0041` | `pilot` | `1-2` | no | `1891b1deaeaefb2c831b9adeb6033f458c3513016a2d207830f1470fdb52325b` |
| `pqid_bench_external_gen_0046` | `pilot` | `5+` | yes | `4fb6f0b5417697903c2ca1f0a74d7fa398791092b38ddd8c218fd29651aaa8a8` |
| `pqid_bench_external_gen_0050` | `pilot` | `5+` | yes | `871de4845d89b067dd5154e50be7ec293724d0fffff19f3209c8936d673fe6ba` |
| `pqid_bench_external_gen_0052` | `pilot` | `5+` | yes | `3d1d70dfae6e93d359eab46a1a9979a1c1fd0828871fbf81151c98cd628dabbc` |
| `pqid_bench_external_gen_0057` | `pilot` | `1-2` | no | `e952554ad209e96e1d7f3596e2822584ee773fe4881399fc90311141331afc3d` |
| `pqid_bench_external_gen_0068` | `pilot` | `3-4` | no | `860896c54131b8747cb1eb122318c8e5e46479bd73a7ace3041192792a2a8c11` |
| `pqid_bench_external_gen_0073` | `extension` | `1-2` | no | `7e3966f8e44a2ea987ec35e1de16051e8fc2e4a8a847c26fdc0094826de2a24b` |
| `pqid_bench_external_gen_0074` | `extension` | `5+` | no | `d6285ef991dad83e23463fc6437a2dc319d5722a775f05d9c1502d3550ccf1e8` |
| `pqid_bench_external_gen_0077` | `extension` | `1-2` | no | `a07a237dfa7847c1d238dbb691334bd6b6d6ebe056f16b1497e46120853eb960` |
| `pqid_bench_external_gen_0079` | `extension` | `5+` | yes | `3265b1c72d7daeca8301dd7441ea4b3ffc023e326697ddde9a4ef8a07b13b128` |
| `pqid_bench_external_gen_0083` | `extension` | `3-4` | no | `9377188d2eeb92461be8864be35e3d013958bd3070c2e1fe76f2056febb62dd9` |
| `pqid_bench_external_gen_0085` | `extension` | `3-4` | no | `70fada9c8c2769dfeb8f113cbea32709914ec3c4ab106e1cb52b98cbf8ca19de` |
| `pqid_bench_external_gen_0106` | `extension` | `5+` | no | `643863331df2e8a2b5e8c6071562fbcea228ab2a4897c95b153cefc336441166` |
| `pqid_bench_external_gen_0111` | `extension` | `1-2` | no | `b536c0e716112b0b5dd281676af14150c28f58db7aea2400e42061ef400c15fe` |
| `pqid_bench_external_gen_0114` | `extension` | `1-2` | no | `f91cba6b9df6c7e3b316ef07936165324e4c3f41962159be13f63ff49abcda51` |
| `pqid_bench_external_gen_0116` | `extension` | `1-2` | no | `ed2d1f25376f2386114b923cc89c670301c6f9cc331f3868518033182dbdbd9b` |
| `pqid_bench_external_gen_0118` | `extension` | `3-4` | yes | `f1bf21757cc524181cc15459975f17e67e604898502ba32337ae3bd7e9c1d1a5` |
| `pqid_bench_external_gen_0124` | `extension` | `3-4` | yes | `9803aeed4291e3c7580298160199242db7899c14a8faf229747e0f555a969805` |
| `pqid_bench_external_gen_0131` | `extension` | `5+` | yes | `34fbe058d919802a9cde76493b605c1cf9bd12c78d285cc6cd1755ba77d7b86a` |
| `pqid_bench_external_gen_0136` | `extension` | `5+` | yes | `3cfcaeb64b382cf3ba1dfddd76c4e47ce65576ee023ea9a4fed8b0bbca4d586c` |
| `pqid_bench_external_gen_0137` | `extension` | `3-4` | yes | `a3c54e605367a4f4fff47a0d059c4555058c927a18475f1340c0e8644990e544` |
| `pqid_bench_external_gen_0140` | `extension` | `5+` | yes | `a4de17668eb352e61ec39b14655fe9ffb0e5daadc1e566660b9467a8d3c7e255` |
| `pqid_bench_external_gen_0143` | `extension` | `5+` | no | `ed60220f9e3eca7e7c3912a939a3dcc7512121ed75a5a69b89923a4de3401275` |
| `pqid_bench_external_gen_0147` | `extension` | `3-4` | no | `6dc7f440b558962fa5942d4a0fcf48be0e8cf3820f3dc4892c6e89772517e28f` |
