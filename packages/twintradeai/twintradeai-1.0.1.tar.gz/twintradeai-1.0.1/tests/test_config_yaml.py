import pytest 
import yaml
import twintradeai.lint_config as lint


def test_lint_detects_and_fixes(tmp_path):
    # config ที่หาย field
    cfg = {"EURUSDc": {}}
    f = tmp_path / "config.symbols.yaml"
    with open(f, "w") as fp:
        yaml.safe_dump(cfg, fp)

    # lint with autofix
    errors, warnings, fixes = lint.lint_config(str(f), auto_fix=True)
    assert not errors  # auto-fix ต้องแก้หมด
    with open(f) as fp:
        fixed = yaml.safe_load(fp)
    assert "confidence_min" in fixed["EURUSDc"]
    assert "strategies" in fixed["EURUSDc"]
    assert "scalp" in fixed["EURUSDc"]["strategies"]
