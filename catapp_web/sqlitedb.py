"""Functions for performing SQL operations"""

from __future__ import unicode_literals

import json
import textwrap
import web
import numpy as np

SEARCH_DB = web.database(dbn='sqlite', db='database/catapp.db')
PLOT_DB = web.database(dbn='sqlite', db='database/catapp_index.db')
TOOL_TIP_LINE_WRAP = 25

"""
HELPER METHODS
"""


def enforceForeignKey():
    """Enforce foreign key constraints"""
    SEARCH_DB.query('PRAGMA foreign_keys = ON')


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
    return SEARCH_DB.transaction()


def query(query_string, database=None, vars=None):
    """returns results from database query as a list

    Note: if the `result' list is empty (i.e. there are no items for a
    a given ID), this will throw an Exception!

    Args:
        query_string (str)
        database (str, optional)
        vars (None, optional): Description
        vars (dict, optional)

    Returns:
        list
    """
    vars = {} if vars == None else vars
    database = SEARCH_DB if database is None else database
    return list(database.query(query_string, vars))


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


def getLinearFit(xData, yData):
    """Return linear fit parameters and a label

    Args:
        xData (list): x coordinates
        yData (list): y coordinates

    Returns:
        xFit (list)
        yFit (list)
        fitLabel (str)
    """
    xFit = []
    yFit = []
    fitLabel = ''

    if len(xData) > 1:
        m, b = np.polyfit(xData, yData, 1)

        bNew = '+ {:.2f}'.format(b) if b > 0 else ' \u2013 {:.2f}'.format(abs(b))
        mNew = '{:.2f}'.format(m) if m > 0 else ' \u2013 {:.2f}'.format(abs(m))

        fitXmin = np.min(xData)
        fitXmax = np.max(xData)

        xFit = [fitXmin, fitXmax]
        yFit = [m * fitXmin + b, m * fitXmax + b]
        fitLabel = 'Y = {} X {}'.format(mNew, bNew)

    return xFit, yFit, fitLabel


def getRawScalingData(xRxn, yRxn, outTypeX, outTypeY):
    """Get raw data and labels for plotting the scaling relation

    Args:
        xRxn (str): x-axis reaction in the form 'IS|TS|FS'
        yRxn (str): y-axis reaction in the form 'IS|TS|FS'
        outTypeX (str): 'Reaction_Energy' or 'Activation_Energy'
        outTypeY (str): 'Reaction_Energy' or 'Activation_Energy'

    Returns:
        rawData (list of dict)
    """
    Xab, Xa, Xb = xRxn.split('|')
    Yab, Ya, Yb = yRxn.split('|')

    if xRxn == yRxn:
        rawData = query(
            """
            SELECT {}, {}, Surface, Termination, Reference, Url
            FROM CatApp
            WHERE AB = '{}'
              AND A = '{}'
              AND B = '{}'
              AND {} <> ''
              AND {} <> ''
            """.format(outTypeX, outTypeY, Xab, Xa, Xb, outTypeX, outTypeY),
            database=PLOT_DB,
        )
    else:
        rawData = query(
            """
            SELECT
                a.{outTypeX} as a_{outTypeX},
                b.{outTypeY} as b_{outTypeY},
                a.Surface as Surface,
                a.Termination as Termination,
                a.Reference as a_Reference,
                a.Url as a_Url,
                b.Reference as b_Reference,
                b.Url as b_Url
            FROM CatApp AS a
            INNER JOIN (
                SELECT  {outTypeY}, Surface, Termination, Reference, Url, AB, A, B
                FROM CatApp
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
            """.format(outTypeX=outTypeX, outTypeY=outTypeY,
                       Xab=Xab, Xa=Xa, Xb=Xb,
                       Yab=Yab, Ya=Ya, Yb=Yb),
            database=PLOT_DB,
        )

    return rawData


def getRefString(rowData):
    """Generate string of literature references

    Args:
        rowRawData (dict): row of data

    Returns:
        str
    """
    # both axes are the same reaction
    if 'Reference' in rowData.keys():
        refString = '<br>'.join(textwrap.wrap(rowData['Reference'], TOOL_TIP_LINE_WRAP))
    # different reactions on each axis
    else:
        refStringA = u'\u2022 {}'.format(
            '<br>'.join(
                textwrap.wrap(rowData['a_Reference'], TOOL_TIP_LINE_WRAP)
            )
        )
        refStringB = u'\u2022 {}'.format(
            '<br>'.join(
                textwrap.wrap(rowData['b_Reference'], TOOL_TIP_LINE_WRAP)
            )
        )
        refString = '<br>'.join((refStringA, refStringB))

    return refString


def getScalingXY(xRxn, yRxn, outTypeX, outTypeY):
    """Get results for plotting scaling relations

    TODO: Refactor to abstract out certain functions

    Args:
        xRxn (str): Reaction on the X axis
        yRxn (str): Reaction on the Y axis
        outTypeX (str): 'Reaction_Energy' or 'Activation_Energy'
        outTypeY (str): 'Reaction_Energy' or 'Activation_Energy'

    Returns:
        output to render (str, str, str, str, str, str, str, str)
    """
    rawData = getRawScalingData(xRxn, yRxn, outTypeX, outTypeY)

    xData = ([float(d[outTypeX]) for d in rawData] if xRxn == yRxn
             else [float(d['a_{}'.format(outTypeX)]) for d in rawData])
    yData = ([float(d[outTypeY]) for d in rawData] if xRxn == yRxn
             else [float(d['b_{}'.format(outTypeY)]) for d in rawData])

    xLabel = '{} \u2192 {} {} (eV)'.format(*xRxn.split('|'))
    yLabel = xLabel if xRxn == yRxn else '{} \u2192 {} {} (eV)'.format(*yRxn.split('|'))

    # HACK: improperly inputted surface terminations
    for d in rawData:
        if d['Termination'] == '1':
            d['Termination'] = '0001'

    # generate data labels
    dataLabels = [
        '{}({}) <br><br>References:<br>{}'.format(d['Surface'], d['Termination'], getRefString(d))
        for d in rawData
    ]

    # get linear fit parameters
    xFit, yFit, fitLabel = getLinearFit(xData, yData)

    return (json.dumps(xData),
            json.dumps(yData),
            xLabel,
            yLabel,
            json.dumps(dataLabels),
            fitLabel,
            json.dumps(xFit),
            json.dumps(yFit))
