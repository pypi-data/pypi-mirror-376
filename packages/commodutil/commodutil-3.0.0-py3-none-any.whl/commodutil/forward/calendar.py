import pandas as pd
from commodutil.forward.util import convert_columns_to_date
from commodutil import dates


def cal_contracts(contracts, col_format=None):
    """
    Given a dataframe of daily values for monthly contracts (eg Brent Jan 15, Brent Feb 15, Brent Mar 15)
    with columns headings as '2020-01-01', '2020-02-01'
    Return a dataframe of cal values (eg Cal15)
    """

    # remove attrs as they cause issues in pandas 2
    if hasattr(contracts, 'attrs'):
        contracts.attrs = {}


    contracts = convert_columns_to_date(contracts)
    years = list(set([x.year for x in contracts.columns]))

    dfs = []
    for year in years:
        s = contracts[[x for x in contracts.columns if x.year == year]].dropna(
            how="all", axis=1
        )
        if len(s.columns) == 12:  # only do if we have full set of contracts
            s = s.mean(axis=1)
            if col_format is not None:
                if col_format == "%Y":
                    s.name = year
            else:
                s.name = "CAL {}".format(year)
            dfs.append(s)
        elif (
                year == dates.curyear and len(s.columns) > 0
        ):  # sometimes current year passed in has less than 12 columns but should be included
            s = s.mean(axis=1)
            if col_format is not None:
                if col_format == "%Y":
                    s.name = year
            else:
                s.name = "CAL {}".format(year)
            dfs.append(s)

    if not dfs:
        return pd.DataFrame()

    res = pd.concat(dfs, axis=1)
    # sort columns by years
    cols = list(res.columns)
    cols.sort(key=lambda s: int(s.split()[1]) if isinstance(s, str) else s)
    res = res[cols]
    return res


def cal_spreads(q, col_format=None):
    """
    Given a dataframe of cal contract values (eg CAL 2015, CAL 2020)
    with columns headings as 'CAL 2015', 'CAL 2020'
    Return a dataframe of cal spreads (eg CAL 2015-2016)
    """

    calspr = []
    for col in q.columns:
        # colcal = col.split(' ')[0]
        colcalyr = col.split(" ")[1]

        curyear = int(colcalyr)
        nextyear = curyear + 1

        colcalnextyr = "CAL %s" % (nextyear)
        if colcalnextyr in q.columns:
            r = q[col] - q[colcalnextyr]
            if col_format:
                if col_format == "%Y":
                    r.name = curyear
            else:
                r.name = "CAL {}-{}".format(curyear, nextyear)
            calspr.append(r)

    if len(calspr) > 0:
        res = pd.concat(calspr, axis=1, sort=True)
        return res


