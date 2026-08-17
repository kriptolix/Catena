Catena/
├── requirements.txt
├── README.md
├── .env
├── data/
│   └── data_collector.db
│
└── src/
    ├── main.py
    │
    ├── core/
    │   ├── config.py
    │   ├── security.py
    │   └── database.py
    │
    ├── routes/
    │   ├── pages.py
    │   └── api/
    │       ├── Equipments.py
    │       ├── users.py
    │       └── auth.py
    │
    ├── models/
    │   └── user.py
    │
    ├── services/
    │   ├── auth.py
    │   └── Equipments.py
    │
    ├── templates/
    │   ├── index.html
    │   └── login.html
    │
    ├── static/
    │   ├── css/
    │   ├── js/
    │   └── img/
    │
    ├── locales/
    │   └── pt_BR/
    │       └── LC_MESSAGES/
    │
    └── utils/
        └── helpers.py