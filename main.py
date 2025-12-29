# Chicago Traffic Camera Analysis - Write a console-based Python program 
#                                   that inputs commands from the user 
#                                   and outputs data from the Chicago traffic camera database.
# Project 1 – CS 341 Fall 2025
# Harsh Shah - hshah82

import sqlite3
import matplotlib.pyplot as plt

##################################################################  
#
# print_stats
#
# Given a connection to the database, executes various
# SQL queries to retrieve and output basic stats.
#

def print_stats(dbConn):
    dbCursor = dbConn.cursor()
    print("General Statistics:")
    dbCursor.execute("SELECT COUNT(*) FROM RedCameras;")
    print("  Number of Red Light Cameras:", f"{dbCursor.fetchone()[0]:,}")
    dbCursor.execute("SELECT COUNT(*) FROM SpeedCameras;")
    print("  Number of Speed Cameras:", f"{dbCursor.fetchone()[0]:,}")
    dbCursor.execute("SELECT COUNT(*) FROM RedViolations;")
    print("  Number of Red Light Camera Violation Entries:", f"{dbCursor.fetchone()[0]:,}")
    dbCursor.execute("SELECT COUNT(*) FROM SpeedViolations;")
    print("  Number of Speed Camera Violation Entries:", f"{dbCursor.fetchone()[0]:,}")

    dbCursor.execute("""
        SELECT MIN(Violation_Date), MAX(Violation_Date)
        FROM (
            SELECT Violation_Date FROM RedViolations
            UNION ALL
            SELECT Violation_Date FROM SpeedViolations
        );
    """)
    mn, mx = dbCursor.fetchone()
    print(f"  Range of Dates in the Database: {mn} - {mx}")
    
    # Total red violations
    dbCursor.execute("SELECT COALESCE(SUM(Num_Violations),0) FROM RedViolations;")
    print("  Total Number of Red Light Camera Violations:", f"{dbCursor.fetchone()[0]:,}")
    
    # Total speed violations
    dbCursor.execute("SELECT COALESCE(SUM(Num_Violations),0) FROM SpeedViolations;")
    print("  Total Number of Speed Camera Violations:", f"{dbCursor.fetchone()[0]:,}")
    print()


# cmd1
def cmd1(dbConn):
    intersectionName = input("\nEnter the name of the intersection to find (wildcards _ and % allowed): ")
    dbCursor = dbConn.cursor()
    
    dbCursor.execute("""
        SELECT Intersection_ID, Intersection
        FROM Intersections
        WHERE Intersection LIKE ?
        ORDER BY Intersection ASC;
    """, (intersectionName,))
    
    rows = dbCursor.fetchall()
    if not rows:
        print("No intersections matching that name were found.\n")
        return
    
    for i in rows:
        print(f"{i[0]} : {i[1]}")
    print()


# cmd2
def cmd2(dbConn):
    intersectionName = input("\nEnter the name of the intersection (no wildcards allowed): ")
    dbCursor = dbConn.cursor()

    dbCursor.execute("""
        SELECT Intersection_ID
        FROM Intersections
        WHERE Intersection = ?;
    """, (intersectionName,))
    row = dbCursor.fetchone()

    if not row:
        print("\nNo red light cameras found at that intersection.\n")
        print("No speed cameras found at that intersection.\n")
        return
    iid = row[0]

    dbCursor.execute("""
        SELECT Camera_ID, Address
        FROM RedCameras
        WHERE Intersection_ID = ?
        ORDER BY Camera_ID ASC;
    """, (iid,))
    red_rows = dbCursor.fetchall()

    if red_rows:
        print("\nRed Light Cameras:")
        for i in red_rows:
            print(f"   {i[0]} : {i[1]}")
    else:
        print("\nNo red light cameras found at that intersection.")

    dbCursor.execute("""
        SELECT Camera_ID, Address
        FROM SpeedCameras
        WHERE Intersection_ID = ?
        ORDER BY Camera_ID ASC;
    """, (iid,))
    speed_rows = dbCursor.fetchall()
    
    if speed_rows:
        print("\nSpeed Cameras:")
        for i in speed_rows:
            print(f"   {i[0]} : {i[1]}")
    else:
        print("\nNo speed cameras found at that intersection.")
    
    print()

