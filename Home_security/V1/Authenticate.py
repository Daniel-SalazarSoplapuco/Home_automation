import pyotp


class Authenticate(object):
    
    def __init__(self, one_time_password):
        self.auth_challenge = pyotp.TOTP(one_time_password)

    def challenge(self, response):
        verify_number = self.auth_challenge.now()
        return verify_number == response