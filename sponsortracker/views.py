from sponsortracker.app import app 

@app.route("/")
def home():
	return "Main page"