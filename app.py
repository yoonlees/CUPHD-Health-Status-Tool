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

from db import get_db
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
def load_user(user_id):
     return User.get(user_id)


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
          "redirect_uri":client.registration_response["redirect_uris"][0],
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

     # see if that user is in local database or not
     user = User.search(user_info["preferred_username"])

     # create that user in local db if that person is not there;
     if not user:
          user = User.create(netid=user_info["preferred_username"], fname=user_info["given_name"],
                             lname=user_info["family_name"], email=user_info["email"], uin=user_info["uiucedu_uin"],
                             phone="NA")

     # login that user
     login_user(user)

     return redirect(url_for("homepage"))


@app.route('/logout')
@login_required
def logout():
     logout_user()
     return redirect(url_for("homepage"))


@app.route('/', methods=['GET'])
def homepage():
     locations = ["Carle", "UIUC", "Peoria"]
     times = [
          "08:00 AM",
          "08:30 AM",
          "09:00 AM",
          "09:30 AM",
          "10:00 AM",
          "10:30 AM",
          "11:00 AM",
          "11:30 AM",
          "12:00 PM",
          "12:30 PM",
          "01:00 PM",
          "01:30 PM",
          "02:00 PM",
          "02:30 PM",
          "03:00 PM",
          "03:30 PM",
          "04:00 PM",
          "04:30 PM",
          "05:00 PM",
          "05:30 PM",
          "06:00 PM",
     ]

     if current_user.is_authenticated:
          user = "Hello! " + current_user.fname + " " + current_user.lname
     else:
          user = None

     return render_template('appointments.html', locations=locations, times=times, user=user)


@app.route('/list', methods=['GET'])
def list_available_appointments():
     query = '''SELECT a.id, a.date, a.time, l.name AS location
    FROM APPOINTMENTS a INNER JOIN LOCATIONS l
    ON a.location = l.id
    WHERE (DATE(a.date) >= DATE("now") and TIME(a.time) >= TIME("now","localtime") ) and a.id NOT IN (
    SELECT appointment
    FROM USER_APPOINTMENTS
    GROUP BY
        appointment
    HAVING COUNT(appointment) >= 120)'''

     location = request.args.get('location')
     if location:
          query += ' AND l.name = "' + location + '"'

     date = request.args.get('date')
     if date:
          query += ' AND a.date = "' + date + '"'

     time = request.args.get('time')
     if time:
          query += ' AND a.time = "' + time + '"'

     cur = get_db().cursor()
     cur.execute(query)

     results = cur.fetchall()
     cur.close()

     available_slots = [{
          "id": row['id'],
          "date": row['date'],
          "time": row['time'],
          "location": row['location']} for row in results
     ]

     return {"available_slots": available_slots}


@app.route('/my-appointment', methods=['GET'])
def list_my_appointment():
     if current_user.is_authenticated:
          conn = get_db()
          cur = conn.cursor()

          # get the appointment id;
          cur.execute("SELECT appointment FROM USER_APPOINTMENTS WHERE user = (?)", (current_user.id,))
          appt_id_list_claimed = cur.fetchall()

          claimed_slot = []
          if appt_id_list_claimed:
               for appt_id_claimed in appt_id_list_claimed:
                    cur.execute(
                         "SELECT a.id, a.date, a.time, l.name as location FROM APPOINTMENTS a INNER JOIN LOCATIONS l ON "
                         "a.location = l.id WHERE a.id = (?)", (appt_id_claimed['appointment'],))
                    result = cur.fetchone()
                    claimed_slot.append({
                         "id": result['id'],
                         "date": result['date'],
                         "time": result['time'],
                         "location": result['location']})

          cur.close()

          return {"claimed_slot": claimed_slot}

     else:
          abort(403, 'User not Authorized! Please login first.')


