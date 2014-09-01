from abc import ABCMeta, abstractmethod


class BaseTest:
    __metaclass__ = ABCMeta

    # the test's type in the JSON object (e.g., 'review')
    json_type = None

    def __init__(self, description, deduction):
        self.description = description
        self.deduction = deduction


    @staticmethod
    @abstractmethod
    def from_dict(dict_obj):
        raise NotImplementedError()


    @abstractmethod
    def to_dict(self):
        raise NotImplementedError()


    @abstractmethod
    def run(self):
        return (self.deduction, '(generic reason)')
        # or, if the test did not fail, return None


    def __str__(self):
        return "'{}' test of {}".format(self.json_type, self.target)