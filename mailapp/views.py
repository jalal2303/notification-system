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

    subject = payload.get("subject", "Notification")
    message_body = payload.get("message_body")
    greetings = payload.get("greetings_per_role", {})
    recipients = payload.get("recipients", [])

    # Dynamic config overrides from payload
    email_user = payload.get("email_user", settings.EMAIL_HOST_USER)
    email_password = payload.get("email_password", settings.EMAIL_HOST_PASSWORD)
    twilio_sid = payload.get("twilio_sid", settings.TWILIO_ACCOUNT_SID)
    twilio_auth_token = payload.get("twilio_auth_token", settings.TWILIO_AUTH_TOKEN)
    twilio_phone = payload.get("twilio_phone", settings.TWILIO_PHONE_NUMBER)
    twilio_whatsapp = payload.get("twilio_whatsapp", settings.TWILIO_WHATSAPP_NUMBER)

    if not message_body or not recipients:
        return Response({
            "message": "❌ 'message_body' and 'recipients' are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    acknowledgements = []

    for recipient in recipients:
        name = recipient.get("name", "User")
        email = recipient.get("email")
        phone = recipient.get("phone")
        role = recipient.get("role", "user")

        # Validate email
        if email and not is_valid_email(email):
            acknowledgements.append(f"❌ Invalid email address: {email}")
            continue

        # Construct greeting
        greet_template = greetings.get(role, f"Hi {name},")
        greet = greet_template.format(name=name)
        full_message = f"{greet}\n\n{message_body}"

        # Email sending
        if email:
            try:
                email_message = EmailMessage(
                    subject=subject,
                    body=full_message,
                    from_email=email_user,
                    to=[email]
                )
                email_message.send()
                acknowledgements.append(f"✅ Email sent to {email}")
            except Exception as e:
                acknowledgements.append(f"❌ Email to {email} failed: {str(e)}")

        # SMS & WhatsApp sending
        if phone:
            try:
                client = Client(twilio_sid, twilio_auth_token)

                # SMS
                client.messages.create(
                    body=full_message,
                    from_=twilio_phone,
                    to=phone
                )
                acknowledgements.append(f"✅ SMS sent to {phone}")

                # WhatsApp
                try:
                    client.messages.create(
                        body=full_message,
                        from_=twilio_whatsapp,
                        to=f'whatsapp:{phone}'
                    )
                    acknowledgements.append(f"✅ WhatsApp sent to {phone}")
                except Exception as wa_error:
                    acknowledgements.append(f"⚠️ WhatsApp failed for {phone}: {str(wa_error)}")

            except Exception as sms_error:
                acknowledgements.append(f"❌ SMS/WhatsApp failed for {phone}: {str(sms_error)}")

    return Response({
        "status": "success",
        "acknowledgements": acknowledgements
    }, status=status.HTTP_200_OK)
