def main():
    # delegate to the real CLI if the core is installed
    from bgm_toolkit.cli import main as _main
    _main()
