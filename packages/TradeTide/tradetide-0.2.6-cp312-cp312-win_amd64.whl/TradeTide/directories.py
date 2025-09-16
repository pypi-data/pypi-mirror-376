#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-

from pathlib import Path
import TradeTide

root_path = Path(TradeTide.__path__[0])

repository = project_path = Path(root_path)

doc_css_path = project_path.parent / "docs/source/_static/default.css"

data = repository / "data"

usd_eur = eur_usd = data.joinpath("eur_usd")
