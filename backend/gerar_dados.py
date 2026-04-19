import random
import psycopg2
from faker import Faker
import bcrypt

random.seed(42)

fake = Faker("pt_PT")
Faker.seed(42)

conn = psycopg2.connect(
    host="localhost",
    database="urgencias_g2",
    user="postgres",
    password="A_TUA_PASSWORD"
)

cur = conn.cursor()

for i in range(1000):
    nome = fake.name()
    username = f"user{i}"
    email = f"user{i}@teste.pt"

    password = bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode()

    num_func = random.randint(1000, 9999)
    role = random.randint(1, 4)

    ativo = random.choice([True, True, True, False])

    cur.execute("""
        INSERT INTO utilizador
        (username, nome_completo, email, password_hash, num_func, id_role, ativo)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        username,
        nome,
        email,
        password,
        num_func,
        role,
        ativo
    ))

conn.commit()
cur.close()
conn.close()

print("1000 utilizadores inseridos.")