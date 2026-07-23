The final picking validation triggered from process_data is opt-in.

Validating the picking by default turns an import step into a
workflow-orchestration step and introduces non-obvious side effects.
Implicitly calling validation also breaks command/query separation and can make
integration flows less predictable and less idempotent.

The default picking validation was introduced in version 16.0:
[f9a4c0f#diff-ba317b47ca5c669f7eb8f157d21581ec7a424e672eccfdf785c0cf2dc97517aaR191](https://github.com/OCA/edi/commit/f9a4c0f39164b1e89c3f014bad6140f5570dbf53#diff-ba317b47ca5c669f7eb8f157d21581ec7a424e672eccfdf785c0cf2dc97517aaR191)
It was removed from the base module and made opt-in in version 19.0.

By default, the wizard only applies despatch advice data and does not validate
the picking.

To enable it for a single execution, pass this context key when calling
process_data:
- despatch_advice_import__picking_validation=True
