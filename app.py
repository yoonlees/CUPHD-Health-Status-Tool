import os

from flask import Flask, render_template, request, g, abort, redirect, url_for
from flask_login import (
     LoginManager,
     login_user,
     login_required,
     logout_user,
     current_user
)
from oic import rndstr
from oic.oic import Client
from oic.oic.message import AuthorizationResponse, RegistrationResponse, ClaimsRequest, Claims
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.utils.http_util import Redirect

from REDCap_connection import set_REDCap_status
from access_control_connection import lookup_access_status
from user import User

app = Flask(__name__)
app.secret_key = os.urandom(24)

# OIDC setting
app.config.from_pyfile('config.py', silent=True)

# create oidc client
client = Client(client_authn_method=CLIENT_AUTHN_METHOD)

# get authentication provider details by hitting the issuer URL
provider_info = client.provider_config(app.config["ISSUER_URL"])

# store registration details
info = {
     "client_id": app.config["CLIENT_ID"],
     "client_secret": app.config["CLIENT_SECRET"],
     "redirect_uris": app.config["REDIRECT_URIS"]
}
client_reg = RegistrationResponse(**info)
client.store_registration_info(client_reg)

session = dict()

# LOGIN management setting
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(netid):
     return User.get(netid)


@app.teardown_appcontext
def close_connection(exception):
     conn = getattr(g, '_database', None)
     if conn is not None:
          conn.close()


@app.route('/login')
def login():
     session['state'] = rndstr()
     session['nonce'] = rndstr()

     # setup claim request
     claims_request = ClaimsRequest(
          userinfo = Claims(uiucedu_uin={"essential": True})
     )

     args = {
          "client_id": client.client_id,
          "response_type": "code",
          "scope": app.config["SCOPES"],
          "nonce": session["nonce"],
          # "redirect_uri":client.registration_response["redirect_uris"][0],
          "redirect_uri":app.config["REDIRECT_URIS"],
          "state":session["state"],
          "claims":claims_request
     }

     auth_req = client.construct_AuthorizationRequest(request_args=args)
     login_url = auth_req.request(client.authorization_endpoint)

     return Redirect(login_url)


@app.route('/callback')
def callback():
     response = request.environ["QUERY_STRING"]

     authentication_response = client.parse_response(AuthorizationResponse, info=response, sformat="urlencoded")

     code = authentication_response["code"]
     assert authentication_response["state"] == session["state"]

     args = {
          "code": code
     }

     token_response = client.do_access_token_request(state=authentication_response["state"], request_args=args,
                                                     authn_method="client_secret_basic")

     user_info = client.do_user_info_request(state=authentication_response["state"])
     if user_info["preferred_username"] in app.config["ADMIN_NETID_LIST"]:
          user = User(netid=user_info["preferred_username"])
          login_user(user)
          return redirect(url_for("homepage"))
     else:
          abort(403, "This is an CUPHD administrator only tool. Your NETID need to be preapproved!")


@app.route('/logout')
@login_required
def logout():
     logout_user()
     return "You have successfully logged out!"


@app.route('/', methods=['GET'])
def homepage():
     if current_user.is_authenticated:
          user = current_user.display_name
          return render_template('homepage.html', user=user)
     else:
          return redirect(url_for("login"))


@app.route('/search', methods=['POST'])
def search():
     if current_user.is_authenticated:
          if request.get_json() and request.get_json()['uin']:
               uin = request.get_json()['uin']
               status, data = lookup_access_status(uin)
               if status:
                    return {
                         "user": {
                              "uin": data['data']["uin"],
                              "username": "NA",
                              "given_name": "NA",
                              "family_name": "NA",
                              "status": data['data']["allowAccess"]
                         }
                    }
               else:
                    abort (500, data['message'])
          else:
               abort(400, 'UIN is a required field!')
     else:
          abort(403, 'User not Authorized! Please login first.')


@app.route('/quarantine', methods=['POST'])
def quarantine():
     if current_user.is_authenticated:

          if request.get_json() and request.get_json()['uin']:
               uin = request.get_json()['uin']
          else:
               abort(400, 'UIN is a required field!')

          # TODO connect to UIN quarantine API endpoint; placeholder here
          REDCap_status, REDCap_data = set_REDCap_status(new_uin=uin, new_status="quarantine")
          if not REDCap_status:
               abort(500, REDCap_data['message'])
          # elif not access_control_status:
          #      abort(500, access_control_message)
          else:
               return {
                    "user": {
                         "uin": uin,
                         "username": "NA",
                         "given_name": "NA",
                         "family_name": "NA",
                         "status": "false"
                    }
               }
     else:
          abort(403, 'User not Authorized! Please login first.')


@app.route('/isolate', methods=['POST'])
def isolate():
     if current_user.is_authenticated:

          if request.get_json() and request.get_json()['uin']:
               uin = request.get_json()['uin']
          else:
               abort(400, 'UIN is a required field!')

          # TODO connect to UIN isolate API endpoint; placeholder here
          REDCap_status, REDCap_data = set_REDCap_status(new_uin=uin, new_status="isolate")
          if not REDCap_status:
               abort(500, REDCap_data['data'])
          else:
               return {
                    "user": {
                         "uin": uin,
                         "username": "NA",
                         "given_name": "NA",
                         "family_name": "NA",
                         "status": "false"
                    }
               }

     else:
          abort(403, 'User not Authorized! Please login first.')


@app.route('/release', methods=['POST'])
def release():
     if current_user.is_authenticated:

          if request.get_json() and request.get_json()['uin']:
               uin = request.get_json()['uin']
          else:
               abort(400, 'UIN is a required field!')

          # TODO connect to UIN release API endpoint; placeholder here
          REDCap_status, REDCap_data = set_REDCap_status(new_uin=uin, new_status="release")
          if not REDCap_status:
               abort(500, REDCap_data['data'])
          else:
               return {
                    "user": {
                         "uin": uin,
                         "username": "NA",
                         "given_name": "NA",
                         "family_name": "NA",
                         "status": "true"
                    }
               }

     else:
          abort(403, 'User not Authorized! Please login first.')


# This is the health check for AWS ECS
@app.route('/health')
def health():
    return {'message': 'Healthy'}  # This will return as JSON by default with a 200 status code

