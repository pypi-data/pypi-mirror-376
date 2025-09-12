def test_imports():
    import joepie_tools
    from joepie_tools.hackerprank import fake_bsod, fake_update_screen, fake_virus_scan, random_popups, run_full_prank
    assert hasattr(joepie_tools, "__version__")
