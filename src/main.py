import sqlite3 as sql
import datetime
import sys

class Application:
    decision: bool = True
    debug: bool = False

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
                check_date varchar(10),
                rbill int default 0,
                gbill int default 0,
                lbill int default 0
            );
        """
        )

    def run(self, debug=False):
        self.debug = debug
        while self.decision:
            self.menu()

    def menu(self):
        print("-" * 45)
        print("Welcome to Hotel!\n")
        print("1. Check-in")
        print("2. Check-out")
        print("3. Calculate Bill")
        print("4. Add Bill")
        print("5. Guest info")
        if self.debug: print("9. Dump all (Debug only)")
        print("0. Exit")

        option = int(input("Enter option: "))
        print()
        match option:
            case 1: self.check_in()
            case 2: self.check_out()
            case 3: self.calculate_bill()
            case 4: self.add_bill()
            case 5: self.guest_info()
            case 9 if self.debug: self.dump_all()
            case 0: self.decision = False
            case _: print("Unknown option")
        print()

    def _check_for_guest(self, name) -> bool:
        self.cursor.execute(f"select name from guests where name='{name}';")
        if self.cursor.fetchone() is None:
            return False
        return True

    def check_in(self):
        name = input("Enter guest name: ")
        if len(name) > 120:
            print("Entered name is too large")
        room_type = input("Choose room type (Normal 'n' default, Delux 'd', Luxury 'l'): ").lower()
        if room_type not in ['n', 'd', 'l']:
            print("Incorrect room type selected")
            return

        # Get a valid room number (or reuse existing ones)
        room_no = self.room_count if len(self.rooms) == 0 else self.rooms.pop()
        self.room_count += 1

        check_date = datetime.date.today()

        self.cursor.execute(f"insert into guests (name, room_no, room_type, check_date) values ('{name}', {room_no}, '{room_type}', '{check_date}');")

        # Confirm if details are correct
        self._guest_info(name);
        if input("Confirm details? (Y/n): ").lower() == 'n':
            self.connection.rollback()
        else:
            self.connection.commit()

    def check_out(self):
        name = input("Enter guest name: ")

        if not self._check_for_guest(name):
            print(f"Guest '{name}' not found")
            return

        self._guest_info(name)
        self._calculate_bill(name)
        if input("Confirm checkout? (y/N): ").lower() == 'y':
            # Get room number
            self.cursor.execute(f"select room_no from guests where name='{name}';")
            data = self.cursor.fetchone()
            self.rooms.append(data[0])

            # Delete
            self.cursor.execute(f"delete from guests where name='{name}';")
            self.connection.commit()

    def calculate_bill(self):
        name = input("Enter guest name: ")
        self._calculate_bill(name)

    def _calculate_bill(self, name):
        self.cursor.execute(f"select room_type, check_date, rbill, gbill, lbill from guests where name='{name}';")
        data = self.cursor.fetchone()
        if data is None:
            print(f"Guest '{name}' not found")
            return

        (room_type, check_date, rbill, gbill, lbill) = data

        room_map = {'n': 1000, 'd': 2500, 'l': 4000}
        num_days = (datetime.date.today() - datetime.date.fromisoformat(check_date)).days + 1
        room_bill = room_map[room_type] * num_days

        print("Bill breakdown: ")
        print(f"  Room bill: {room_bill}")
        if rbill != 0: print(f"  Restaurant bill: {rbill}")
        if gbill != 0: print(f"  Game bill: {gbill}")
        if lbill != 0: print(f"  Laundary bill: {lbill}")
        print(" ", "-"*20)
        print(f"  Total bill: {room_bill+rbill+gbill+lbill}")

    def add_bill(self):
        name = input("Enter guest name: ")

        if not self._check_for_guest(name):
            print(f"Guest '{name}' not found")
            return

        print()
        print("Bill options\n")
        print("1. Restaurant bill")
        print("2. Game bill")
        print("3. Laundary bill")
        option = int(input("Enter bill type: "))

        bill_keys = {1: "rbill", 2: "gbill", 3: "lbill"}
        key = bill_keys.get(option)

        if key is None:
            print("Incorrect bill type")
            return

        amount = int(input("Enter bill amount: "))
        if amount == 0:
            return

        self.cursor.execute(f"select {key} from guests where name='{name}'")
        data = self.cursor.fetchone()
        if data is None:
            print(f"Guest '{name}' not found")
            return

        prev_amount = int(data[0])
        self.cursor.execute(f"update guests set {key}={prev_amount+amount}")

        self._calculate_bill(name)
        if input("Confirm changes to bill? (Y/n): ").lower() == 'n':
            self.connection.rollback()
        else:
            self.connection.commit()

    def guest_info(self):
        name = input("Enter guest name: ")
        self._guest_info(name);

    def _guest_info(self, name: str):
        self.cursor.execute(f"select name, room_no, room_type, check_date from guests where name='{name}';")
        data = self.cursor.fetchone()
        if data is None:
            print(f"Guest '{name}' not found")
            return

        (name, room_no, room_type, check_date) = data
        room_type_class = {"n": "Normal", "d": "Delux", "l": "Luxury"}
        room_type_str = room_type_class.get(room_type)

        print("Guest info:")
        print(f"  Name: {name}")
        print(f"  Room no: {room_no}")
        print(f"  Room type: {room_type_str}")
        print(f"  Check in date: {check_date}")

    def dump_all(self):
        self.cursor.execute("select * from guests")
        for idx, data in enumerate(self.cursor.fetchall()):
            print(f"{idx}: {data}")

def main():
    with sql.connect("database.db") as connection:
        cursor = connection.cursor()
        Application(connection, cursor).run(len(sys.argv) > 1 and sys.argv[1].lower() == "debug")

if __name__ == "__main__":
    main()