def half_year_contracts(contracts):
    """
    Given a dataframe of daily values for monthly contracts (eg Brent Jan 15, Brent Feb 15, Brent Mar 15)
    with columns headings as '2020-01-01', '2020-02-01'
    Return a dataframe of half year values (eg H115)
    :param contracts:
    :return:
    """
    contracts = convert_columns_to_date(contracts)
    years = list(set([x.year for x in contracts.columns]))

    dfs = []
    for year in years:
        c1, c2, c3, c4, c5, c6 = (
            "{}-01-01".format(year),
            "{}-02-01".format(year),
            "{}-03-01".format(year),
            "{}-04-01".format(year),
            "{}-05-01".format(year),
            "{}-06-01".format(year),
        )
        if (
                c1 in contracts.columns
                and c2 in contracts.columns
                and c3 in contracts.columns
                and c4 in contracts.columns
                and c5 in contracts.columns
                and c6 in contracts.columns
        ):
            s = (
                pd.concat(
                    [
                        contracts[c1],
                        contracts[c2],
                        contracts[c3],
                        contracts[c4],
                        contracts[c5],
                        contracts[c6],
                    ],
                    axis=1,
                )
                .dropna(how="any")
                .mean(axis=1)
            )
            s.name = "H1 {}".format(year)
            dfs.append(s)
        c7, c8, c9, c10, c11, c12 = (
            "{}-07-01".format(year),
            "{}-08-01".format(year),
            "{}-09-01".format(year),
            "{}-10-01".format(year),
            "{}-11-01".format(year),
            "{}-12-01".format(year),
        )
        if (
                c7 in contracts.columns
                and c8 in contracts.columns
                and c9 in contracts.columns
                and c10 in contracts.columns
                and c11 in contracts.columns
                and c12 in contracts.columns
        ):
            s = (
                pd.concat(
                    [
                        contracts[c7],
                        contracts[c8],
                        contracts[c9],
                        contracts[c10],
                        contracts[c11],
                        contracts[c12],
                    ],
                    axis=1,
                )
                .dropna(how="any")
                .mean(axis=1)
            )
            s.name = "H2 {}".format(year)
            dfs.append(s)
        # Winter
        c1, c2, c3, c10, c11, c12 = (
            "{}-01-01".format(year + 1),
            "{}-02-01".format(year + 1),
            "{}-03-01".format(year + 1),
            "{}-10-01".format(year),
            "{}-11-01".format(year),
            "{}-12-01".format(year),
        )
        if (
                c1 in contracts.columns
                and c2 in contracts.columns
                and c3 in contracts.columns
                and c10 in contracts.columns
                and c11 in contracts.columns
                and c12 in contracts.columns
        ):
            s = (
                pd.concat(
                    [
                        contracts[c1],
                        contracts[c2],
                        contracts[c3],
                        contracts[c10],
                        contracts[c11],
                        contracts[c12],
                    ],
                    axis=1,
                )
                .dropna(how="any")
                .mean(axis=1)
            )
            s.name = "Winter {}".format(year)
            dfs.append(s)
            # Summer
            c4, c5, c6, c7, c8, c9 = (
                "{}-04-01".format(year),
                "{}-05-01".format(year),
                "{}-06-01".format(year),
                "{}-07-01".format(year),
                "{}-08-01".format(year),
                "{}-09-01".format(year),
            )
            if (
                    c4 in contracts.columns
                    and c5 in contracts.columns
                    and c6 in contracts.columns
                    and c7 in contracts.columns
                    and c8 in contracts.columns
                    and c9 in contracts.columns
            ):
                s = (
                    pd.concat(
                        [
                            contracts[c4],
                            contracts[c5],
                            contracts[c6],
                            contracts[c7],
                            contracts[c8],
                            contracts[c9],
                        ],
                        axis=1,
                    )
                    .dropna(how="any")
                    .mean(axis=1)
                )
                s.name = "Summer {}".format(year)
                dfs.append(s)

    res = pd.concat(dfs, axis=1)
    # sort columns by years
    cols = list(res.columns)
    cols.sort(key=lambda s: s.split()[1])
    res = res[cols]
    return res


def half_year_spreads(q):
    """
    Given a dataframe of half year values (eg Brent H115, Brent H215, Brent H116)
    with columns headings as 'H1 2015', 'H2 2015'
    Return a dataframe of half year spreads (eg H1-H2 15, H2-H1 15)

    """

    half_year_spread = []
    for col in q.columns:
        colhx = col.split(" ")[0]
        colhxyr = col.split(" ")[1]
        if colhx == "H2":
            colhxyr = int(colhxyr) + 1
        colqy = f"H2 {colhxyr}" if colhx == "H1" else f"H1 {colhxyr}"
        if colqy in q.columns:
            r = q[col] - q[colqy]
            r.name = "{}{} {}".format(colhx, colqy.split(" ")[0], col.split(" ")[1])
            half_year_spread.append(r)

    for col in q.columns:
        colhx = col.split(" ")[0]
        colhxyr = col.split(" ")[1]
        if colhx == "Summer":
            colqy = f"Winter {colhxyr}"
            if colqy in q.columns:
                r = q[col] - q[colqy]
                r.name = "{}{} {}".format(colhx, colqy.split(" ")[0], col.split(" ")[1])
                half_year_spread.append(r)
        if colhx == "Winter":
            colqy = f"Summer {int(colhxyr) + 1}"
            if colqy in q.columns:
                r = q[col] - q[colqy]
                r.name = "{}{} {}".format(colhx, colqy.split(" ")[0], col.split(" ")[1])
                half_year_spread.append(r)

    res = pd.concat(half_year_spread, axis=1, sort=True)
    return res
