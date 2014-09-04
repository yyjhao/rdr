from api.app import app
import base.config as config

app.debug = config.debug
app.config['SECRET_KEY'] = config.SECRET_KEY
app.run(host='127.0.0.1')