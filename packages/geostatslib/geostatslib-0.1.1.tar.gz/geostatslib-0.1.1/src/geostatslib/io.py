import pandas as pd

def read_gslib(filename):
    """Read a GSLIB file into a pandas DataFrame."""
    with open(filename, 'r') as f:
        title = f.readline().strip()
        nvar = int(f.readline().strip())
        varnames = [f.readline().strip() for _ in range(nvar)]

    df = pd.read_csv(
        filename,
        skiprows=nvar + 2,
        sep=r'\s+',
        names=varnames,
        engine='python'
    )
    return title, df


def write_gslib(filename, title, df):
    """Write a pandas DataFrame to GSLIB format."""
    with open(filename, 'w') as f:
        f.write(f"{title}\n")
        f.write(f"{df.shape[1]}\n")
        for col in df.columns:
            f.write(f"{col}\n")
        df.to_csv(f, sep=" ", index=False, header=False)