# cmd3
def cmd3(dbConn):
    date = input("\nEnter the date that you would like to look at (format should be YYYY-MM-DD): ").strip()
    dbCursor = dbConn.cursor()
    dbCursor.execute("SELECT COALESCE(SUM(Num_Violations),0) FROM RedViolations WHERE Violation_Date = ?;", (date,))
    red_on_date = dbCursor.fetchone()[0]
    dbCursor.execute("SELECT COALESCE(SUM(Num_Violations),0) FROM SpeedViolations WHERE Violation_Date = ?;", (date,))
    speed_on_date = dbCursor.fetchone()[0]
    total = red_on_date + speed_on_date
    
    if total == 0:
        print("No violations on record for that date.\n")
        return
    
    red_pct = (red_on_date / total * 100) if total > 0 else 0
    speed_pct = (speed_on_date / total * 100) if total > 0 else 0
    
    print(f"Number of Red Light Violations: {red_on_date:,} ({red_pct:.3f}%)")
    print(f"Number of Speed Violations: {speed_on_date:,} ({speed_pct:.3f}%)")
    print(f"Total Number of Violations: {total:,}\n")


# cmd4
def cmd4(dbConn):
    cur = dbConn.cursor()
    cur.execute("SELECT COUNT(*) FROM RedCameras;")
    total_red = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM SpeedCameras;")
    total_speed = cur.fetchone()[0]

    cur.execute("""
        SELECT I.Intersection, I.Intersection_ID, COUNT(*) AS cnt
        FROM Intersections I
        JOIN RedCameras R ON R.Intersection_ID = I.Intersection_ID
        GROUP BY I.Intersection_ID
        ORDER BY cnt DESC, I.Intersection_ID DESC
    """)
    red_rows = cur.fetchall()

    cur.execute("""
        SELECT I.Intersection, I.Intersection_ID, COUNT(*) AS cnt
        FROM Intersections I
        JOIN SpeedCameras S ON S.Intersection_ID = I.Intersection_ID
        GROUP BY I.Intersection_ID
        ORDER BY cnt DESC, I.Intersection_ID DESC
    """)
    speed_rows = cur.fetchall()
    print()
    print("Number of Red Light Cameras at Each Intersection")

    for name, iid, cnt in red_rows:
        pct = (cnt / total_red * 100) if total_red else 0.0
        print(f"  {name} ({iid}) : {cnt} ({pct:.3f}%)")
    
    print()
    print("Number of Speed Cameras at Each Intersection")

    for name, iid, cnt in speed_rows:
        pct = (cnt / total_speed * 100) if total_speed else 0.0
        print(f"  {name} ({iid}) : {cnt} ({pct:.3f}%)")
    print()

# cmd5
def cmd5(dbConn):
    year = input("\nEnter the year that you would like to analyze: ").strip()
    dbCursor = dbConn.cursor()
    print()

    dbCursor.execute("""
        SELECT I.Intersection_ID, I.Intersection, COALESCE(SUM(RV.Num_Violations), 0) as total_violations
        FROM Intersections I
        LEFT JOIN RedCameras RC ON I.Intersection_ID = RC.Intersection_ID
        LEFT JOIN RedViolations RV ON RC.Camera_ID = RV.Camera_ID AND strftime('%Y', RV.Violation_Date) = ?
        GROUP BY I.Intersection_ID, I.Intersection
        HAVING total_violations > 0
        ORDER BY total_violations DESC, I.Intersection_ID DESC
    """, (year,))
    
    red_rows = dbCursor.fetchall()
    
    dbCursor.execute("""
        SELECT COALESCE(SUM(Num_Violations), 0)
        FROM RedViolations
        WHERE strftime('%Y', Violation_Date) = ?
    """, (year,))
    total_red = dbCursor.fetchone()[0]
    
    print("Number of Red Light Violations at Each Intersection for", year)
    if total_red == 0:
        print("No red light violations on record for that year.")
    else:
        for iid, intersection, violations in red_rows:
            if violations > 0:
                pct = (violations / total_red * 100)
                print(f"  {intersection} ({iid}) : {violations:,} ({pct:.3f}%)")
        print(f"Total Red Light Violations in {year} : {total_red:,}")
    
    print()
    
    dbCursor.execute("""
        SELECT I.Intersection_ID, I.Intersection, COALESCE(SUM(SV.Num_Violations), 0) as total_violations
        FROM Intersections I
        LEFT JOIN SpeedCameras SC ON I.Intersection_ID = SC.Intersection_ID
        LEFT JOIN SpeedViolations SV ON SC.Camera_ID = SV.Camera_ID AND strftime('%Y', SV.Violation_Date) = ?
        GROUP BY I.Intersection_ID, I.Intersection
        HAVING total_violations > 0
        ORDER BY total_violations DESC, I.Intersection_ID DESC
    """, (year,))
    speed_rows = dbCursor.fetchall()
    
   
    dbCursor.execute("""
        SELECT COALESCE(SUM(Num_Violations), 0)
        FROM SpeedViolations
        WHERE strftime('%Y', Violation_Date) = ?
    """, (year,))
    total_speed = dbCursor.fetchone()[0]
    
    print("Number of Speed Violations at Each Intersection for", year)
    if total_speed == 0:
        print("No speed violations on record for that year.")
    else:
        for iid, intersection, violations in speed_rows:
            if violations > 0:
                pct = (violations / total_speed * 100)
                print(f"  {intersection} ({iid}) : {violations:,} ({pct:.3f}%)")
        print(f"Total Speed Violations in {year} : {total_speed:,}")
    print()

