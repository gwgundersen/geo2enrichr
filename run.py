# This is only for development.
#
# In production, Flask is run by mod_wsgi, which imports the via wsgi.py.


from g2e import app
app.run(debug=True, port=8083, host='0.0.0.0')