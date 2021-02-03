-- Keep a log of any SQL queries you execute as you solve the mystery.

--start of solving the mystery, query of the description of the crime scene from the crime scene reports table
SELECT description
FROM crime_scene_reports
WHERE month = 7 AND day = 28
AND street = "Chamberlin Street";

--the description states the theft took place at 10:15am on 7/28/2020 at the chamberlin street courthouse with 3 witnesses who were present at the time
--querying into the interviews transcript column because the previous description stated all 3 witnesseses mentioned the courthouse in the transcript to try to find out the 3 witnesses' names
SELECT name, month, day, year, transcript
FROM interviews
WHERE month = 7 AND day = 28 AND year = 2020 AND transcript LIKE "%courthouse%";

--Ruth, Eugene, Raymond are the 3 witnesses
--(Ruth) Start with Ruth's account first which states that the courthouse security cams should have cars that EXITED the parking lot in +10 min of 10:15am so I am only looking at 10:15am - 10:25am
SELECT activity, license_plate, hour, minute
FROM courthouse_security_logs
WHERE month = 7 AND day = 28 AND year = 2020 AND hour = 10 AND minute BETWEEN 15 AND 25;

--(Ruth) jotting down all the license plates and searching for all the people with those license plates from the people table
--List of suspects = Patrick, Ernest, Amber, Danielle, Roger, Elizabeth, Russell, Evelyn
SELECT name, phone_number, passport_number, people.license_plate
FROM people
JOIN courthouse_security_logs ON courthouse_security_logs.license_plate = people.license_plate
WHERE month = 7 AND day = 28 AND year = 2020 AND hour = 10 AND minute BETWEEN 15 AND 25;

--(Eugene) Since I received the list of suspects now I'm moving onto Eugene's account
--Eugene stated the thief was someone that he RECOGNIZED and he saw the thief withdrawing some money by the ATM on Fifer Street
--Query into the atm_transctions table looking for the transactions and the amount on 7/28/2020 and join onto bank_accounts AND people tables to cross reference against list of suspects
--List of suspects narrowed down to Russell, Ernest, Danielle, and Elizabeth
SELECT people.name, atm_transactions.amount, atm_transactions.transaction_type
FROM atm_transactions
JOIN bank_accounts ON atm_transactions.account_number = bank_accounts.account_number
JOIN people ON bank_accounts.person_id = people.id
WHERE month = 7 AND day = 28 AND year = 2020 AND atm_location = "Fifer Street" AND transaction_type = "withdraw";

--(Raymond) Moving onto Raymond's account which states that they heard the thief say that they were planning to take the EARLIEST FLIGHT out of Fiftyville on 7/29/2020
--the thief then asked the person on the other end of the phone to purchase the flight ticket
--Query into the people table for passport number then join the airports, flights, and passengers tables to cross reference into the people table
SELECT people.name, airports.full_name, flights.hour, flights.minute
FROM people
JOIN passengers ON passengers.passport_number = people.passport_number
JOIN flights on flights.id = passengers.flight_id
JOIN airports on flights.origin_airport_id = airports.id
WHERE airports.city = "Fiftyville" AND flights.month = 7 AND flights.day = 29 AND flights.year = 2020;

--Wittled the thief suspects down to Ernest and Danielle
--Query into phone_calls table to see the callers for 7/28/20 with duration less than a minute
SELECT caller, receiver, duration
FROM phone_calls
WHERE month = 7 AND day = 28 AND year = 2020 AND duration < 60;

--Based on the calls caller and receiver ; Ernest is the thief
--Query into the people table with the receiver's phone number which is Berthold who is the accomplice
SELECT name, phone_number
FROM people
WHERE phone_number = "(375) 555-8161";

--Query into the flights information again to see where Ernest went
SELECT airports.city, flights.origin_airport_id, flights.destination_airport_id, flights.hour, flights.minute
FROM people
JOIN passengers ON passengers.passport_number = people.passport_number
JOIN flights on flights.id = passengers.flight_id
JOIN airports on flights.origin_airport_id = airports.id
WHERE month = 7 AND day = 29 AND year = 2020 AND airports.city = "Fiftyville";

--The destination id I am looking for is 4 so I query into airports to check which airport city is 4
SELECT * FROM airports
