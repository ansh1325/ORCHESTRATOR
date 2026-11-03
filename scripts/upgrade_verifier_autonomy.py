import sys
from pathlib import Path

# 1. Update lead_verifier.py
lv_path = Path(r"D:\LlamaOrchestrator\core\lead_verifier.py")
content = lv_path.read_text(encoding="utf-8")
content = content.replace("dynamic_lead_hunter.deduce_lead_strategy(niche)", "dynamic_lead_hunter.deduce_strategy(niche)")
lv_path.write_text(content, encoding="utf-8")

# 2. Add alias in dynamic_lead_hunter.py
dlh_path = Path(r"D:\LlamaOrchestrator\core\dynamic_lead_hunter.py")
dlh_content = dlh_path.read_text(encoding="utf-8")
if "deduce_lead_strategy = deduce_strategy" not in dlh_content:
    dlh_content = dlh_content.replace(
        "    deduce_strategy = classmethod(deduce_strategy)",
        "    deduce_strategy = classmethod(deduce_strategy)\n    deduce_lead_strategy = deduce_strategy"
    )
    if "deduce_lead_strategy = deduce_strategy" not in dlh_content:
        dlh_content += "\nDynamicLeadHunter.deduce_lead_strategy = DynamicLeadHunter.deduce_strategy\n"
    dlh_path.write_text(dlh_content, encoding="utf-8")

print("Fixed deduce_strategy in both files!")
