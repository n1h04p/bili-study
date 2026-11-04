# Sources and licensing

The independent QR login flow and message-normalization field mappings are adapted from:

- https://github.com/Yuuyuko-uu/dsh-bili-subagent
- Snapshot: efae852a276b7b120ca9d8ef6cd5080da3023005
- `lib/login.mjs` and `vendor/bilibili-mcp/mcp_server.py`, MIT.
- Original contributors: c1overzz, Yuuyuko-uu, AGI_Ananas.

Original license texts are included in `licenses/`.
The DSH host integration, its automatic agents, schedulers, updater and write tools are not executed.

Runtime dependencies are installed from https://pypi.org/ and recorded in ../requirements-lock.txt.
`bilibili-api-python` is a community library. This plugin is not an official Bilibili or OpenAI product.
