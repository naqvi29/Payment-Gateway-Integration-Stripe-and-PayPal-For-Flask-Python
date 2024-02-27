from flask import Flask, render_template, request, jsonify, redirect
import stripe
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv
import paypalrestsdk

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
csrf = CSRFProtect(app)

# Configure Stripe with your API keys
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Configure PayPal SDK
paypalrestsdk.configure({
  "mode": "sandbox",  # Change to "live" for production
  "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
  "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET')
})

# Define tax rate (17%)
TAX_RATE = 0.17

####################################### Stripe start #######################################

@app.route('/')
def index():
    return render_template('stripe/index.html',public_key=os.environ.get('STRIPE_PUBLIC_KEY'))

@app.route('/charge', methods=['POST'])  
def charge():
    amount = 500  # Amount in cents

    tax_amount = int(amount * TAX_RATE)
    total_amount = amount + tax_amount
    try:

        # Create a customer and charge
        customer = stripe.Customer.create(
            email=request.form['stripeEmail'],
            source=request.form['stripeToken']
        )
        charge = stripe.Charge.create(
            customer=customer.id,
            amount=total_amount,
            currency='usd',
            description='Flask Stripe Example'
        )
        return render_template('stripe/charge.html', amount=amount)
    except Exception as e:
        return str(e), 400
    
####################################### Stripe End #######################################
    
####################################### Paypal start #######################################


@app.route('/paypal')
def index_paypal():
    return render_template('paypal/index.html')

# Route for initiating payment
@app.route('/pay', methods=['POST'])
def pay():
    amount = request.form['amount']
    total_amount = float(amount) * (1 + TAX_RATE)

    payment = paypalrestsdk.Payment({
      "intent": "sale",
      "payer": {
        "payment_method": "paypal"
      },
      "transactions": [{
        "amount": {
          "total": "{:.2f}".format(total_amount),
          "currency": "USD"
        },
        "description": "Payment for your service from flask"
      }],
      "redirect_urls": {
        "return_url": f"{os.environ.get('DOMAIN')}/success",
        "cancel_url": f"{os.environ.get('DOMAIN')}/cancel"
      }
    })

    if payment.create():
        for link in payment.links:
            if link.method == 'REDIRECT':
                redirect_url = str(link.href)
                
                return redirect(redirect_url)
    else:
        return jsonify({'error': payment.error}), 400
    
# Route for success page
@app.route('/success')
def success():
    return render_template('paypal/success.html')

# Route for cancel page
@app.route('/cancel')
def cancel():
    return render_template('paypal/cancel.html')
####################################### Paypal End #######################################

if __name__ == '__main__':
    app.run(debug=True)
