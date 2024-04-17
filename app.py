import math
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import logging
import datetime
from datetime import datetime
import mysql.connector



app = Flask(__name__)
  
  
app.secret_key = 'janasaleh'
  
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'satellitesys'

app.config['MYSQL_HOST'] = 'mysql-lynstguide.alwaysdata.net'
app.config['MYSQL_USER'] = '355991'
app.config['MYSQL_PASSWORD'] = 'Janasaleh2003'
app.config['MYSQL_DB'] = 'lynstguide_satsys'
  
mysql = MySQL(app)


@app.route('/')

##QUERY 1
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'username' in request.form and 'gender' in request.form and 'birthdate' in request.form and 'location' in request.form and 'region' in request.form:
        email = request.form['email']
        username = request.form['username']
        gender = request.form['gender']
        birthdate = request.form['birthdate']
        location = request.form['location']
        region = request.form['region']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not re.match(r'\d{4}-\d{2}-\d{2}', birthdate):
            message = 'Invalid birthdate format. Please use YYYY-MM-DD.'
        elif not email or not username or not gender or not birthdate or not location or not region:
            message = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO user (email, username, gender, birthdate, location, region) VALUES (%s, %s, %s, %s, %s, %s)', (email, username, gender, birthdate, location, region))
            mysql.connection.commit()
            message = 'You have successfully registered!'
            session['email'] = email 
            cursor.close()  
            return redirect(url_for('dashboard'))  
    
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


##QUERY 2
@app.route('/favorite-channels', methods=['GET', 'POST'])
def favorite_channels():
    if 'email' not in session:
        return redirect(url_for('register')) 

    email = session['email']
    message = ''
    channel_details = None
    favorite_channels = None
    
    if request.method == 'POST' and 'channel_name' in request.form and 'channel_frequency' in request.form:
        channel_name = request.form['channel_name']
        channel_frequency = request.form['channel_frequency']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT Channelname, Frequency, Lang FROM channel WHERE ChannelName = %s AND Frequency = %s', (channel_name, channel_frequency))
        channel = cursor.fetchone()

        print("Channel tuple:", channel)  # Debugging statement


    # if request.method == 'POST' and 'channel_name' in request.form:
    #     channel_name = request.form['channel_name']

    #     cursor = mysql.connection.cursor()
    #     cursor.execute('SELECT Channelname, Frequency, Lang FROM channel WHERE ChannelName = %s', (channel_name,))
    #     channel = cursor.fetchone()

    #     print("Channel tuple:", channel)  # Debugging statement

        if channel:
            # Convert tuple to dictionary
            channel_dict = {
                'Channel Name': channel[0],
                'Frequency': channel[1],
                'Language': channel[2]
            }

            cursor.execute('INSERT INTO userfavchanel (Email, ChannelName, Favchfreq, Favchlang) VALUES (%s, %s, %s, %s)', (email, channel_name, channel_dict['Frequency'], channel_dict['Language']))
            mysql.connection.commit()
            message = 'Channel added to favorites!'
            channel_details = channel_dict
        else:
            message = 'Channel not found!'

        cursor.close()
        
        
            # Fetch the user's favorite channels from the database
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT ChannelName, Favchfreq, Favchlang FROM userfavchanel WHERE Email = %s', (email,))
    favorite_channels = cursor.fetchall()  # Use the result set
    cursor.close()
        

    return render_template('userfavch.html', message=message, channel_details=channel_details, favorite_channels=favorite_channels)

