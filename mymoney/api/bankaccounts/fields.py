class CurrentBankAccountDefault(object):
    def set_context(self, serializer_field):
        self.bankaccount = serializer_field.context['view'].bankaccount

    def __call__(self):
        return self.bankaccount

    def __repr__(self):
        return 'CurrentBankAccountDefault'
