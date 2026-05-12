Process Optimization Platform - Setup GuideThis guide provides instructions on how to set up and run the application locally on a Windows machine using PyCharm.Final Folder StructureCreate a folder on your computer (e.g., C:\Users\YourUser\PycharmProjects\Process-Optimization-App). Place all the files from this response inside it. The final structure will look like this:/Process-Optimization-App/
├── files/
│   ├── json/   <-- (Empty folder, will be auto-created)
│   ├── logs/   <-- (Empty folder, will be auto-created)
│   └── data/   
│       └── fingerprint4.csv  <-- (IMPORTANT: Your historical data goes here)
│
├── api.py                  (Backend: API routes)
├── authentication.py       (Backend: User auth)
├── config.py               (Backend: System config)
├── database.py             (Backend: InfluxDB logic)
├── expert_guidance_tool.py (Backend: Guidance routes)
├── fingerprint_engine.py   (Backend: Core algorithm)
├── Interactive_plot_duna.py(Backend: Dash simulator)
├── main.py                 (Backend: Main server entry point)
├── previousInfo.py         (Backend: API for legacy settings)
├── process_model.py        (Backend: "Cartridge" loader/logic)
│
├── index.html              (Frontend: The UI)
├── model_config.json       (Config: The "Cartridge" data)
└── requirements.txt        (Config: Python dependencies)
Step 1: Prepare DataHistorical Data (CSV): Place your fingerprint4.csv file inside the files/data/ folder. The app uses this for pattern matching.Real-Time Data (InfluxDB): Ensure your InfluxDB is running and receiving live data.Download InfluxDB 1.8.10 for Windows.Run influxd.exe to start the server.The app connects to localhost:8086, database dunadrava.Step 2: Set Up PyCharmOpen Project: In PyCharm, go to File > Open and select your Process-Optimization-App folder.Create Virtual Environment:Go to File > Settings > Project: Process-Optimization-App > Python Interpreter.Click the gear icon > Add... > Virtualenv Environment > OK.Install Dependencies:Open the Terminal tab at the bottom of PyCharm.Run:pip install -r requirements.txt
Step 3: Run The ApplicationRun the Backend:Right-click main.py in the project explorer and select "Run 'main'".The console should say:Successfully loaded process modelSuccessfully loaded historical data from files/data/fingerprint4.csvRun the Frontend:Right-click index.html in the project explorer and select "Open in > Browser" (Chrome/Edge).The dashboard will appear.Note: If you don't have live data flowing into InfluxDB yet, the "Current Setpoints" might show as empty or error, but the app will still load.