#QUERY 3
@app.route('/viewable-channels', methods=['GET', 'POST'])
def viewable_channels():
    if request.method == 'POST' and 'longitude' in request.form:
        longitude = request.form['longitude']

        cursor = mysql.connection.cursor()
        
        if longitude.endswith('E'):
            longitude_val = float(longitude[:-3])
        elif longitude.endswith('W'):
            longitude_val = float(longitude[:-3])
        else:
            return "Invalid longitude format"

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT ChannelName, Frequency, Lang, position FROM channel WHERE ABS(CAST(SUBSTRING_INDEX(position, \'°\', 1) AS DECIMAL(10, 1)) - %s) <= 10', (longitude_val,))
        channels = cursor.fetchall()
        cursor.close()

        return render_template('viewablech.html', channels=channels, longitude=longitude)

    return render_template('viewablech.html')

#QUERY 4

@app.route('/covered-favorite-channels', methods=['GET', 'POST'])
def covered_favorite_channels():
    if request.method == 'POST' and 'email' in request.form and 'region' in request.form:
        email = request.form['email']
        region = request.form['region']
        
        print(f"Received request for email: {email}, region: {region}")

        cursor = mysql.connection.cursor()

        
        cursor.execute('SELECT ChannelName FROM userfavchanel WHERE Email = %s', (email,))
        favorite_channels = cursor.fetchall()

        covered_channels = []

        for channel in favorite_channels:
            channel_name = channel[0]

            cursor.execute('SELECT Frequency FROM channel WHERE ChannelName = %s', (channel_name,))
            chinfo = cursor.fetchone()

            cursor.execute('SELECT SatName FROM satelite WHERE Region = %s', (region,))
            sats = cursor.fetchall()

            print(f"Channel: {channel_name}, Region: {region}, Satellites: {sats}")

            for sat in sats:
                satname = sat[0]

                cursor.execute('SELECT * FROM satellitechannel WHERE SatName = %s AND ChannelName = %s', (satname, channel_name))
                sat_channel = cursor.fetchone()

                if sat_channel:
                    cursor.execute('SELECT Encryption FROM channel WHERE ChannelName = %s', (channel_name,))
                    encryp = cursor.fetchone()[0]
                    covered_channels.append({
                        'ChannelName': channel_name,
                        'Frequency': chinfo[0],
                        'SatName': satname,
                        'Encryption': encryp if encryp else 'Free'
                    })

        cursor.close()

        print(covered_channels)
        return render_template('coveredfavch.html', covered_channels=covered_channels, email=email, region=region)

    return render_template('coveredfavch.html')


#QUERY 5

@app.route('/top-networks', methods=['GET', 'POST'])
def top_networks():
    cursor = mysql.connection.cursor()

    #top 5 TVnets by the number of channels
    cursor.execute('''
        SELECT nc.NetName AS TVNetwork, COUNT(nc.ChannelName) AS NumChannels
        FROM networkchannel AS nc
        GROUP BY nc.NetName
        ORDER BY NumChannels DESC
        LIMIT 5
    ''')
    top_networks = cursor.fetchall()
   
    print(top_networks)

    # avg number of satellites each channel is available on
    cursor.execute('''
        SELECT nc.NetName AS TVNetwork, AVG(s.NumSatellites) AS AvgSatellites
        FROM networkchannel AS nc
        JOIN (
            SELECT sc.ChannelName, COUNT(DISTINCT sc.SatName) AS NumSatellites
            FROM satellitechannel AS sc
            GROUP BY sc.ChannelName
        ) AS s ON nc.ChannelName = s.ChannelName
        GROUP BY nc.NetName
    ''')
    avg_satellites = cursor.fetchall()
    cursor.close()
    print(avg_satellites)
    
    return render_template('topnets.html', top_networks=top_networks, avg_satellites=avg_satellites)



#QUERY 6
@app.route('/top-rockets', methods=['GET', 'POST'])
def top_rockets():
    cursor = mysql.connection.cursor()

    #5 rockets by the number of satellites
    cursor.execute('''
        SELECT LaunchingRoc AS Rocket, COUNT(*) AS NumSatellites
        FROM satelite
        WHERE LaunchingRoc <> ''
        GROUP BY LaunchingRoc
        ORDER BY NumSatellites DESC
        LIMIT 5
    ''')
    toprockets = cursor.fetchall()

    cursor.close()
    
    print("Top Rockets:", toprockets)

    return render_template('toprockets.html', toprockets=toprockets)


# Query 7
@app.route('/top-growing-satellites', methods=['GET', 'POST'])
def top_growing_satellites():
    cursor = mysql.connection.cursor()
    
     # Get the current date
    currentDate = datetime.now()

    # number of channels hosted by each satellite
    cursor.execute('''
        SELECT sc.SatName, COUNT(sc.channelname) AS NumChannels, s.LauncingDate
        FROM satellitechannel AS sc
        JOIN satelite AS s ON sc.SatName = s.SatName
        GROUP BY sc.SatName, s.LauncingDate
    ''')
    satelliteInfo = cursor.fetchall()

    cursor.close()
    
    print(satelliteInfo)

    satellites = []
    for SatName, NumChannels, LauncingDate in satelliteInfo:
        # launchyear = datetime.strptime(LauncingDate,'%Y-%m-%d').year
        # yearsFromlaunch = datetime.now().year - launchyear
        # growthRate = math.ceil(NumChannels / yearsFromlaunch if yearsFromlaunch != 0 else NumChannels)
        # satellites.append((SatName, growthRate))
        
        if not LauncingDate:
            continue
        #days since the satellite's launch
        launchdate = datetime.strptime(LauncingDate, '%Y-%m-%d')
        daySfromLaunch = (currentDate - launchdate).days

        
        growthRate =  round(NumChannels / daySfromLaunch, 1)  if daySfromLaunch != 0 else NumChannels
        satellites.append((SatName, growthRate))

    topSats = sorted(satellites, key=lambda x: x[1], reverse=True)[:5]
    ##print(topSats)

    return render_template('growingStas.html', topSats=topSats)

#query 8

@app.route('/top-channels-by-language', methods=['GET', 'POST'])
def top_channels_by_language():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT sc.chLang, sc.ChannelName, COUNT(DISTINCT sc.SatName) AS NumSatellites
        FROM satellitechannel AS sc
        GROUP BY sc.chLang, sc.ChannelName
        ORDER BY sc.chLang, NumSatellites DESC
    ''')
    ChbyLang = cursor.fetchall()

    cursor.close()
    top_channels = {}
    for chLang, ChannelName, NumSatellites in ChbyLang:
        if chLang not in top_channels:
            top_channels[chLang] = []
        if len(top_channels[chLang]) < 5:
            top_channels[chLang].append((ChannelName, NumSatellites))

    return render_template('topforLang.html', top_channels=top_channels)

#Query 9
@app.route('/filter-channels', methods=['GET', 'POST'])
def filter_channels():
    region = request.form.get('region', '')
    satellite = request.form.get('satellite', '')
    language = request.form.get('language', '')

    cursor = mysql.connection.cursor()
    
    if not (region or satellite or language):
        return render_template('filters.html', channels=[])

    query = """
        SELECT DISTINCT ch.ChannelName
        FROM channel AS ch
        JOIN satellitechannel AS sc ON ch.ChannelName = sc.ChannelName
        JOIN satelite AS s ON sc.SatName = s.SatName
        WHERE 1=1
    """
    if region:
        query += f" AND s.Region = '{region}'"
    if satellite:
        query += f" AND sc.SatName = '{satellite}'"
    if language:
        query += f" AND ch.Lang = '{language}'"

    cursor.execute(query)
    channels = [row[0] for row in cursor.fetchall()]

    cursor.close()

    return render_template('filters.html', channels=channels)

    
if __name__ == "__main__":
    app.run()