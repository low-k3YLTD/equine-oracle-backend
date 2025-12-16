// Mock data to simulate responses from The Racing API
// This data is based on the expected structure for Australian/NZ racing.

export const mockRacecards = {
    "date": "2025-11-16",
    "meetings": [
        {
            "id": "mtg_1",
            "name": "Randwick",
            "country": "AU",
            "races": [
                {
                    "id": "rc_101",
                    "raceNo": 1,
                    "time": "12:00",
                    "distance": "1200m",
                    "status": "open",
                    "horses": [
                        { "id": "hrs_1", "name": "Winx", "number": 1, "odds": 2.5, "form": "1-1-1" },
                        { "id": "hrs_2", "name": "Black Caviar", "number": 2, "odds": 4.0, "form": "2-1-1" },
                        { "id": "hrs_3", "name": "Makybe Diva", "number": 3, "odds": 8.0, "form": "3-2-1" },
                    ]
                },
                {
                    "id": "rc_102",
                    "raceNo": 2,
                    "time": "12:30",
                    "distance": "1600m",
                    "status": "open",
                    "horses": [
                        { "id": "hrs_4", "name": "Phar Lap", "number": 1, "odds": 1.5, "form": "1-1-1" },
                        { "id": "hrs_5", "name": "Kingston Town", "number": 2, "odds": 5.0, "form": "2-2-1" },
                    ]
                },
                {
                    "id": "rc_103",
                    "raceNo": 3,
                    "time": "13:00",
                    "distance": "1400m",
                    "status": "completed",
                    "horses": [
                        { "id": "hrs_6", "name": "Tulloch", "number": 1, "odds": 3.0, "form": "1-1-1" },
                        { "id": "hrs_7", "name": "Might and Power", "number": 2, "odds": 6.0, "form": "2-1-1" },
                    ],
                    "result": {
                        "winner": { "name": "Tulloch", "number": 1 },
                        "placings": ["Tulloch", "Might and Power"]
                    }
                }
            ]
        }
    ]
};

export const mockOdds = {
    "raceId": "rc_101",
    "market": [
        { "horseId": "hrs_1", "winOdds": 2.5, "placeOdds": 1.4, "volume": 10000 },
        { "horseId": "hrs_2", "winOdds": 4.0, "placeOdds": 1.8, "volume": 8000 },
        { "horseId": "hrs_3", "winOdds": 8.0, "placeOdds": 2.5, "volume": 5000 },
    ]
};

export const mockHorseHistory = {
    "horseId": "hrs_1",
    "history": [
        { "date": "2025-11-09", "result": "1st", "days_since": 7 },
        { "date": "2025-10-26", "result": "1st", "days_since": 14 },
        { "date": "2025-10-12", "result": "2nd", "days_since": 14 },
    ],
    "stats": {
        "days_since_last_race": 7,
        "prev_race_won": 1,
        "win_streak": 2
    }
};
