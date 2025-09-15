from django.conf import settings as global_settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from django_admin_otp import settings, utils
from django_admin_otp.forms import OTPForm
from django_admin_otp.models import OTPVerification, TrustedDevice


def _mfa_verify_success_response(request, user, trust_device):
    request.session[settings.MFA_VERIFIED_SESSION_KEY] = True
    response = redirect(utils.admin_url())

    if trust_device:
        device = TrustedDevice.create_for_user(user=user, device_info=request.META["HTTP_USER_AGENT"])
        response.set_cookie(
            key=settings.DEVICE_TOKEN_COOKIE_NAME,
            value=device.token_cipher,
            max_age=settings.TRUSTED_DEVICE_DAYS * 24 * 60 * 60,  # seconds
            httponly=True,
            secure=not global_settings.DEBUG,  # secured in production
            samesite="Lax",
        )
    return response


def _mfa_verify_get_response(request):
    if utils.is_request_mfa_verified(request) or utils.is_trusted_device_request(request):
        return redirect(utils.admin_url())

    if not OTPVerification.objects.filter(user=request.user, confirmed=True).exists():
        if settings.FORCE_OTP:
            return redirect(settings.MFA_SETUP_INTERNAL_NAME)
        return redirect(utils.admin_url())

    return render(request, "mfa_verify.html")


@login_required
def mfa_verify(request):
    if request.method != "POST":
        return _mfa_verify_get_response(request)

    user = request.user
    form = OTPForm(request.POST)
    if not form.is_valid():
        return render(request, "mfa_verify.html", {"error": "Wrong form data"})

    verification = OTPVerification.objects.only("secret_key_cipher").get(user=user, confirmed=True)
    if verification.verify(form.cleaned_data["code"]):
        return _mfa_verify_success_response(
            request=request,
            user=user,
            trust_device=form.cleaned_data["trust_device"],
        )

    return render(request, "mfa_verify.html", {"error": "Wrong code"})


def _mfa_setup_get_response(request, verification):
    if verification.confirmed:
        # if user already has the confirmed verification - skip it
        return redirect(utils.admin_url())

    return render(
        request,
        "mfa_setup.html",
        {"qr_code_url": utils.generate_qr_image(verification.generate_qr_code_uri())},
    )


@login_required
def mfa_setup(request):
    verification, _ = OTPVerification.objects.get_or_create(user=request.user)
    if request.method != "POST":
        return _mfa_setup_get_response(request, verification)

    form = OTPForm(request.POST)
    if not form.is_valid():
        return render(request, "mfa_setup.html", {"error": "Wrong form data"})

    if verification.verify(form.cleaned_data["code"]):
        verification.confirmed = True
        verification.save()
        return redirect(utils.admin_url())

    return render(
        request,
        "mfa_setup.html",
        {
            "qr_code_url": utils.generate_qr_image(verification.generate_qr_code_uri()),
            "error": "Wrong code",
        },
    )
