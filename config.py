#  Copyright (c) 2020. Board of Trustees of the University of Illinois.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Issuer URL. For production, this is https://shibboleth.illinois.edu.
import os

ISSUER_URL = "https://shibboleth.illinois.edu"
SCOPES = ["openid", "profile", "email", "offline_access"]  # Other OIDC scopes can be added as needed.

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REDIRECT_URIS = [os.environ["REDIRECT_URIS"]]
ADMIN_NETID_LIST = os.environ['ADMIN_NETID_LIST'].split(",")