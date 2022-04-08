import sqlite3 as sql
import datetime

class Application:
    decision: bool = True

    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor
        self.rooms = []
        self.room_count = 0

        self.cursor.execute("""
            create table if not exists guests (
                name varchar(120) primary key not null,
                room_no int,
                room_type char(1) check(room_type in ('n', 'd', 'l')),
                check_date varchar(10)
            );
        """
        )

    def run(self):
        while self.decision:
            self.menu()

    def menu(self):
        print("-" * 45)
        print("Welcome to Hotel!\n")
        print("1. Check-in")
        print("2. Check-out")
        print("3. Calculate Bill")
        print("4. Guest info")
        print("9. Dump all (Debug only)")
        print("0. Exit")

        option = int(input("Enter option: "))
        match option:
            case 1: self.check_in()
            case 2: self.check_out()
            case 3: self.calculate_bill()
            case 4: self.guest_info()
            case 9: self.dump_all()
            case 0: self.decision = False
            case _: print("Unknown option")
        print("\n")

    def check_in(self):
        name = input("Enter guest name: ")
        if len(name) > 120:
            print("Entered name is too large")
        room_type = input("Choose room type (Normal 'n' default, Delux 'd', Luxury 'l'): ").lower()

        # Get a valid room number
        room_no = self.room_count if len(self.rooms) == 0 else self.rooms.pop()
        self.room_count += 1

        check_date = datetime.date.today()

        self.cursor.execute(f"insert into guests (name, room_no, room_type, check_date) values ('{name}', {room_no}, '{room_type}', '{check_date}');")
        self.connection.commit()

    def check_out(self):
        name = input("Enter guest name: ")
        
        # Get room number
        self.cursor.execute(f"select room_no from guests where name='{name}';")
        data = self.cursor.fetchone()
        self.rooms.append(data[0])

        # Delete
        self.cursor.execute(f"delete from guests where name='{name}';")
        self.connection.commit()

    def calculate_bill(self):
        name = input("Enter guest name: ")

        self.cursor.execute(f"select room_type, check_date from guests where name='{name}';")
        data = self.cursor.fetchone()

        room_map = {'n': 1000, 'd': 2500, 'l': 4000}
        num_days = (datetime.date.today() - datetime.date.fromisoformat(data[1])).days + 1
        room_bill = room_map[data[0]] * num_days

        print("Bill breakdown: ")
        print(f"  Room bill: {room_bill}")

    def guest_info(self):
        name = input("Enter guest name: ")
        self.cursor.execute(f"select * from guests where name='{name}';")
        data = self.cursor.fetchone()
        print(data)

    def dump_all(self):
        self.cursor.execute("select * from guests")
        for idx, data in enumerate(self.cursor.fetchall()):
            print(f"{idx}: {data}")

def main():
    with sql.connect("database.db") as connection:
        cursor = connection.cursor()
        Application(connection, cursor).run()

if __name__ == "__main__":
    main()

