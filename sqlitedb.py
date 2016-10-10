import web
import json
from numpy import polyfit, min, max

DATABASE = web.database(dbn='sqlite', db='catapp.db')


"""
HELPER METHODS
"""


def enforceForeignKey():
    """Enforce foreign key constraints"""
    DATABASE.query('PRAGMA foreign_keys = ON')


def transaction():
    """initiates a transaction on the database

    Sample usage:

        t = sqlitedb.transaction()
        try:
            sqlitedb.query('[FIRST QUERY STATEMENT]')
            sqlitedb.query('[SECOND QUERY STATEMENT]')
        except Exception as e:
            t.rollback()
            print str(e)
        else:
            t.commit()

    check out http://webpy.org/cookbook/transactions for examples

    wrapper method around web.py's db.query method
    check out http://webpy.org/cookbook/query for more info
    """
    return DATABASE.transaction()


def query(query_string, vars={}):
    """returns results from database query as a list

    Note: if the `result' list is empty (i.e. there are no items for a
    a given ID), this will throw an Exception!

    Args:
        query_string (str)
        vars (dict, optional)

    Returns:
        list
    """
    return list(DATABASE.query(query_string, vars))


def getRxn(search_query):
    """Free text search

    Args:
        search_query (str)

    Returns:
        list
    """
    query_string = """
        SELECT * FROM CatApp WHERE CatApp MATCH '{}' ORDER BY Surface
        """.format(search_query)
    return query(query_string)


def getUniqueRxns():
    """Get all unique reactions

    Returns:
        list
    """
    return query("SELECT DISTINCT AB, A, B FROM CatAPP ORDER BY AB")


def getScalingXY(X_rxn, Y_rxn, outTypeX, outTypeY):
    """Get results for plotting scaling relations

    Args:
        X_rxn (str): Reaction on the X axis
        Y_rxn (str): Reaction on the Y axis
        outTypeX (str): Reaction type, either
        outTypeY (TYPE): Description

    Returns:
        TYPE: Description
    """
    Xab = X_rxn.split("|")[0]
    Xa = X_rxn.split("|")[1]
    Xb = X_rxn.split("|")[2]
    xLabel = "{} \u2192 {} {} (eV)".format(Xab, Xa, Xb)

    if X_rxn == Y_rxn:
        rawData = query(
            """
            SELECT {}, {}, Surface, Termination FROM CatApp 
            WHERE AB = '{}' and A = '{}' and B = '{}'
            AND {} <> '' AND {} <> ''
            """.format(outTypeX, outTypeY, Xab, Xa, Xb, outTypeX, outTypeY)
        )
        yLabel = xLabel
        xData = [float(d[outTypeX]) for d in rawData]
        yData = [float(d[outTypeY]) for d in rawData]
    else:
        Yab = Y_rxn.split("|")[0]
        Ya = Y_rxn.split("|")[1]
        Yb = Y_rxn.split("|")[2]
        yLabel = "{} \u2192 {} {} (eV)".format(Yab, Ya, Yb)

        rawData = query(
            """
            SELECT
                a.{outTypeX} as a_{outTypeX},
                b.{outTypeY} as b_{outTypeY},
                a.Surface as Surface,
                a.Termination as Termination
            FROM CatApp AS a
            INNER JOIN (
                SELECT  {outTypeY}, Surface, Termination, AB, A, B FROM CatApp
            ) AS b
            ON (
                (a.AB = '{Xab}' and a.A = '{Xa}' and a.B = '{Xb}')
                OR
                (a.AB = '{Xab}' and a.B = '{Xa}' and a.A = '{Xb}')
            )
            AND (
                (b.AB = '{Yab}' and b.A = '{Ya}' and b.B = '{Yb}')
                OR
                (b.AB = '{Yab}' and b.B = '{Ya}' and b.A = '{Yb}')
            )
            AND a.Surface = b.Surface
            AND a.Termination = b.Termination
            AND a.{outTypeX} <> ''
            AND b.{outTypeY} <> ''
            """.format(outTypeX=outTypeX,
                       outTypeY=outTypeY,
                       Xab=Xab,
                       Xa=Xa,
                       Xb=Xb,
                       Yab=Yab,
                       Ya=Ya,
                       Yb=Yb)
        )

        xData = [float(d['a_' + outTypeX]) for d in rawData]
        yData = [float(d['b_' + outTypeY]) for d in rawData]

    for d in rawData:
        if d['Termination'] == '1':
            d['Termination'] = '0001'

    dataLabels = ["{}({})".format(d['Surface'], d['Termination']) for d in rawData]

    if len(xData) > 1:
        m, b = polyfit(xData, yData, 1)
        if b > 0:
            b_new = "+ {:.2f}".format(b)
        else:
            b_new = " \u2013 {:.2f}".format(abs(b))
        if m > 0:
            m_new = "{:.2f}".format(m)
        else:
            m_new = " \u2013 {:.2f}".format(abs(m))

        fitLabel = "Y = {} X {}".format(m_new, b_new)
        fit_xmin = min(xData)
        fit_xmax = max(xData)
        xFit = [fit_xmin, fit_xmax]
        yFit = [m * fit_xmin + b, m * fit_xmax + b]
    else:
        xFit = []
        yFit = {}
        fitLabel = ''

    return (json.dumps(xData),
            json.dumps(yData),
            xLabel,
            yLabel,
            json.dumps(dataLabels),
            fitLabel,
            json.dumps(xFit),
            json.dumps(yFit))
