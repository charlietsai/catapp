#!/usr/bin/env python

import sys
sys.path.insert(0, 'lib')  # HACK: get imports to work

import os
from datetime import datetime

import web
import sqlitedb
import jinja2

"""
HELPER FUNCTIONS
"""


def string_to_time(date_str):
    """helper method to convert times from database (which will return a string)
    into datetime objects. This will allow you to compare times correctly (using
    ==, !=, <, >, etc.) instead of lexicographically as strings.

    Sample use:
    current_time = string_to_time(sqlitedb.getTime())

    Args:
        date_str (str)

    Returns:
        datetime.datetime
    """
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')


def render_template(template_name, **context):
    """helper method to render a template in the templates/ directory

    See curr_time's `GET' method for sample usage.

    Args:
        template_name (string): name of template file to render
        **context (kwargs): dictionary of variable names mapped to values that are passed to
            Jinja2's templating engine.

    Returns:
        render Jinja2 template
    """
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = jinja2.Environment(autoescape=True,
                                   loader=jinja2.FileSystemLoader(
                                       os.path.join(os.path.dirname(__file__), 'templates')
                                   ),
                                   extensions=extensions)
    jinja_env.globals.update(globals)

    web.header('Content-Type', 'text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

"""
MAIN FUNCTIONS
"""


URLS = ('/', 'search',
        '/search', 'search',
        '/plot', 'plot',
        # TODO: add additional URLs here
        # first parameter => URL, second parameter => class name
        )


class search(object):

    def GET(self):
        """Get

        Render search page

        Returns:
            render Jinja2 template
        """
        return render_template('search.html')

    def POST(self):
        """Post

        Returns:
            render Jinja2 template
        """
        key_order = ('Reaction_Energy', 'Activation_Energy', 'Surface',
                     'Termination', 'AB', 'A', 'B', 'Reference', 'Source')
        post_params = web.input()
        result = sqlitedb.getRxn(post_params['query'])
        if result:
            return render_template('search.html',
                                   search_result=result,
                                   key_order=key_order,
                                   search_query=post_params['query'])
        else:
            return render_template('search.html', search_result='empty')


class plot(object):

    def GET(self):
        """Get

        Plot default scaling relations

        Returns:
            render Jinja2 template
        """
        uniqueRxns = sqlitedb.getUniqueRxns()
        #X =  "NH3*|NH3|*"
        X = "N2|N*|N*"
        Y = "N2|N*|N*"
        defaultOutX = "Reaction_Energy"
        defaultOutY = "Activation_Energy"
        xData, yData, xLabel, yLabel, dataLabels, fitLabel, xFit, yFit = sqlitedb.getScalingXY(
            X, Y, defaultOutX, defaultOutY
        )
        return render_template('plot.html',
                               X_select=X,
                               Y_select=Y,
                               outTypeX=defaultOutX,
                               outTypeY=defaultOutY,
                               Xdata=xData,
                               Ydata=yData,
                               Xlab=xLabel,
                               Ylab=yLabel,
                               dataLabels=dataLabels,
                               Xfit=xFit,
                               Yfit=yFit,
                               fitLabel=fitLabel,
                               reactions=uniqueRxns)

    def POST(self):
        """Post

        Plot new scaling relations

        Returns:
            render Jinja2 template
        """
        uniqueRxns = sqlitedb.getUniqueRxns()
        post_params = web.input()
        xData, yData, xLabel, yLabel, dataLabels, fitLabel, xFit, yFit = sqlitedb.getScalingXY(
            post_params['X'],
            post_params['Y'],
            post_params['outTypeX'],
            post_params['outTypeY'])
        return render_template('plot.html',
                               X_select=post_params['X'],
                               Y_select=post_params['Y'],
                               outTypeX=post_params['outTypeX'],
                               outTypeY=post_params['outTypeY'],
                               Xdata=xData,
                               Ydata=yData,
                               Xlab=xLabel,
                               Ylab=yLabel,
                               dataLabels=dataLabels,
                               Xfit=xFit,
                               Yfit=yFit,
                               fitLabel=fitLabel,
                               reactions=uniqueRxns)

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(URLS, globals())
    # app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
