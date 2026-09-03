import random
import time
import requests

RANDOM_SEED: str = "job-et-bonheur"

def generate_name(length: int = 32) -> str:
    """ Generate a name """
    ...

def seed(employee: int, partners: int, transactions: int, duration: int) -> None:
    print("Starting seeding with:")
    print(f"-> {employee} employees")
    print(f"-> {partners} partners")
    print(f"-> {transactions} transactions on a period of {duration} days")

    time.sleep(2)
    print(f"Seeding done!")

if __name__ == '__main__':
    random.seed(RANDOM_SEED)
    seed(employee=50, partners=12, transactions=200, duration=90)
