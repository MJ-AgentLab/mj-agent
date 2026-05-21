"""scripts.sdd — SDD validator package.

Phase M2 + Q-A7 augmentation: enable `from scripts.sdd._common import ...` for
shared module/AST parsing logic across 6 validator scripts. Empty until
`_common/` subpackage lands (current decision: defer until validator 2-3 prove
the duplication; see check_python_contracts.py docstring).
"""

__all__: list[str] = []
