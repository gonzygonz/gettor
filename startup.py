from gettor import create_app
import sys

debug = len(sys.argv) > 1
app = create_app()
app.run(debug=debug)