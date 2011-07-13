def translate_greek2latin(abstract):
    greek2latin = {u"\u03B1": "alpha", u"\u03B2": "beta", u"\u03B3": "gamma",
                   u"\u03B4": "delta", u"\u03BA": "kappa", u"\u03BB": "lambda",
                   u"\u03BB": "mu", u"\u03C3": "sigma"}

    for greek, latin in greek2latin.items():
        abstract = abstract.replace(greek,latin)

    return abstract

