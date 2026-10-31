import sqlite3
from utils.security import hash_password

def reset_and_seed():
    conn = sqlite3.connect("football_system.db")
    cursor = conn.cursor()

    print("🗑️ กำลังล้างข้อมูลเก่าทั้งหมด...")
    cursor.execute("DELETE FROM transfer_offers")
    cursor.execute("DELETE FROM players")
    cursor.execute("DELETE FROM clubs")
    cursor.execute("DELETE FROM agents")
    cursor.execute("DELETE FROM users")

    default_pwd = hash_password("password123")

    print("👤 กำลังสร้างบัญชี Admin, Clubs และ Agents...")
    # สร้าง Admin
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', default_pwd, 'Admin'))
    
    # สร้าง Clubs
    clubs_data = [
        ('realmadrid', 'Real Madrid', 500000000),
        ('mancity', 'Manchester City', 600000000),
        ('arsenal', 'Arsenal', 300000000),
        ('barcelona', 'Barcelona', 200000000),
        ('liverpool', 'Liverpool', 250000000)
    ]
    club_ids = {}
    for uname, club_name, budget in clubs_data:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (uname, default_pwd, 'Club'))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO clubs (user_id, club_name, budget) VALUES (?, ?, ?)", (user_id, club_name, budget))
        club_ids[club_name] = cursor.lastrowid

    # สร้าง Agents 5 คน
    agents_data = [
        ('agent1', 'Jorge', 'Mendes', 'Gestifute'),
        ('agent2', 'Rafaela', 'Pimenta', 'One Sarl'),
        ('agent3', 'Jonathan', 'Barnett', 'ICM Stellar'),
        ('agent4', 'Pini', 'Zahavi', 'Gol International'),
        ('agent5', 'Volker', 'Struth', 'Sports360')
    ]
    agent_ids = []
    for uname, fname, lname, agency in agents_data:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (uname, default_pwd, 'Agent'))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO agents (user_id, first_name, last_name, agency_name) VALUES (?, ?, ?, ?)", (user_id, fname, lname, agency))
        agent_ids.append(cursor.lastrowid)

    print("⚽ กำลังเพิ่มรายชื่อนักเตะ 55 คน (11 คน / 5 สโมสร)...")
    players = [
        # Real Madrid (อ้างอิงข้อมูลของคุณ)
        ('Kylian', 'Mbappé', '1998-12-20', 'France', 'ST', 180000000, 'Real Madrid', agent_ids[0]),
        ('Vinícius', 'Júnior', '2000-07-12', 'Brazil', 'LW', 140000000, 'Real Madrid', agent_ids[1]),
        ('Jude', 'Bellingham', '2003-06-29', 'England', 'CM', 150000000, 'Real Madrid', agent_ids[2]),
        ('Trent', 'Alexander-Arnold', '1998-10-07', 'England', 'RB', 70000000, 'Real Madrid', agent_ids[3]),
        ('Federico', 'Valverde', '1998-07-22', 'Uruguay', 'CM', 120000000, 'Real Madrid', agent_ids[4]),
        ('Rodrygo', 'Goes', '2001-01-09', 'Brazil', 'RW', 100000000, 'Real Madrid', agent_ids[0]),
        ('Thibaut', 'Courtois', '1992-05-11', 'Belgium', 'GK', 30000000, 'Real Madrid', agent_ids[1]),
        ('Antonio', 'Rüdiger', '1993-03-03', 'Germany', 'CB', 25000000, 'Real Madrid', agent_ids[2]),
        ('Éder', 'Militão', '1998-01-18', 'Brazil', 'CB', 70000000, 'Real Madrid', agent_ids[3]),
        ('Aurélien', 'Tchouaméni', '2000-01-27', 'France', 'CDM', 90000000, 'Real Madrid', agent_ids[4]),
        ('Eduardo', 'Camavinga', '2002-11-10', 'France', 'CM', 90000000, 'Real Madrid', agent_ids[0]),
        
        # Manchester City
        ('Erling', 'Haaland', '2000-07-21', 'Norway', 'ST', 180000000, 'Manchester City', agent_ids[1]),
        ('Gianluigi', 'Donnarumma', '1999-02-25', 'Italy', 'GK', 45000000, 'Manchester City', agent_ids[2]),
        ('James', 'Trafford', '2002-10-10', 'England', 'GK', 25000000, 'Manchester City', agent_ids[3]),
        ('Enzo', 'Fernández', '2001-01-17', 'Argentina', 'CM', 80000000, 'Manchester City', agent_ids[4]),
        ('Phil', 'Foden', '2000-05-28', 'England', 'RW', 150000000, 'Manchester City', agent_ids[0]),
        ('Jeremy', 'Doku', '2002-05-27', 'Belgium', 'LW', 65000000, 'Manchester City', agent_ids[1]),
        ('Rodri', 'Hernández', '1996-06-22', 'Spain', 'CDM', 110000000, 'Manchester City', agent_ids[2]),
        ('Ruben', 'Dias', '1997-05-14', 'Portugal', 'CB', 80000000, 'Manchester City', agent_ids[3]),
        ('Josko', 'Gvardiol', '2002-01-23', 'Croatia', 'LB', 75000000, 'Manchester City', agent_ids[4]),
        ('Kevin', 'De Bruyne', '1991-06-28', 'Belgium', 'CAM', 50000000, 'Manchester City', agent_ids[0]),
        ('Bernardo', 'Silva', '1994-08-10', 'Portugal', 'CM', 80000000, 'Manchester City', agent_ids[1]),

        # Arsenal
        ('Bukayo', 'Saka', '2001-09-05', 'England', 'RW', 130000000, 'Arsenal', agent_ids[2]),
        ('Martin', 'Odegaard', '1998-12-17', 'Norway', 'CAM', 90000000, 'Arsenal', agent_ids[3]),
        ('Declan', 'Rice', '1999-01-14', 'England', 'CDM', 110000000, 'Arsenal', agent_ids[4]),
        ('William', 'Saliba', '2001-03-24', 'France', 'CB', 80000000, 'Arsenal', agent_ids[0]),
        ('Gabriel', 'Magalhaes', '1997-12-19', 'Brazil', 'CB', 65000000, 'Arsenal', agent_ids[1]),
        ('Ben', 'White', '1997-10-08', 'England', 'RB', 55000000, 'Arsenal', agent_ids[2]),
        ('Kai', 'Havertz', '1999-06-11', 'Germany', 'ST', 70000000, 'Arsenal', agent_ids[3]),
        ('Gabriel', 'Martinelli', '2001-06-18', 'Brazil', 'LW', 85000000, 'Arsenal', agent_ids[4]),
        ('David', 'Raya', '1995-09-15', 'Spain', 'GK', 35000000, 'Arsenal', agent_ids[0]),
        ('Riccardo', 'Calafiori', '2002-05-19', 'Italy', 'LB', 45000000, 'Arsenal', agent_ids[1]),
        ('Mikel', 'Merino', '1996-06-22', 'Spain', 'CM', 50000000, 'Arsenal', agent_ids[2]),

        # Barcelona
        ('Lamine', 'Yamal', '2007-07-13', 'Spain', 'RW', 120000000, 'Barcelona', agent_ids[3]),
        ('Pedri', 'González', '2002-11-25', 'Spain', 'CM', 90000000, 'Barcelona', agent_ids[4]),
        ('Gavi', 'Páez', '2004-08-05', 'Spain', 'CM', 90000000, 'Barcelona', agent_ids[0]),
        ('Ronald', 'Araujo', '1999-03-07', 'Uruguay', 'CB', 70000000, 'Barcelona', agent_ids[1]),
        ('Jules', 'Kounde', '1998-11-12', 'France', 'RB', 60000000, 'Barcelona', agent_ids[2]),
        ('Raphinha', 'Belloli', '1996-12-14', 'Brazil', 'LW', 60000000, 'Barcelona', agent_ids[3]),
        ('Marc-André', 'ter Stegen', '1992-04-30', 'Germany', 'GK', 30000000, 'Barcelona', agent_ids[4]),
        ('Pau', 'Cubarsi', '2007-01-22', 'Spain', 'CB', 40000000, 'Barcelona', agent_ids[0]),
        ('Alejandro', 'Balde', '2003-10-18', 'Spain', 'LB', 50000000, 'Barcelona', agent_ids[1]),
        ('Frenkie', 'de Jong', '1997-05-12', 'Netherlands', 'CM', 70000000, 'Barcelona', agent_ids[2]),
        ('Dani', 'Olmo', '1998-05-07', 'Spain', 'CAM', 60000000, 'Barcelona', agent_ids[3]),

        # Liverpool
        ('Mohamed', 'Salah', '1992-06-15', 'Egypt', 'RW', 65000000, 'Liverpool', agent_ids[4]),
        ('Virgil', 'van Dijk', '1991-07-08', 'Netherlands', 'CB', 30000000, 'Liverpool', agent_ids[0]),
        ('Alisson', 'Becker', '1992-10-02', 'Brazil', 'GK', 32000000, 'Liverpool', agent_ids[1]),
        ('Alexis', 'Mac Allister', '1998-12-24', 'Argentina', 'CM', 70000000, 'Liverpool', agent_ids[2]),
        ('Dominik', 'Szoboszlai', '2000-10-25', 'Hungary', 'CAM', 75000000, 'Liverpool', agent_ids[3]),
        ('Luis', 'Diaz', '1997-01-13', 'Colombia', 'LW', 75000000, 'Liverpool', agent_ids[4]),
        ('Cody', 'Gakpo', '1999-05-07', 'Netherlands', 'ST', 55000000, 'Liverpool', agent_ids[0]),
        ('Diogo', 'Jota', '1996-12-04', 'Portugal', 'ST', 50000000, 'Liverpool', agent_ids[1]),
        ('Andrew', 'Robertson', '1994-03-11', 'Scotland', 'LB', 35000000, 'Liverpool', agent_ids[2]),
        ('Ibrahima', 'Konate', '1999-05-25', 'France', 'CB', 45000000, 'Liverpool', agent_ids[3]),
        ('Harvey', 'Elliott', '2003-04-04', 'England', 'CM', 35000000, 'Liverpool', agent_ids[4])
    ]

    for p in players:
        cursor.execute('''
            INSERT INTO players (first_name, known_as, dob, nationality, main_position, estimated_value, current_club, agent_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Approved')
        ''', p)

    conn.commit()
    conn.close()
    print("✅ ล้างระบบและเพิ่มข้อมูล 5 สโมสร, 5 เอเยนต์, และนักเตะ 55 คน สำเร็จเรียบร้อย!")

if __name__ == "__main__":
    reset_and_seed()