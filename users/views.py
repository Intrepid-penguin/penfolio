from django.shortcuts import render, redirect
from .forms import UserRegisterForm, CovertuserForm
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from requests_oauthlib import OAuth1Session
import logging # Optional: for logging errors/info

# Configure logging (optional)
logger = logging.getLogger(__name__)

# X API OAuth 1.0a endpoints
REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
AUTHORIZE_URL = 'https://api.twitter.com/oauth/authorize'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'


def connect_page(request: HttpRequest) -> HttpResponse:
    """Displays a simple page with a button/link to start the auth process."""
    return render(request, 'users/connect.html') # Create this template


def success_page(request: HttpRequest) -> HttpResponse:
    """Displays a simple success page after authorization."""
    # You might want to fetch user details here using the stored tokens
    screen_name = request.session.get('twitter_screen_name', 'User')
    return render(request, 'users/success.html', {'screen_name': screen_name}) # Create this template


# === Step 1: Authorize ===
def twitter_authorize(request: HttpRequest) -> HttpResponseRedirect:
    """
    Redirects the user to Twitter to grant permissions to your app.
    """
    try:
        # --- 1. Get Request Token ---
        # Build the callback URL dynamically (important!)
        callback_uri = request.build_absolute_uri(reverse('twitter_callback'))
        print(f"DEBUG: Callback URI: {callback_uri}") # Debug print

        # Create an OAuth1Session instance (Consumer Key/Secret, Callback URI)
        oauth = OAuth1Session(
            client_key=settings.X_API_KEY,
            client_secret=settings.X_API_SECRET,
            callback_uri=callback_uri
        )

        # Fetch the Request Token from Twitter
        fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
        print(f"DEBUG: Fetch Response: {fetch_response}") # Debug print


        # Extract the Request Token and Secret from the response
        resource_owner_key = fetch_response.get('oauth_token')
        resource_owner_secret = fetch_response.get('oauth_token_secret')
        # Check if Twitter confirmed the callback (useful for debugging)
        callback_confirmed = fetch_response.get('oauth_callback_confirmed') == 'true'

        if not resource_owner_key or not resource_owner_secret or not callback_confirmed:
            logger.error("OAuth callback not confirmed or tokens missing in response.")
            # Redirect to an error page or show a message
            return redirect('connect_page') # Or a dedicated error page

        # --- 2. Store Request Token Secret in Session ---
        # This secret is needed in the callback step to get the Access Token
        request.session['oauth_token_secret'] = resource_owner_secret
        request.session['oauth_token'] = resource_owner_key # Store token too if needed for verification
        print(f"DEBUG: Stored oauth_token_secret in session: {resource_owner_secret[:5]}...") # Debug print

        # --- 3. Redirect User to Twitter Authorization URL ---
        authorization_url = oauth.authorization_url(AUTHORIZE_URL)
        print(f"DEBUG: Redirecting user to: {authorization_url}") # Debug print

        return HttpResponseRedirect(authorization_url)

    except Exception as e:
        logger.exception("Error during Twitter authorization initiation:")
        # Handle error appropriately, maybe redirect to an error page
        return HttpResponse(f"An error occurred: {e}", status=500)


# === Step 2: Callback ===
def twitter_callback(request: HttpRequest) -> HttpResponseRedirect:
    """
    Handles the callback from Twitter after the user authorizes the app.
    Exchanges the Request Token and Verifier for an Access Token.
    """
    try:
        # --- 1. Get OAuth Verifier and Token from Request ---
        # Twitter redirects here with oauth_token and oauth_verifier in query params
        oauth_token = request.GET.get('oauth_token')
        oauth_verifier = request.GET.get('oauth_verifier')
        denied = request.GET.get('denied') # Check if the user denied access

        if denied:
            logger.warning(f"User denied access for request token: {denied}")
            # Redirect to a page indicating denial
            return redirect('connect_page') # Or an 'access_denied' page

        if not oauth_verifier or not oauth_token:
            logger.error("OAuth verifier or token missing in callback request.")
            # Redirect to an error page
            return redirect('connect_page')

        # --- 2. Retrieve Request Token Secret from Session ---
        # This MUST match the secret associated with the oauth_token received
        resource_owner_secret = request.session.get('oauth_token_secret')
        # Optional: verify oauth_token matches the one stored in session
        # stored_oauth_token = request.session.get('oauth_token')
        # if oauth_token != stored_oauth_token:
        #     logger.error("OAuth token mismatch between callback and session.")
        #     return redirect('connect_page') # Or an error page

        if not resource_owner_secret:
            logger.error("OAuth token secret not found in session. Session might have expired.")
            # Redirect to start the process again
            return redirect('twitter_authorize')


        # --- 3. Exchange for Access Token ---
        # Create an OAuth1Session instance WITH the request token/secret retrieved
        oauth = OAuth1Session(
            client_key=settings.X_API_KEY,
            client_secret=settings.X_API_SECRET,
            resource_owner_key=oauth_token,         # The oauth_token from callback
            resource_owner_secret=resource_owner_secret, # The SECRET retrieved from session
            verifier=oauth_verifier                  # The verifier from callback
        )

        # Fetch the Access Token from Twitter
        access_token_response = oauth.fetch_access_token(ACCESS_TOKEN_URL)
        print(f"DEBUG: Access Token Response: {access_token_response}") # Debug print


        # --- 4. Extract and Store Final User Tokens ---
        final_oauth_token = access_token_response.get('oauth_token')
        final_oauth_token_secret = access_token_response.get('oauth_token_secret')
        user_id = access_token_response.get('user_id')
        screen_name = access_token_response.get('screen_name')

        if not final_oauth_token or not final_oauth_token_secret:
             logger.error("Access token or secret missing in response.")
             return redirect('connect_page') # Or an error page

        # **IMPORTANT: Store these securely!**
        # Associate them with the logged-in Django user (request.user if using auth)
        # Example: Storing in session (OK for demo, use DB for production)
        request.session['twitter_access_token'] = final_oauth_token
        request.session['twitter_access_token_secret'] = final_oauth_token_secret
        request.session['twitter_user_id'] = user_id
        request.session['twitter_screen_name'] = screen_name
        print(f"DEBUG: Stored final access token for {screen_name} in session.")

        # Clean up temporary session data
        if 'oauth_token_secret' in request.session:
            del request.session['oauth_token_secret']
        if 'oauth_token' in request.session:
            del request.session['oauth_token']

        # --- 5. Redirect to Success Page ---
        return redirect('success_page')

    except Exception as e:
        logger.exception("Error during Twitter callback handling:")
        # Handle error appropriately
        return HttpResponse(f"An error occurred during callback: {e}", status=500)

# Create your views here.
@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        pin_form = CovertuserForm(request.POST)
        if form.is_valid() and pin_form.is_valid():
            user = form.save()
            pin = make_password(pin_form.cleaned_data['pin'])
            user.user_profile.pin = pin
            user.user_profile.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account creation for { username} was successful.') 
            return redirect('home')
    else:
        form = UserRegisterForm()
        pin_form = CovertuserForm()
    return render(request, 'users/auth.html', {'sign_up_form': form,
                                                    'pin_form': pin_form
                                                   })
@login_required   
def Logout(request):
    logout(request)
    return redirect('login')