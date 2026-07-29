# PQID-Bench Stochastic Repeatability Request Manifest

- schema: `pqid-bench-stochastic-repeatability-requests-v1`
- panel prompts: `36`
- model endpoints: `21`
- observed baseline cells: `756`
- newly authorized calls: `1512`
- successful completed responses are never retried or selected by outcome
- run 2 and run 3 preserve each model's original provider payload byte-for-byte apart from trace fields outside the provider request body

## Models

| model | provider | family | payload | run-1 response |
| --- | --- | --- | --- | --- |
| `gpt-5.6-sol` | `openai` | `openai_responses` | `55042f3f06404c6a113e01bfa0f7f1f2a32d24a75f313f15f3a33dc1773e60e2` | `0838e4883e1f3d8a20d387afef6cc7591677b8be8ccf93e0f5d1803b2c8e62c4` |
| `gpt-5.5` | `openai` | `openai_responses` | `c8658a19ddcf166e23db668fd819d01b2c3fed2d9654724a170580211bb923bc` | `1b68b805cecd786c0f9b090faa036ae7c91cd43b442a2ec4c38143e87f9a82a8` |
| `gpt-5.4-mini` | `openai` | `openai_responses` | `8043bb12c8a1926f8318b052d5bd4931009ee6d2ed9e11dc81c5e32cd00e6c1e` | `145dd98f4d238a85f9aa198f1b07f35b66692a5da81168a5cde5b14c24a0cfc4` |
| `claude-fable-5` | `anthropic` | `anthropic_messages` | `72b9bddd510b970f2a80320f9d89660aa8d3488046ab88489a6eef8749b5dc69` | `1c25dec68e653d981c0a87c3ff15323b2cfdc41246682e819ee23220f82adb2e` |
| `claude-sonnet-4-6` | `anthropic` | `anthropic_messages` | `70afa548d72c6b0629ffe07e3ac9467ec1031648ab52f4e9fe7968e53e78f811` | `b7c34b0905e7b6c6dcee2c3c5c0e25cd7645ad8abf9507e0a544c2d3ffafc9fd` |
| `claude-opus-4-8` | `anthropic` | `anthropic_messages` | `bffbc8a4156b1b3c72070de4a267ce70c6ee022a00a19042294d9fcea9fb0ea7` | `23caad403fc17f50daeb664584d0496f3dba8c130ef5f8611d90b5982e269cea` |
| `gemini-2.5-pro` | `google` | `gemini_generate_content` | `a150bbd08669a8d41e599cbbe152ed80df8a0b6868ece5698df3d707e78feac0` | `d5e17f85bfe95b3056df0c103caedeb1cdfb4a184e93d41966c7a4fb26426489` |
| `gemini-3.1-pro-preview` | `google` | `gemini_generate_content` | `d801c16ce802c3aff44061f3c6d4552eb9cca615dc242ea5eb9e6de21f4011d2` | `4bf62e142896a3db0680afb02bf51c5a9e5ebf0de73e811113aad201e27f16db` |
| `deepseek-v4-pro` | `deepseek` | `openai_compatible_chat` | `f7ea00c4b62204da684439e8960816f140515fd51fa4abd9a83897c35c62d4f2` | `a9af25b0e5b4018d0ee9eeca6fb465d3e8e30fe613e277dbf05a0588da21a362` |
| `deepseek-v4-flash` | `deepseek` | `openai_compatible_chat` | `ab9ddef2280a043d5c72dfa6b0b126786075f2f17a0144e0ac885ebaf3dd41eb` | `1b227656f00df18c95803564500fad25a1ad2dc0e9d33eb609adf4bcfbad0825` |
| `mistral-ai/codestral-2501` | `github_models` | `openai_compatible_chat` | `b39adf09d2bd54f58d8d71abcd80d0cbc9e2f64393306c4c35498f31f3e9e3ce` | `456ba5bf31d16993b63ced9f131b25817dc6fd7f13170626d6a8a35a37031d6a` |
| `qwen/qwen3-coder-next` | `huggingface_router` | `openai_compatible_chat` | `769d3b1f9caa1925d159ee25ac09cbe1ccac6e00a87433ce5259fe3221fc1c01` | `86e3b48a7e625da0b862a15d8f4d8292bf78276e9084538090bb9a4ccf930b53` |
| `meta/llama-4-maverick-17b-128e-instruct-fp8` | `github_models` | `openai_compatible_chat` | `b2c043e5c04a91555c3b24a0fd6bb849d3d09c72da77e939b692c371fa6ff11d` | `32524702d78a4e0c472b5d99f68566f5eea2f34e40b66761238baaa642e23fcb` |
| `llama-3.3-70b-versatile` | `groq` | `openai_compatible_chat` | `d354be285dc29f3bdcbe5b8a8f128fdda2f91e1807d3b5b796cf20104ab79d1b` | `273d9fec439e9e877f39ed4be1686df4a60ab0ca75939c170fe06f50bd615dba` |
| `openai/gpt-oss-120b` | `groq` | `openai_compatible_chat` | `8bac69971e05d6fcccbf5833a118469d435179221a59550aa1dd1f2b1c54e06d` | `c87c7537133920d569516a306da825eb869c9d976357219943f55f0b88e0b647` |
| `openai/gpt-oss-20b` | `groq` | `openai_compatible_chat` | `6552aeaa6a4ca0299428daa967e26ff683ef955d88d5a7e86ca6a11af8dea8cf` | `f921a58926230896621376c3f55f92ea88aae3ab81134e0e0a5aceba28f9150d` |
| `mistralai/mistral-small-3.2-24b-instruct` | `openrouter` | `openai_compatible_chat` | `dc6bd606b50f478cfc400c3ffead8dced21486dfc120f09b17b69081d1d23cbb` | `b29f35972fa362830361ab3b1d79b9430baadfe5d6ef073c2f66d7c82c39373e` |
| `qiskit/mistral-small-3.2-24b-qiskit` | `huggingface_router` | `openai_compatible_completion` | `25420fd211c4e692ffc7ed14721b030f3b0d39c7726c2043f4d60e963ec5a325` | `3b0e242b5faa3335c3f9ef57ec53373881600fe0cdfdb1cb884034ef80e7d836` |
| `qwen/qwen3-32b` | `groq` | `openai_compatible_chat` | `6e036bf09a8ed607da95ab2696b7a9d857652fc3a633d4a804282c8433528d05` | `e4f465de28bd35950f92b380f93a973ddb3361a7113d2de0f56c2eb08d2fd1e8` |
| `meta-llama/llama-4-scout-17b-16e-instruct` | `groq` | `openai_compatible_chat` | `6c28742b8bb78c3983be315680ceb000c57f1bc73f577ef19020ca74031c263c` | `00a93afe70b2565f065dbf79b21981a142ec9c03c3b07e3e48347a230bee8072` |
| `llama-3.1-8b-instant` | `groq` | `openai_compatible_chat` | `59b1c68876e47caed987a883ac8e1767a7b191f6db462a237f5e1946dd4bc71d` | `42029a2e47c36a759bfd82f6539ceb6a7f48cedfb236b8434754a37c42c7973a` |

## Run Directories

| run | status | request files | response files |
| ---: | --- | ---: | ---: |
| 1 | observed canonical baseline | 21 | 21 |
| 2 | prepared for API execution | 21 | 0 |
| 3 | prepared for API execution | 21 | 0 |
