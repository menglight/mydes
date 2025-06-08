from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, Response
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import db
from app.main import bp
from app.main.forms import LoginForm, RegistrationForm
from app.main.models import User
import stripe
from datetime import datetime
import openai # Import OpenAI

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Home')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user! Please log in to continue.')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/dashboard')
@login_required
def dashboard():
    stripe_pk = current_app.config.get('STRIPE_PUBLISHABLE_KEY')
    price_id = current_app.config.get('STRIPE_PRICE_ID')
    # Define available models for the dropdown
    available_models = [
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        # Add other models here if you plan to support them
        # {"id": "gpt-4", "name": "GPT-4 (If available)"},
    ]
    return render_template('dashboard.html', title='Dashboard', stripe_pk=stripe_pk, price_id=price_id, available_models=available_models)

@bp.route('/api/interact', methods=['POST'])
@login_required
def interact_placeholder():
    if not current_user.subscription_active:
        return jsonify({'error': 'Active subscription required. Please subscribe via the dashboard.'}), 403

    data = request.get_json()
    if not data or 'user_input' not in data or 'selected_model' not in data:
        return jsonify({'error': 'Missing data: user_input or selected_model'}), 400

    user_input = data.get('user_input')
    selected_model_id = data.get('selected_model') # e.g., "gpt-3.5-turbo"

    openai.api_key = current_app.config['OPENAI_API_KEY']

    if not openai.api_key:
        current_app.logger.error("OpenAI API key is not set.")
        return jsonify({'error': 'OpenAI API key not configured on server.'}), 500

    try:
        # Example: Using ChatCompletion for models like gpt-3.5-turbo or gpt-4
        if selected_model_id in ["gpt-3.5-turbo", "gpt-4"]: # Add other chat models if needed
            completion = openai.ChatCompletion.create(
                model=selected_model_id,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            )
            response_text = completion.choices[0].message.content.strip()
        else:
            # Potentially handle other types of models or throw an error for unsupported model
            current_app.logger.warning(f"Unsupported model selected: {selected_model_id}")
            return jsonify({'error': f"Model '{selected_model_id}' is not supported."}), 400

        return jsonify({'response': response_text})

    except openai.error.OpenAIError as e:
        current_app.logger.error(f"OpenAI API Error: {e}")
        # More specific error handling can be added here (e.g., for rate limits, auth errors)
        error_message = str(e)
        if "quota" in error_message.lower():
            error_message = "You have exceeded your OpenAI API quota. Please check your OpenAI account."
        elif "authentication" in error_message.lower():
            error_message = "OpenAI API authentication failed. Please check the server configuration."
        else:
            error_message = "An error occurred while communicating with the OpenAI API."
        return jsonify({'error': error_message}), 500
    except Exception as e:
        current_app.logger.error(f"General Error in /api/interact: {e}")
        return jsonify({'error': 'An unexpected error occurred on the server.'}), 500

# Stripe routes (remain unchanged from previous step)
@bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    price_id = current_app.config['STRIPE_PRICE_ID']
    domain_url = current_app.config['DOMAIN_URL']
    try:
        customer_id = current_user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(email=current_user.email, name=current_user.username)
            customer_id = customer.id
            current_user.stripe_customer_id = customer_id
            db.session.commit()
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=domain_url + url_for('main.payment_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + url_for('main.payment_cancel'),
            client_reference_id=str(current_user.id)
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        current_app.logger.error(f"Stripe Checkout Error: {e}")
        flash(f'Error creating Stripe checkout session: {str(e)}')
        return redirect(url_for('main.dashboard'))

@bp.route('/payment/success')
@login_required
def payment_success():
    flash('Your payment was successful! Your subscription status will be updated shortly.')
    return redirect(url_for('main.dashboard'))

@bp.route('/payment/cancel')
@login_required
def payment_cancel():
    flash('Your payment was cancelled.')
    return redirect(url_for('main.dashboard'))

@bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        current_app.logger.error(f"Webhook ValueError: {e}")
        return Response(status=400)
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error(f"Webhook SignatureVerificationError: {e}")
        return Response(status=400)
    except Exception as e:
        current_app.logger.error(f"Webhook general error: {e}")
        return Response(status=500)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get('subscription')
        if not client_reference_id:
            current_app.logger.error("Webhook Error: checkout.session.completed event without client_reference_id")
            return Response(status=400)
        user = User.query.get(int(client_reference_id))
        if user:
            user.stripe_customer_id = stripe_customer_id
            user.stripe_subscription_id = stripe_subscription_id
            db.session.commit()
            current_app.logger.info(f"Webhook: Checkout session completed for user {user.id}. Customer ID: {stripe_customer_id}, Sub ID: {stripe_subscription_id}")
        else:
            current_app.logger.error(f"Webhook Error: User not found with ID {client_reference_id}")
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        stripe_customer_id = invoice.get('customer')
        stripe_subscription_id = invoice.get('subscription')
        period_end_timestamp = invoice.get('lines', {}).get('data', [{}])[0].get('period', {}).get('end')
        user = User.query.filter_by(stripe_customer_id=stripe_customer_id).first()
        if user:
            user.subscription_active = True
            user.stripe_subscription_id = stripe_subscription_id
            if period_end_timestamp:
                user.stripe_current_period_end = datetime.utcfromtimestamp(period_end_timestamp)
            db.session.commit()
            current_app.logger.info(f"Webhook: Invoice paid for user {user.id}. Subscription active until {user.stripe_current_period_end}.")
        else:
            current_app.logger.error(f"Webhook Error: User not found with Stripe Customer ID {stripe_customer_id} for invoice.paid event.")
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        stripe_customer_id = invoice.get('customer')
        user = User.query.filter_by(stripe_customer_id=stripe_customer_id).first()
        if user:
            current_app.logger.warning(f"Webhook: Invoice payment failed for user {user.id}.")
        else:
            current_app.logger.error(f"Webhook Error: User not found with Stripe Customer ID {stripe_customer_id} for invoice.payment_failed event.")
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        stripe_customer_id = subscription.get('customer')
        user = User.query.filter_by(stripe_customer_id=stripe_customer_id).first()
        if user and user.stripe_subscription_id == subscription.id:
            user.subscription_active = False
            user.stripe_current_period_end = None
            db.session.commit()
            current_app.logger.info(f"Webhook: Subscription deleted for user {user.id}.")
        elif user: # Mismatch in subscription ID, log but don't alter
             current_app.logger.warning(f"Webhook: Subscription deleted event for user {user.id} but subscription ID {subscription.id} does not match stored ID {user.stripe_subscription_id}.")
        else:
            current_app.logger.error(f"Webhook Error: User not found with Stripe Customer ID {stripe_customer_id} for customer.subscription.deleted event.")
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        stripe_customer_id = subscription.get('customer')
        user = User.query.filter_by(stripe_customer_id=stripe_customer_id).first()
        if user:
            user.stripe_subscription_id = subscription.id
            user.subscription_active = subscription.status == 'active' or subscription.status == 'trialing'
            if subscription.current_period_end:
                 user.stripe_current_period_end = datetime.utcfromtimestamp(subscription.current_period_end)
            else:
                user.stripe_current_period_end = None
            db.session.commit()
            current_app.logger.info(f"Webhook: Subscription updated for user {user.id}. Active: {user.subscription_active}, Period End: {user.stripe_current_period_end}")
        else:
            current_app.logger.error(f"Webhook Error: User not found with Stripe Customer ID {stripe_customer_id} for customer.subscription.updated event.")
    else:
        current_app.logger.info(f"Webhook: Unhandled event type {event['type']}")
    return Response(status=200)
