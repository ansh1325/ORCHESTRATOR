path = 'D:/LlamaOrchestrator/README.md'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Tests-143%2F143%20Passed', 'Tests-150%2F150%20Passed')
text = text.replace('143-test regression suite', '150-test regression suite')
text = text.replace('all 143 tests:', 'all 150 tests:')
text = text.replace('143 passed in ~120s', '150 passed in ~150s')

qs_target = '* `call campaign --niche "Medical Clinics" --leads 300 --target-calls 2`'
qs_replacement = """* `call campaign --niche "Medical Clinics" --leads 300 --target-calls 2`
* `builds list` (or `builds run <id>`, `builds open <id>`, `builds clean`)"""

text = text.replace(qs_target, qs_replacement)

sec8 = """
### 8. Builds & Workspaces Operating Hub (`core/build_manager.py`)
* **Central Build Registry**: Indexes, categorizes, and audits all autonomous builds, full-stack microservices, and workspaces.
* **Direct Execution Engine**: Run any build immediately (`builds run <id>`) with isolated execution environments and live stdout/stderr streaming.
* **1-Click Native Desktop Explorer**: Direct OS integration (`builds open <id>`) opens Windows File Explorer pointed directly to the workspace.
* **Safe Zero-Harm Workspace Pruner**: Prunes empty ghost directories and test artifacts (`builds clean`) while preserving core databases and datasets with zero risk."""

target_anchor = "* **Concrete Proof-of-Need**: Extracts verifiable technical bottlenecks (e.g. cold-start latency, Next.js migrations, microservice refactoring, SOC2 compliance) with observed signals and active sourcing channels."
text = text.replace(target_anchor, target_anchor + "\n" + sec8)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("README.md updated with Build Manager docs!")

