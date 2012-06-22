__author__ = 'brunocatao'

from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.utils.translation import ugettext as _

class RegisterUserTestCase(TestCase):
    def _send_request(self, email='', password='', password_confirm=''):
        c = Client()

        form_data = {
            'email': email,
            'password': password,
            'password_confirm': password_confirm,
        }

        return c.post(reverse('portal.accounts.views.register'), form_data)

    def testSuccessfullyRegister(self):
        response = self._send_request('john@doe.com', '12345', '12345')
        self.assertEqual(response.status_code, 302) #302 => Redirect
        self.assertRedirects(response, reverse('portal.accounts.views.fill_user_info'))

    def testCheckRepeatedUsernames(self):
        response = self._send_request('john@doe.com', '12345', '12345')
        self.assertEqual(response.status_code, 302) #302 => Redirect
        self.assertRedirects(response, reverse('portal.accounts.views.fill_user_info'))
        response = self._send_request('john@doe.com', '12345', '12345')
        self.assertEqual(response.status_code, 200) #200 => OK
        self.assertFormError(response, 'form', 'email', _('A user with that username already exists.'))

    def testRegisterRequiredFields(self):
        response = self._send_request()
        self.assertEqual(response.status_code, 200) #200 => OK
        self.assertFormError(response, 'form', 'email', _("This field is required."))
        self.assertFormError(response, 'form', 'password', _("This field is required."))
        self.assertFormError(response, 'form', 'password_confirm', _("This field is required."))

    def testRegisterInvalidEmail(self):
        response = self._send_request('xpto', '12345', '12345')
        self.assertEqual(response.status_code, 200) #200 => OK
        self.assertFormError(response, 'form', 'email', _("Enter a valid e-mail address."))

    def testRegisterFieldsMinLength(self):
        response = self._send_request('xpto', '123', '123')
        self.assertEqual(response.status_code, 200) #200 => OK

        msg = _("Ensure this value has at least %(limit_value)d characters (it has %(show_value)d).") % {'limit_value': 5, 'show_value': 3}

        self.assertFormError(response, 'form', 'password', msg)
        self.assertFormError(response, 'form', 'password_confirm', msg)

    def testRegisterDifferentPasswords(self):
        response = self._send_request('john@doe.com', '12345', '54321')
        self.assertEqual(response.status_code, 200) #200 => OK
        self.assertFormError(response, 'form', 'password_confirm', _("The two password fields didn't match."))