@app.route('/submit', methods=['POST'])
def submit_appointment():

     if current_user.is_authenticated:

          if request.get_json() and request.get_json()['appt_id']:
               appt_id = request.get_json()['appt_id']
          else:
               abort(400, 'Apppointment Id is a required field!')

          conn = get_db()
          cur = conn.cursor()

          # get the appt id
          cur.execute("SELECT * FROM APPOINTMENTS WHERE id = (?)", (appt_id,))
          appt = cur.fetchone()
          if not appt:
               abort(404, 'Cannot the selected appointment in the APPOINTMENTS database table.')

          # INSERT IF MAX 100 NOT REACHED PER APPOINTMENT ID
          cur.execute('''
             SELECT COUNT(appointment) as count_appt
             FROM USER_APPOINTMENTS
             WHERE appointment = (?)''', (appt['id'],))
          count_appt = cur.fetchone()
          if not count_appt:
               count_appt_num = 0
          else:
               count_appt_num = count_appt['count_appt']

          cur.execute('''
               SELECT COUNT(a.week) as count_week
               FROM USER_APPOINTMENTS ua 
               INNER JOIN APPOINTMENTS a 
               ON ua.appointment = a.id
               WHERE ua.user = (?) and a.week = (?)
               GROUP BY ua.user''', (current_user.id, appt['week'],))

          count_user_week = cur.fetchone()
          if not count_user_week:
               count_user_week_num = 0
          else:
               count_user_week_num = count_user_week['count_week']

          if count_appt_num >= 60:
               cur.close()
               abort(400, 'The appointment block has reached maximum capacity. Please choose another block in a ' \
                          'different week.')
          elif count_user_week_num >= 2:
               cur.close()
               abort(400,
                     'You have reached your maximum number of appointments for that week. Please choose another week.')
          # TODO: use should not select same appointment twice, check if that's enforced
          else:
               cur.execute("INSERT INTO USER_APPOINTMENTS (user, appointment) VALUES (?,?)",
                           (current_user.id, appt['id']))
               conn.commit()

               cur.execute(
                    "SELECT a.id, a.date, a.time, l.name as location FROM APPOINTMENTS a INNER JOIN LOCATIONS l ON "
                    "a.location = l.id WHERE a.id = (?)", (appt['id'],))
               results = cur.fetchall()

               claimed_slot = {
                    "id": results[0]['id'],
                    "date": results[0]['date'],
                    "time": results[0]['time'],
                    "location": results[0]['location']}

               cur.close()

               return {"claimed_slot": claimed_slot}
     else:
          abort(403, 'User not Authorized! Please login first.')


@app.route('/cancel', methods=['DELETE'])
def cancel_appointment():
     if current_user.is_authenticated:

          if request.get_json() and request.get_json()['appt_id']:
               appt_id = request.get_json()['appt_id']
          else:
               abort(400, 'Apppointment Id is a required field!')

          conn = get_db()
          cur = conn.cursor()

          cur.execute("SELECT appointment FROM USER_APPOINTMENTS WHERE user = (?)", (current_user.id,))
          appt_id_list_claimed = cur.fetchall()

          if appt_id_list_claimed:
               matched = False
               for appt_id_claimed in appt_id_list_claimed:
                    # confirm that "appt_id" is indeed in the user's appointment list and delete if it is
                    if str(appt_id_claimed['appointment']) == appt_id:
                         cur.execute("DELETE FROM USER_APPOINTMENTS WHERE appointment = (?)",
                                     (appt_id_claimed['appointment'],))
                         conn.commit()

                         cur.execute(
                              "SELECT a.id, a.date, a.time, l.name as location FROM APPOINTMENTS a INNER JOIN LOCATIONS l ON "
                              "a.location = l.id WHERE a.id = (?)", (appt_id_claimed['appointment'],))

                         result = cur.fetchone()
                         cur.close()

                         unclaimed_slot = {
                              "id": result['id'],
                              "date": result['date'],
                              "time": result['time'],
                              "location": result['location']}

                         return {"unclaimed_slot": unclaimed_slot}

               if not matched:
                    abort(404,'The appointment id: ' + appt_id + ' does not exist in the current user\'s appointment list')
          else:
               cur.close()
               abort(403, 'Action not allowed. This user currently has no appointment!')

     else:
          abort(403, 'User not Authorized! Please login first.')


@app.route('/list-all-appointments', methods=['GET'])
def list_all_appointments():
     if current_user.is_authenticated:
          conn = get_db()
          cur = conn.cursor()

          user = User.get(current_user.id)

          # if admin
          if user.netid in app.config['ADMIN_NETID_LIST']:
               cur.execute('''SELECT u.netid as NetID, u.fname ||' '|| u.lname as Name, u.email, l.name as Location, 
               a.date, a.time FROM USERS u INNER JOIN USER_APPOINTMENTS ua ON u.id=ua.user 
               INNER JOIN APPOINTMENTS a ON ua.appointment = a.id
               INNER JOIN LOCATIONS l ON a.location = l.id ''')
               results = cur.fetchall()
               cur.close()

               all_claimed_slot = [{
                    "netid": row["NetID"],
                    "name": row['Name'],
                    "email": row['email'],
                    "date": row['date'],
                    "time": row['time'],
                    "location": row['Location']} for row in results
               ]
          else:
               cur.close()
               abort(403, 'This is an administrator only feature!')

          return {"all_claimed_slot": all_claimed_slot}

     else:
          abort(403, 'User not Authorized! Please login first.')