# cmd6
def cmd6(dbConn):
    camera_id = input("\nEnter a camera ID: ").strip()
    dbCursor = dbConn.cursor()
    
    dbCursor.execute("SELECT 1 FROM RedCameras WHERE Camera_ID = ? UNION SELECT 1 FROM SpeedCameras WHERE Camera_ID = ?", 
                    (camera_id, camera_id))
    
    if not dbCursor.fetchone():
        print("No cameras matching that ID were found in the database.\n")
        return
    
    dbCursor.execute("""
        SELECT strftime('%Y', Violation_Date) as year, SUM(Num_Violations) as total
        FROM (
            SELECT Violation_Date, Num_Violations FROM RedViolations WHERE Camera_ID = ?
            UNION ALL
            SELECT Violation_Date, Num_Violations FROM SpeedViolations WHERE Camera_ID = ?
        )
        GROUP BY year
        ORDER BY year ASC
    """, (camera_id, camera_id))
    
    rows = dbCursor.fetchall()
    
    if not rows:
        print(f"No violations found for camera {camera_id}\n")
        return
    
    print(f"Yearly Violations for Camera {camera_id}")
    for year, total in rows:
        print(f"{year} : {total:,}")
    
    plot = input("\nPlot? (y/n) ").strip().lower()
    if plot == 'y':
        years = [row[0] for row in rows]
        violations = [row[1] for row in rows]
        
        plt.figure(figsize=(10, 6))
        plt.plot(years, violations, marker='o')
        plt.title(f"Yearly Violations for Camera {camera_id}")
        plt.xlabel("Year")
        plt.ylabel("Number of Violations")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    print()

# cmd7
def cmd7(dbConn):
    dbCursor = dbConn.cursor()
    camera_id = input("\nEnter a camera ID: ").strip()
    dbCursor.execute("SELECT 1 FROM RedCameras WHERE Camera_ID = ? UNION SELECT 1 FROM SpeedCameras WHERE Camera_ID = ?", 
                    (camera_id, camera_id))
    if not dbCursor.fetchone():
        print("No cameras matching that ID were found in the database.\n")
        return
    year = input("Enter a year: ").strip()
    dbCursor.execute("""
        SELECT strftime('%m', Violation_Date) as month, SUM(Num_Violations) as total
        FROM (
            SELECT Violation_Date, Num_Violations FROM RedViolations 
            WHERE Camera_ID = ? AND strftime('%Y', Violation_Date) = ?
            UNION ALL
            SELECT Violation_Date, Num_Violations FROM SpeedViolations 
            WHERE Camera_ID = ? AND strftime('%Y', Violation_Date) = ?
        )
        GROUP BY month
        ORDER BY month ASC
    """, (camera_id, year, camera_id, year))
    
    rows = dbCursor.fetchall()
    
    print(f"Monthly Violations for Camera {camera_id} in {year}")
    for month, total in rows:
        month_str = f"{month}/{year}"
        print(f"{month_str} : {total:,}")
    
    plot = input("\nPlot? (y/n) ").strip().lower()
    if plot == 'y':
        months = [int(row[0]) for row in rows]
        violations = [row[1] for row in rows]
        month_labels = [f"{m:02d}/{year}" for m in months]
        plt.figure(figsize=(12, 6))
        plt.plot(month_labels, violations, marker='o')
        plt.title(f"Monthly Violations for Camera {camera_id} ({year})")
        plt.xlabel("Month")
        plt.ylabel("Number of Violations")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    print()


