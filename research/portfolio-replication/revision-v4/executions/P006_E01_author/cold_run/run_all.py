"""Reproduce the UPSA paper figures from processed inputs.

    python run_all.py --main          # main-text figures
    python run_all.py --appendix      # appendix figures
    python run_all.py --simulations   # simulation figures
    python run_all.py --all           # everything (default if no flag)

By default each section reuses the cached numerical objects in
outputs/computed/ if present; pass --compute to regenerate them from the
processed panels in data/processed_inputs/.

Figures are written to outputs/figures/.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FIG_DIR = os.path.join(HERE, "outputs", "figures")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--main", action="store_true", help="main-text figures")
    ap.add_argument("--appendix", action="store_true", help="appendix figures")
    ap.add_argument("--simulations", action="store_true", help="simulation figures")
    ap.add_argument("--all", action="store_true", help="all of the above")
    ap.add_argument("--compute", action="store_true",
                    help="recompute numerical objects instead of using the cache")
    args = ap.parse_args()

    do_all = args.all or not (args.main or args.appendix or args.simulations)
    os.makedirs(FIG_DIR, exist_ok=True)
    from src.data import load_panel

    if args.main or do_all:
        from scripts.compute_main_figures import compute_main
        from scripts.plot_main_figures import plot_main
        bundle = compute_main(force=args.compute)
        plot_main(bundle, load_panel("factors_main"), FIG_DIR)

    if args.simulations or do_all:
        from scripts.compute_simulations import compute_simulations
        from scripts.plot_simulations import plot_simulations
        sim = compute_simulations(force=args.compute)
        plot_simulations(sim, FIG_DIR)

    if args.appendix or do_all:
        from scripts.compute_appendix_figures import compute_appendix
        from scripts.plot_appendix_figures import plot_appendix
        appx = compute_appendix(force=args.compute)
        plot_appendix(appx, load_panel("factors_main"), FIG_DIR)

    # Rename outputs from internal semantic names to paper-ordered names
    # (e.g. is_vs_oos.jpg -> fig_01_is_vs_oos.jpg) and refresh manifest.csv.
    from scripts.finalize_outputs import finalize
    finalize()

    print("done.")


if __name__ == "__main__":
    main()
