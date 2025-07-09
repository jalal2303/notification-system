from django.conf import settings
from django.core.mail import EmailMessage
from twilio.rest import Client
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from jdformvalidator import is_valid_email

@api_view(['POST'])
def send_notification(request):
    payload = request.data

    subject = payload.get("subject")
    message_body = payload.get("message_body")
    greetings = payload.get("greetings_per_role", {})
    recipients = payload.get("recipients", [])

    if not message_body or not recipients:
        return Response({
            "message": "❌ message_body and recipients are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    acknowledgements = []

    for recipient in recipients:
        name = recipient.get("name")
        email = recipient.get("email")
        phone = recipient.get("phone")
        role = recipient.get("role")

        #Email Validation
        if email and not is_valid_email(email):
            acknowledgements.append(f"❌ Invalid email address: {email}")
            continue

        greet_template=greetings.get(role,f"Hi {name},")
        greet = greet_template.format(name=name)
        full_message = f"{greet}\n\n{message_body}"

        # Send Email
        if email:
            try:
                email_message = EmailMessage(
                    subject=subject or "Notification",
                    body=full_message,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[email]
                )
                email_message.send()
                acknowledgements.append(f"✅ Email sent to {email}")
            except Exception as e:
                acknowledgements.append(f"❌ Email to {email} failed: {str(e)}")

        # Send SMS and WhatsApp
        if phone:
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

                # SMS
                client.messages.create(
                    body=full_message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
                acknowledgements.append(f"✅ SMS sent to {phone}")

                # WhatsApp
                try:
                    client.messages.create(
                        body=full_message,
                        from_='whatsapp:+14155238886',
                        to=f'whatsapp:{phone}'
                    )
                    acknowledgements.append(f"✅ WhatsApp sent to {phone}")
                except Exception as wa_error:
                    acknowledgements.append(f"⚠️ WhatsApp failed: {str(wa_error)}")

            except Exception as sms_error:
                acknowledgements.append(f"❌ SMS/WhatsApp failed: {str(sms_error)}")

    return Response({
        "status": "success",
        "acknowledgements": acknowledgements
    }, status=status.HTTP_200_OK)