# cmd8
def cmd8(dbConn):
    year = input("\nEnter a year: ").strip()
    dbCursor = dbConn.cursor()
    dbCursor.execute("""
        SELECT Violation_Date, SUM(Num_Violations) as total
        FROM RedViolations
        WHERE strftime('%Y', Violation_Date) = ?
        GROUP BY Violation_Date
        ORDER BY Violation_Date ASC
    """, (year,))
    red_rows = dbCursor.fetchall()
    
    dbCursor.execute("""
        SELECT Violation_Date, SUM(Num_Violations) as total
        FROM SpeedViolations
        WHERE strftime('%Y', Violation_Date) = ?
        GROUP BY Violation_Date
        ORDER BY Violation_Date ASC
    """, (year,))
    speed_rows = dbCursor.fetchall()
    
    print("Red Light Violations:")
    if not red_rows:
        pass
    else:
        first_five = red_rows[:5]
        last_five = red_rows[-5:] if len(red_rows) > 5 else []
        
        for date, total in first_five + last_five:
            print(f"{date} {total}")
    
    print("Speed Violations:")
    if not speed_rows:
        pass
    else:
        first_five = speed_rows[:5]
        last_five = speed_rows[-5:] if len(speed_rows) > 5 else []
        for date, total in first_five + last_five:
            print(f"{date} {total}")
    
    plot = input("\nPlot? (y/n) ").strip().lower()
    if plot == 'y':
        import datetime
        try:
            all_dates = []
            current_date = datetime.date(int(year), 1, 1)
            end_date = datetime.date(int(year), 12, 31)
            
            while current_date <= end_date:
                all_dates.append(current_date)
                current_date += datetime.timedelta(days=1)
            red_dict = dict(red_rows)
            speed_dict = dict(speed_rows)
            red_vals = []
            speed_vals = []
            
            for date in all_dates:
                date_str = date.strftime("%Y-%m-%d")
                red_vals.append(red_dict.get(date_str, 0))
                speed_vals.append(speed_dict.get(date_str, 0))
            
            plt.figure(figsize=(12, 6))
            plt.plot(range(len(red_vals)), red_vals, color='red', label='Red Light', alpha=0.7)
            plt.plot(range(len(speed_vals)), speed_vals, color='orange', label='Speed', alpha=0.7)
            plt.title(f"Violations Each Day of {year}")
            plt.xlabel("Day")
            plt.ylabel("Number of Violations")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            
        except ValueError:
            pass
    
    print()

