import random

class Faker:
    def __init__(self):
        raise NotImplementedError("This class cannot be instantiated.")
    
    @staticmethod
    def generate_fake_avg(avg=100, std_dev=5):
        """
        Generate a single fake sample.
        :param avg: Average to base value on
        :param std_dev: Standard deviation
        :return: A single heart rate sample
        """
        return round(random.gauss(avg, std_dev))
    
    @staticmethod
    def generate_fake_hr():
        return Faker.generate_fake_avg(72, 5)
    
    @staticmethod
    def generate_fake_bpm():
        return Faker.generate_fake_avg(120, 10)