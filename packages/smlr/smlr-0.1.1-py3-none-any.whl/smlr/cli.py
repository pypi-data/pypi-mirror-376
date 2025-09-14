import argparse
from smlr import SMLR

def cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", type=str, required=True)
    ap.add_argument("--ratio", type=int, default=4)
    args = ap.parse_args()

    SMLR.compress(args.path, args.ratio)
    
    
if __name__=="__main__":
    cli()