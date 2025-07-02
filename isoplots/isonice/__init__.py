import configparser

# TODO: This will source from isofit once the PR is accepted
try:
    from isofit.utils.wd import IsofitWD, Loaders
except:
    print("Using Isoplots for WD")
    from isoplots.isonice.utils.wd import IsofitWD, Loaders

# Globally shared single-states
Config = configparser.ConfigParser()
WD = IsofitWD(".")