# cmd9
def cmd9(dbConn):
    streetName = input("\nEnter a street name: ").strip()
    dbCursor = dbConn.cursor()
    dbCursor.execute("""
        SELECT Camera_ID, Address, Latitude, Longitude
        FROM RedCameras
        WHERE Address LIKE ?
        ORDER BY Camera_ID ASC
    """, (f'%{streetName}%',))
    red_cameras = dbCursor.fetchall()
    dbCursor.execute("""
        SELECT Camera_ID, Address, Latitude, Longitude
        FROM SpeedCameras
        WHERE Address LIKE ?
        ORDER BY Camera_ID ASC
    """, (f'%{streetName}%',))
    speed_cameras = dbCursor.fetchall()
    
    if not red_cameras and not speed_cameras:
        print("There are no cameras located on that street.\n")
        return
    
    print(f"\nList of Cameras Located on Street: {streetName}")
    print("  Red Light Cameras:")
    if red_cameras:
        for cam_id, address, lat, lon in red_cameras:
            lat_str = f"{lat:.8f}".rstrip('0').rstrip('.') if '.' in str(lat) else str(lat)
            lon_str = f"{lon:.8f}".rstrip('0').rstrip('.') if '.' in str(lon) else str(lon)
            print(f"     {cam_id} : {address} ({lat_str}, {lon_str})")
    else:
        pass
    print("  Speed Cameras:")
    if speed_cameras:
        for cam_id, address, lat, lon in speed_cameras:
            lat_str = f"{lat:.8f}".rstrip('0').rstrip('.') if '.' in str(lat) else str(lat)
            lon_str = f"{lon:.8f}".rstrip('0').rstrip('.') if '.' in str(lon) else str(lon)
            print(f"     {cam_id} : {address} ({lat_str}, {lon_str})")
    else:
        pass
    
    plot = input("\nPlot? (y/n) ").strip().lower()
    if plot == 'y':
        try:
            image = plt.imread("chicago.png")
            xydims = [-87.9277, -87.5569, 41.7012, 42.0868]
            
            plt.figure(figsize=(10, 8))
            plt.imshow(image, extent=xydims)
            plt.title(f"Cameras on Street: {streetName}")
            
            if red_cameras:
                red_x = [cam[3] for cam in red_cameras]
                red_y = [cam[2] for cam in red_cameras]
                plt.scatter(red_x, red_y, color='red', label='Red Light Cameras', s=50, alpha=0.7)
            
            if speed_cameras:
                speed_x = [cam[3] for cam in speed_cameras]
                speed_y = [cam[2] for cam in speed_cameras]
                plt.scatter(speed_x, speed_y, color='orange', label='Speed Cameras', s=50, alpha=0.7)
            
           
            for cam in red_cameras + speed_cameras:
                plt.annotate(str(cam[0]), (cam[3], cam[2]), xytext=(5, 5), 
                           textcoords='offset points', fontsize=8, alpha=0.8)
            plt.xlim([-87.9277, -87.5569])
            plt.ylim([41.7012, 42.0868])
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            plt.legend()
            plt.tight_layout()
            plt.show()
            
        except FileNotFoundError:
            print("Note: chicago.png map file not found. Plotting without map background.")
            plt.figure(figsize=(10, 8))
            plt.title(f"Cameras on Street: {streetName}")
            
            if red_cameras:
                red_x = [cam[3] for cam in red_cameras]
                red_y = [cam[2] for cam in red_cameras]
                plt.scatter(red_x, red_y, color='red', label='Red Light Cameras', s=50, alpha=0.7)
            
            if speed_cameras:
                speed_x = [cam[3] for cam in speed_cameras]
                speed_y = [cam[2] for cam in speed_cameras]
                plt.scatter(speed_x, speed_y, color='orange', label='Speed Cameras', s=50, alpha=0.7)
            
            for cam in red_cameras + speed_cameras:
                plt.annotate(str(cam[0]), (cam[3], cam[2]), xytext=(5, 5), 
                           textcoords='offset points', fontsize=8, alpha=0.8)
            
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
    print()

##################################################################  
#
# main
#
def main():
    dbConn = sqlite3.connect('chicago-traffic-cameras.db')

    print("Project 1: Chicago Traffic Camera Analysis")
    print("CS 341, Fall 2025")
    print()
    print("This application allows you to analyze various")
    print("aspects of the Chicago traffic camera database.")
    print()
    print_stats(dbConn)

    while True:
        print("Select a menu option: ")
        print("  1. Find an intersection by name")
        print("  2. Find all cameras at an intersection")
        print("  3. Percentage of violations for a specific date")
        print("  4. Number of cameras at each intersection")
        print("  5. Number of violations at each intersection, given a year")
        print("  6. Number of violations by year, given a camera ID")
        print("  7. Number of violations by month, given a camera ID and year")
        print("  8. Compare the number of red light and speed violations, given a year")
        print("  9. Find cameras located on a street")
        print("or x to exit the program.")
        
        choice = input("Your choice --> ").strip()
        
        if choice == "x":
            print("Exiting program.")
            break
        elif choice == "1":
            cmd1(dbConn)
        elif choice == "2":
            cmd2(dbConn)
        elif choice == "3":
            cmd3(dbConn)
        elif choice == "4":
            cmd4(dbConn)
        elif choice == "5":
            cmd5(dbConn)
        elif choice == "6":
            cmd6(dbConn)
        elif choice == "7":
            cmd7(dbConn)
        elif choice == "8":
            cmd8(dbConn)
        elif choice == "9":
            cmd9(dbConn)
        else:
            print("Error, unknown command, try again...\n")

    dbConn.close()

##################################################################  
#
# entry point
#3
if __name__ == "__main__":
    main()

