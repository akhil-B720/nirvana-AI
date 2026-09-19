# -*- coding: utf-8 -*-

def test_frontend_enterprise_contract():
    with open('backend/static/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Check all 15 views
    views = [
        'view-overview', 'view-projects', 'view-map', 'view-risk-monitor', 'view-reality-gap',
        'view-digital-twins', 'view-evidence', 'view-analytics', 'view-models', 'view-reports',
        'view-cases', 'view-inspections', 'view-audit', 'view-settings', 'view-credits'
    ]
    for v in views:
        assert f'id="{v}"' in html, f'Missing view {v}'

    # 2. Check all 15 nav links
    navs = [f'nav-{v.replace("view-", "")}' for v in views]
    for n in navs:
        assert f'id="{n}"' in html, f'Missing nav link {n}'

    # 3. Check prominent Reset button
    assert 'id="projectsResetBtn"' in html
    assert 'resetProjectsFilters' in html

    # 4. Check Credits & Team
    assert 'Team TYRANTS' in html
    assert 'SIH26102' in html
    assert 'MoSPI' in html
    assert 'FastAPI' in html
    assert 'ReportLab' in html

    # 5. Check No Cyberpunk / Sci-fi Clutter
    assert 'PETAL MERYC' not in html
    assert 'DATA RA TIME' not in html

    # 6. Check dual theme tokens
    assert '--canvas-bg: #f8fafc' in html  # Light mode
    assert '--canvas-bg: #090d16' in html  # Dark mode

    # 7. Check Esri Map
    assert 'server.arcgisonline.com' in html
